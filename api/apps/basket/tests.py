"""
Basket coupon apply/remove — exercises the real Redis-backed basket via the
actual add-item endpoint, since basket has no DB model to fixture directly.
"""

import pytest

from apps.coupons.models import Coupon
from apps.store.models import Category, Product

BASKET_URL = '/api/v1/basket/'
BASKET_ITEMS_URL = '/api/v1/basket/items/'
BASKET_COUPON_URL = '/api/v1/basket/coupon/'


@pytest.fixture
def category(db):
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product(db, category, staff_user):
    return Product.objects.create(
        category=category, created_by=staff_user, title='Widget', slug='widget',
        price='50.00', stock_quantity=10,
    )


@pytest.fixture
def coupon(db):
    return Coupon.objects.create(code='SAVE10', discount_type=Coupon.DiscountType.PERCENTAGE, discount_value='10.00')


@pytest.fixture
def basket_with_item(api_client, regular_user, product):
    """Authenticate as regular_user with £50 already in their basket."""
    api_client.force_authenticate(regular_user)
    api_client.post(BASKET_ITEMS_URL, {'product_id': product.id, 'qty': 1}, format='json')
    return api_client


@pytest.mark.django_db
class TestBasketCoupon:
    def test_apply_valid_coupon_discounts_total(self, basket_with_item, coupon):
        response = basket_with_item.post(BASKET_COUPON_URL, {'code': 'save10'}, format='json')

        assert response.status_code == 200
        assert response.data['coupon_code'] == 'SAVE10'
        assert response.data['discount_amount'] == '5.00'
        assert response.data['total'] == '45.00'

    def test_apply_unknown_code_returns_404(self, basket_with_item):
        response = basket_with_item.post(BASKET_COUPON_URL, {'code': 'NOPE'}, format='json')
        assert response.status_code == 404

    def test_apply_inactive_coupon_returns_400(self, basket_with_item, coupon):
        coupon.is_active = False
        coupon.save()

        response = basket_with_item.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        assert response.status_code == 400

    def test_apply_requires_code(self, basket_with_item):
        response = basket_with_item.post(BASKET_COUPON_URL, {}, format='json')
        assert response.status_code == 400

    def test_remove_coupon_reverts_total(self, basket_with_item, coupon):
        basket_with_item.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        response = basket_with_item.delete(BASKET_COUPON_URL)

        assert response.status_code == 200
        assert response.data['coupon_code'] is None
        assert response.data['total'] == '50.00'

    def test_basket_detail_reflects_applied_coupon(self, basket_with_item, coupon):
        basket_with_item.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        response = basket_with_item.get(BASKET_URL)

        assert response.data['coupon_code'] == 'SAVE10'
        assert response.data['total'] == '45.00'

    def test_coupon_below_minimum_order_value_rejected(self, basket_with_item, coupon):
        coupon.min_order_value = '100.00'
        coupon.save()

        response = basket_with_item.post(BASKET_COUPON_URL, {'code': 'SAVE10'}, format='json')

        assert response.status_code == 400

    def test_empty_basket_has_no_discount_fields_error(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.get(BASKET_URL)
        assert response.data['total'] == '0.00'
        assert response.data['coupon_code'] is None
