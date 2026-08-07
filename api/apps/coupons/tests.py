"""
Coupon model validity/discount math, and admin CRUD authorization.
Checkout-flow integration (basket apply, payment amount, order totals) is
covered in apps/basket/tests.py and apps/orders/tests.py.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from .models import Coupon

ADMIN_COUPONS_URL = '/api/v1/admin/coupons/'


@pytest.fixture
def percent_coupon(db):
    return Coupon.objects.create(
        code='SAVE10', discount_type=Coupon.DiscountType.PERCENTAGE, discount_value=Decimal('10.00')
    )


@pytest.fixture
def fixed_coupon(db):
    return Coupon.objects.create(
        code='FIVEOFF', discount_type=Coupon.DiscountType.FIXED, discount_value=Decimal('5.00')
    )


class TestCouponValidity:
    def test_valid_coupon_passes(self, percent_coupon):
        valid, error = percent_coupon.is_valid(Decimal('100.00'))
        assert valid is True
        assert error == ''

    def test_inactive_coupon_fails(self, percent_coupon):
        percent_coupon.is_active = False
        valid, error = percent_coupon.is_valid(Decimal('100.00'))
        assert valid is False
        assert 'active' in error.lower()

    def test_not_yet_started_coupon_fails(self, percent_coupon):
        percent_coupon.valid_from = timezone.now() + timedelta(days=1)
        valid, error = percent_coupon.is_valid(Decimal('100.00'))
        assert valid is False

    def test_expired_coupon_fails(self, percent_coupon):
        percent_coupon.valid_until = timezone.now() - timedelta(days=1)
        valid, error = percent_coupon.is_valid(Decimal('100.00'))
        assert valid is False
        assert 'expired' in error.lower()

    def test_usage_limit_reached_fails(self, percent_coupon):
        percent_coupon.usage_limit = 5
        percent_coupon.times_used = 5
        valid, error = percent_coupon.is_valid(Decimal('100.00'))
        assert valid is False
        assert 'limit' in error.lower()

    def test_below_minimum_order_value_fails(self, percent_coupon):
        percent_coupon.min_order_value = Decimal('50.00')
        valid, error = percent_coupon.is_valid(Decimal('20.00'))
        assert valid is False
        assert 'minimum' in error.lower()

    def test_meets_minimum_order_value_passes(self, percent_coupon):
        percent_coupon.min_order_value = Decimal('50.00')
        valid, error = percent_coupon.is_valid(Decimal('50.00'))
        assert valid is True


class TestCouponDiscountCalculation:
    def test_percentage_discount(self, percent_coupon):
        assert percent_coupon.calculate_discount(Decimal('100.00')) == Decimal('10.00')

    def test_fixed_discount(self, fixed_coupon):
        assert fixed_coupon.calculate_discount(Decimal('100.00')) == Decimal('5.00')

    def test_fixed_discount_never_exceeds_subtotal(self, fixed_coupon):
        assert fixed_coupon.calculate_discount(Decimal('2.00')) == Decimal('2.00')

    def test_percentage_discount_rounds_to_two_places(self, percent_coupon):
        percent_coupon.discount_value = Decimal('33.33')
        discount = percent_coupon.calculate_discount(Decimal('10.00'))
        assert discount == Decimal('3.33')


@pytest.mark.django_db
class TestCouponAdminAuthorization:
    def test_anonymous_cannot_list_coupons(self, api_client):
        response = api_client.get(ADMIN_COUPONS_URL)
        assert response.status_code == 401

    def test_regular_user_cannot_create_coupon(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.post(
            ADMIN_COUPONS_URL, {'code': 'HACK', 'discount_type': 'fixed', 'discount_value': '5.00'}, format='json'
        )
        assert response.status_code == 403

    def test_staff_can_create_coupon(self, api_client, staff_user):
        api_client.force_authenticate(staff_user)
        response = api_client.post(
            ADMIN_COUPONS_URL,
            {'code': 'newcode', 'discount_type': 'percentage', 'discount_value': '15.00'},
            format='json',
        )
        assert response.status_code == 201
        # Code is normalised to uppercase regardless of client casing.
        assert response.data['code'] == 'NEWCODE'

    def test_percentage_over_100_rejected(self, api_client, staff_user):
        api_client.force_authenticate(staff_user)
        response = api_client.post(
            ADMIN_COUPONS_URL,
            {'code': 'TOOBIG', 'discount_type': 'percentage', 'discount_value': '150.00'},
            format='json',
        )
        assert response.status_code == 400

    def test_duplicate_code_rejected(self, api_client, staff_user, percent_coupon):
        api_client.force_authenticate(staff_user)
        response = api_client.post(
            ADMIN_COUPONS_URL,
            {'code': 'save10', 'discount_type': 'fixed', 'discount_value': '1.00'},
            format='json',
        )
        assert response.status_code == 400

    def test_staff_can_deactivate_coupon(self, api_client, staff_user, percent_coupon):
        api_client.force_authenticate(staff_user)
        response = api_client.patch(
            f'{ADMIN_COUPONS_URL}{percent_coupon.id}/', {'is_active': False}, format='json'
        )
        assert response.status_code == 200
        percent_coupon.refresh_from_db()
        assert percent_coupon.is_active is False

    def test_staff_can_delete_coupon(self, api_client, staff_user, percent_coupon):
        api_client.force_authenticate(staff_user)
        response = api_client.delete(f'{ADMIN_COUPONS_URL}{percent_coupon.id}/')
        assert response.status_code == 204
        assert not Coupon.objects.filter(id=percent_coupon.id).exists()
