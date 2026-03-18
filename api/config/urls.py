"""
URL configuration for the e-commerce API.
All routes are versioned under /api/v1/
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

urlpatterns = [
    # Django admin (kept for direct DB management)
    path('django-admin/', admin.site.urls),

    # API v1
    path('api/v1/', include([
        # Core / health
        path('', include('apps.core.urls', namespace='core')),

        # Auth & accounts
        path('auth/', include('apps.account.urls', namespace='account')),

        # Store
        path('products/', include('apps.store.urls', namespace='store')),

        # Basket
        path('basket/', include('apps.basket.urls', namespace='basket')),

        # Orders
        path('orders/', include('apps.orders.urls', namespace='orders')),

        # Payment
        path('payment/', include('apps.payment.urls', namespace='payment')),
    ])),

    # OpenAPI schema + docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
