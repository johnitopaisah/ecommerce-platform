from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from . import views

app_name = 'account'

urlpatterns = [
    # Registration & activation
    path('register/', views.register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),

    # JWT — login / refresh / logout
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Current user profile
    path('me/', views.me, name='me'),
    path('me/deactivate/', views.deactivate_me, name='deactivate_me'),
    path('me/change-password/', views.change_password, name='change_password'),

    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]
