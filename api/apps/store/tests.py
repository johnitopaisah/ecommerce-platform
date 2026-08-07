"""
Authorization coverage tests for admin-only store endpoints — verifies
IsAdminUser is actually enforced (not just present in the source), and that
the admin audit log (apps/core/models.AdminActionLog) records writes.
"""

import pytest

from apps.core.models import AdminActionLog
from .models import Category, Product

ADMIN_PRODUCTS_URL = '/api/v1/admin/products/'
ADMIN_CATEGORIES_URL = '/api/v1/admin/categories/'


@pytest.fixture
def category(db):
    return Category.objects.create(name='Electronics', slug='electronics')


@pytest.fixture
def product(db, category, staff_user):
    return Product.objects.create(
        category=category, created_by=staff_user, title='Widget', slug='widget',
        price='19.99', stock_quantity=10,
    )


@pytest.mark.django_db
class TestAdminAuthorization:
    def test_anonymous_cannot_list_admin_products(self, api_client):
        response = api_client.get(ADMIN_PRODUCTS_URL)
        assert response.status_code == 401

    def test_regular_user_cannot_list_admin_products(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.get(ADMIN_PRODUCTS_URL)
        assert response.status_code == 403

    def test_staff_user_can_list_admin_products(self, api_client, staff_user):
        api_client.force_authenticate(staff_user)
        response = api_client.get(ADMIN_PRODUCTS_URL)
        assert response.status_code == 200

    def test_regular_user_cannot_create_category(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.post(ADMIN_CATEGORIES_URL, {'name': 'Books'}, format='json')
        assert response.status_code == 403
        assert not Category.objects.filter(name='Books').exists()

    def test_staff_user_can_create_category(self, api_client, staff_user):
        api_client.force_authenticate(staff_user)
        response = api_client.post(ADMIN_CATEGORIES_URL, {'name': 'Books'}, format='json')
        assert response.status_code == 201
        assert Category.objects.filter(name='Books').exists()


@pytest.mark.django_db
class TestAdminAuditLog:
    def test_product_price_update_is_logged(self, api_client, staff_user, product):
        api_client.force_authenticate(staff_user)
        response = api_client.patch(
            f'{ADMIN_PRODUCTS_URL}widget/', {'price': '24.99'}, format='json'
        )

        assert response.status_code == 200
        log = AdminActionLog.objects.get(action='product_update')
        assert log.actor == staff_user
        assert log.detail['before']['price'] == '19.99'
        assert log.detail['after']['price'] == '24.99'

    def test_product_delete_is_logged(self, api_client, staff_user, product):
        api_client.force_authenticate(staff_user)
        response = api_client.delete(f'{ADMIN_PRODUCTS_URL}widget/')

        assert response.status_code == 204
        assert AdminActionLog.objects.filter(action='product_delete', target='Product: Widget').exists()
