"""
Authorization coverage tests for admin-only store endpoints — verifies
IsAdminUser is actually enforced (not just present in the source), and that
the admin audit log (apps/core/models.AdminActionLog) records writes.
"""

import pytest

from apps.account.models import UserBase
from apps.core.models import AdminActionLog
from apps.orders.models import Order, OrderItem, OrderStatus
from .models import Category, Product, Review

ADMIN_PRODUCTS_URL = '/api/v1/admin/products/'
ADMIN_CATEGORIES_URL = '/api/v1/admin/categories/'
ADMIN_REVIEWS_URL = '/api/v1/admin/reviews/'


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


@pytest.mark.django_db
class TestProductReviews:
    REVIEWS_URL = '/api/v1/products/widget/reviews/'

    def test_list_only_shows_approved_reviews(self, api_client, regular_user, product):
        other = UserBase.objects.create(email='other@example.com', user_name='other', is_active=True)
        Review.objects.create(product=product, user=regular_user, rating=5, is_approved=True)
        Review.objects.create(product=product, user=other, rating=1, is_approved=False)

        response = api_client.get(self.REVIEWS_URL)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['rating'] == 5

    def test_unauthenticated_cannot_submit_review(self, api_client, product):
        response = api_client.post(self.REVIEWS_URL, {'rating': 4}, format='json')
        assert response.status_code == 401

    def test_authenticated_user_can_submit_review_pending_approval(self, api_client, regular_user, product):
        api_client.force_authenticate(regular_user)
        response = api_client.post(
            self.REVIEWS_URL, {'rating': 4, 'title': 'Good', 'comment': 'Solid product.'}, format='json'
        )

        assert response.status_code == 201
        assert response.data['is_approved'] is False
        review = Review.objects.get(product=product, user=regular_user)
        assert review.rating == 4
        assert review.is_approved is False

    def test_cannot_review_same_product_twice(self, api_client, regular_user, product):
        Review.objects.create(product=product, user=regular_user, rating=3)
        api_client.force_authenticate(regular_user)

        response = api_client.post(self.REVIEWS_URL, {'rating': 5}, format='json')

        assert response.status_code == 400
        assert Review.objects.filter(product=product, user=regular_user).count() == 1

    def test_verified_purchase_flag_set_from_confirmed_order(self, api_client, regular_user, product):
        order = Order.objects.create(
            user=regular_user, order_key='key123', total_paid=product.price,
            status=OrderStatus.CONFIRMED, full_name='Test', email='t@example.com',
            address_line_1='1 St', city='London', postcode='AA1 1AA', country='UK',
        )
        OrderItem.objects.create(
            order=order, product=product, product_title=product.title,
            price=product.price, quantity=1,
        )
        api_client.force_authenticate(regular_user)

        response = api_client.post(self.REVIEWS_URL, {'rating': 5}, format='json')

        assert response.status_code == 201
        review = Review.objects.get(product=product, user=regular_user)
        assert review.verified_purchase is True

    def test_average_rating_only_reflects_approved_reviews(self, api_client, regular_user, product):
        u2 = UserBase.objects.create(email='u2@example.com', user_name='u2', is_active=True)
        Review.objects.create(product=product, user=regular_user, rating=5, is_approved=True)
        Review.objects.create(product=product, user=u2, rating=1, is_approved=False)

        response = api_client.get('/api/v1/products/widget/')

        assert response.status_code == 200
        assert response.data['average_rating'] == 5.0
        assert response.data['review_count'] == 1


@pytest.mark.django_db
class TestReviewModeration:
    def test_non_staff_cannot_list_admin_reviews(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.get(ADMIN_REVIEWS_URL)
        assert response.status_code == 403

    def test_staff_can_approve_a_review(self, api_client, staff_user, regular_user, product):
        review = Review.objects.create(product=product, user=regular_user, rating=4)
        api_client.force_authenticate(staff_user)

        response = api_client.patch(
            f'{ADMIN_REVIEWS_URL}{review.id}/', {'is_approved': True}, format='json'
        )

        assert response.status_code == 200
        review.refresh_from_db()
        assert review.is_approved is True
        assert AdminActionLog.objects.filter(action='review_approve').exists()

    def test_staff_can_delete_a_review(self, api_client, staff_user, regular_user, product):
        review = Review.objects.create(product=product, user=regular_user, rating=1)
        api_client.force_authenticate(staff_user)

        response = api_client.delete(f'{ADMIN_REVIEWS_URL}{review.id}/')

        assert response.status_code == 204
        assert not Review.objects.filter(id=review.id).exists()
        assert AdminActionLog.objects.filter(action='review_delete').exists()

    def test_admin_review_list_filters_by_approval_status(self, api_client, staff_user, regular_user, product):
        u2 = UserBase.objects.create(email='u3@example.com', user_name='u3', is_active=True)
        Review.objects.create(product=product, user=regular_user, rating=5, is_approved=True)
        Review.objects.create(product=product, user=u2, rating=2, is_approved=False)
        api_client.force_authenticate(staff_user)

        response = api_client.get(f'{ADMIN_REVIEWS_URL}?is_approved=false')

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['rating'] == 2
