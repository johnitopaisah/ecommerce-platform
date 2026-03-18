"""
Root URL configuration.
All API routes are versioned under /api/v1/
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from apps.store import views as store_views, admin_views as store_admin_views
from apps.orders import views as order_views
from apps.orders.admin_views import admin_order_mark_paid
from apps.account import views as account_views

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('api/v1/', include([

        path('', include('apps.core.urls', namespace='core')),
        path('auth/', include('apps.account.urls', namespace='account')),
        path('products/', include('apps.store.urls', namespace='store')),

        path('categories/', store_views.category_list, name='category_list'),
        path('categories/<slug:slug>/', store_views.category_detail, name='category_detail'),
        path('categories/<slug:slug>/products/', store_views.category_products, name='category_products'),

        path('basket/', include('apps.basket.urls', namespace='basket')),
        path('orders/', include('apps.orders.urls', namespace='orders')),
        path('payment/', include('apps.payment.urls', namespace='payment')),

        path('admin/', include([
            # Products
            path('products/', store_admin_views.admin_product_list, name='admin_product_list'),
            path('products/<slug:slug>/', store_admin_views.admin_product_detail, name='admin_product_detail'),
            path('products/<slug:slug>/images/', store_admin_views.admin_product_image_upload, name='admin_product_image_upload'),
            path('products/<slug:slug>/images/<int:image_id>/', store_admin_views.admin_product_image_delete, name='admin_product_image_delete'),

            # Categories
            path('categories/', store_admin_views.admin_category_list, name='admin_category_list'),
            path('categories/<slug:slug>/', store_admin_views.admin_category_detail, name='admin_category_detail'),

            # Orders
            path('orders/', order_views.admin_order_list, name='admin_order_list'),
            path('orders/<str:order_number>/status/', order_views.admin_order_status_update, name='admin_order_status_update'),
            path('orders/<str:order_number>/mark-paid/', admin_order_mark_paid, name='admin_order_mark_paid'),

            # Users
            path('users/', account_views.admin_user_list, name='admin_user_list'),
            path('users/<int:user_id>/', account_views.admin_user_detail, name='admin_user_detail'),
            path('users/<int:user_id>/deactivate/', account_views.admin_user_deactivate, name='admin_user_deactivate'),

            # Stats
            path('stats/', account_views.admin_stats, name='admin_stats'),
        ])),
    ])),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
