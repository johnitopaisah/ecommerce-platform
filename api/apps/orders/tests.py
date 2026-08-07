"""
Order status transitions — authorization and the tracking-email side effect.
"""

import pytest
from django.core import mail

from apps.coupons.models import Coupon
from apps.store.models import Category, Product
from .models import Order, OrderStatus

ADMIN_ORDERS_URL = '/api/v1/admin/orders/'
ORDERS_URL = '/api/v1/orders/'
BASKET_ITEMS_URL = '/api/v1/basket/items/'
BASKET_COUPON_URL = '/api/v1/basket/coupon/'


@pytest.fixture
def category(db):
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product(db, category, staff_user):
    return Product.objects.create(
        category=category, created_by=staff_user, title='Widget', slug='widget',
        price='19.99', stock_quantity=10,
    )


@pytest.fixture
def order(db, regular_user):
    return Order.objects.create(
        user=regular_user, order_key='key123', total_paid='19.99',
        status=OrderStatus.CONFIRMED, billing_status=True,
        full_name='Test Buyer', email='buyer@example.com',
        address_line_1='1 Test St', city='London', postcode='AA1 1AA', country='UK',
    )


@pytest.mark.django_db
class TestAdminOrderStatusUpdate:
    def test_regular_user_cannot_update_status(self, api_client, regular_user, order):
        api_client.force_authenticate(regular_user)
        response = api_client.put(
            f'{ADMIN_ORDERS_URL}{order.order_number}/status/', {'status': 'shipped'}, format='json'
        )
        assert response.status_code == 403

    def test_staff_can_update_status(self, api_client, staff_user, order):
        api_client.force_authenticate(staff_user)
        response = api_client.put(
            f'{ADMIN_ORDERS_URL}{order.order_number}/status/', {'status': 'processing'}, format='json'
        )
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.PROCESSING

    def test_status_change_to_shipped_sends_tracking_email(self, api_client, staff_user, order):
        api_client.force_authenticate(staff_user)

        response = api_client.put(
            f'{ADMIN_ORDERS_URL}{order.order_number}/status/', {'status': 'shipped'}, format='json'
        )

        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [order.email]
        assert order.order_number in mail.outbox[0].subject

    def test_setting_same_status_sends_no_email(self, api_client, staff_user, order):
        api_client.force_authenticate(staff_user)
        response = api_client.put(
            f'{ADMIN_ORDERS_URL}{order.order_number}/status/', {'status': order.status}, format='json'
        )
        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_transition_to_confirmed_sends_no_email(self, api_client, staff_user, order):
        # CONFIRMED isn't a tracking milestone — the order-confirmation email
        # already covers it at creation time.
        order.status = OrderStatus.PENDING
        order.save(update_fields=['status'])
        api_client.force_authenticate(staff_user)

        response = api_client.put(
            f'{ADMIN_ORDERS_URL}{order.order_number}/status/', {'status': 'confirmed'}, format='json'
        )

        assert response.status_code == 200
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestOrderCreationWithCoupon:
    def _checkout_payload(self, order_key='order-key-1'):
        return {
            'order_key': order_key,
            'full_name': 'Test Buyer', 'email': 'buyer@example.com',
            'address_line_1': '1 Test St', 'city': 'London',
            'postcode': 'AA1 1AA', 'country': 'UK',
        }

    def test_order_total_reflects_applied_coupon(self, api_client, regular_user, product):
        Coupon.objects.create(code='SAVE10', discount_type=Coupon.DiscountType.PERCENTAGE, discount_value='10.00')
        api_client.force_authenticate(regular_user)
        api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')
        api_client.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        response = api_client.post(ORDERS_URL, self._checkout_payload(), format='json')

        assert response.status_code == 201
        assert response.data['coupon_code'] == 'SAVE10'
        assert response.data['discount_amount'] == '2.00'  # 10% of 19.99, rounded
        assert response.data['total_paid'] == '17.99'

    def test_coupon_usage_count_increments_on_checkout(self, api_client, regular_user, product):
        coupon = Coupon.objects.create(
            code='SAVE10', discount_type=Coupon.DiscountType.PERCENTAGE, discount_value='10.00'
        )
        api_client.force_authenticate(regular_user)
        api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')
        api_client.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        api_client.post(ORDERS_URL, self._checkout_payload(), format='json')

        coupon.refresh_from_db()
        assert coupon.times_used == 1

    def test_coupon_cleared_from_basket_after_checkout(self, api_client, regular_user, product):
        Coupon.objects.create(code='SAVE10', discount_type=Coupon.DiscountType.PERCENTAGE, discount_value='10.00')
        api_client.force_authenticate(regular_user)
        api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')
        api_client.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')
        api_client.post(ORDERS_URL, self._checkout_payload(), format='json')

        # New basket (product re-added) should start with no leftover coupon.
        api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')
        response = api_client.get('/api/v1/basket/')

        assert response.data['coupon_code'] is None

    def test_order_without_coupon_has_zero_discount(self, api_client, regular_user, product):
        api_client.force_authenticate(regular_user)
        api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')

        response = api_client.post(ORDERS_URL, self._checkout_payload(), format='json')

        assert response.status_code == 201
        assert response.data['coupon_code'] is None
        assert response.data['discount_amount'] == '0.00'
        assert response.data['total_paid'] == '19.99'


@pytest.mark.django_db
class TestCustomerOrderCancel:
    def test_cancelling_own_order_sends_email(self, api_client, regular_user, order):
        api_client.force_authenticate(regular_user)

        response = api_client.post(f'/api/v1/orders/{order.order_number}/cancel/')

        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert 'cancelled' in mail.outbox[0].subject.lower() or 'cancel' in mail.outbox[0].body.lower()

    def test_cannot_cancel_shipped_order(self, api_client, regular_user, order):
        order.status = OrderStatus.SHIPPED
        order.save(update_fields=['status'])
        api_client.force_authenticate(regular_user)

        response = api_client.post(f'/api/v1/orders/{order.order_number}/cancel/')

        assert response.status_code == 400
        assert len(mail.outbox) == 0
