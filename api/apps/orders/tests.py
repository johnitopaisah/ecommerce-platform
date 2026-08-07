"""
Order status transitions — authorization and the tracking-email side effect.
"""

import pytest
from django.core import mail

from apps.store.models import Category, Product
from .models import Order, OrderStatus

ADMIN_ORDERS_URL = '/api/v1/admin/orders/'


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
