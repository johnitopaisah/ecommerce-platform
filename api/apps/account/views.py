"""
Account views — all JSON, no templates.

Endpoints (all under /api/v1/auth/):
  POST   register/                    — create account, send activation email
  GET    activate/<uidb64>/<token>/   — activate account via email link
  GET    me/                          — get current user profile
  PUT    me/                          — update current user profile
  DELETE me/deactivate/               — deactivate account (soft delete)
  POST   me/change-password/          — change password (requires old password)
  POST   token/                       — obtain JWT pair (login)
  POST   token/refresh/               — refresh access token
  POST   token/blacklist/             — logout (blacklist refresh token)
  POST   password-reset/              — request password reset email
  POST   password-reset/confirm/      — confirm reset with uid + token + new password

Admin endpoints (under /api/v1/admin/):
  GET    users/                       — list all users
  GET    users/<id>/                  — user detail
  PUT    users/<id>/                  — update user
  POST   users/<id>/deactivate/       — deactivate user
  GET    stats/                       — platform dashboard stats
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.permissions import IsAdminUser
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)
from .tokens import account_activation_token

User = get_user_model()


# ── Registration ───────────────────────────────────────────────────────────────

@extend_schema(
    tags=['auth'],
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description='Account created. Activation email sent.')},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Create a new user account and send activation email."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    _send_activation_email(request, user)
    return Response(
        {'detail': 'Account created. Please check your email to activate your account.'},
        status=status.HTTP_201_CREATED,
    )


def _send_activation_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_url = f'http://{current_site.domain}/api/v1/auth/activate/{uid}/{token}/'
    subject = 'Activate your account'
    message = (
        f'Hi {user.user_name},\n\n'
        f'Please click the link below to activate your account:\n\n'
        f'{activation_url}\n\n'
        f'If you did not register, please ignore this email.'
    )
    user.email_user(subject, message)


# ── Activation ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'])
@api_view(['GET'])
@permission_classes([AllowAny])
def activate(request, uidb64, token):
    """Activate user account via emailed link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'invalid_link', 'detail': 'Activation link is invalid.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not account_activation_token.check_token(user, token):
        return Response(
            {'error': 'invalid_link', 'detail': 'Activation link is expired or already used.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = True
    user.save(update_fields=['is_active'])

    refresh = RefreshToken.for_user(user)
    return Response({
        'detail': 'Account activated successfully.',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }, status=status.HTTP_200_OK)


# ── Profile ────────────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'], responses={200: UserSerializer})
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    """Retrieve or update the current user's profile."""
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)

    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=(request.method == 'PATCH'),
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@extend_schema(tags=['auth'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deactivate_me(request):
    """Soft-delete: mark the account as inactive."""
    request.user.is_active = False
    request.user.save(update_fields=['is_active'])
    return Response({'detail': 'Account deactivated.'}, status=status.HTTP_200_OK)


# ── Change password ────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'], request=ChangePasswordSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password — requires the current password for verification."""
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response(
            {'error': 'bad_request', 'detail': 'Current password is incorrect.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data['new_password'])
    user.save(update_fields=['password'])
    return Response({'detail': 'Password changed successfully.'})


# ── Password reset ─────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Send a password-reset email if the email exists.
    Always returns 200 to avoid user enumeration.
    """
    email = request.data.get('email', '').lower().strip()
    if email:
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            pass
        else:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            current_site = get_current_site(request)
            reset_url = f'http://{current_site.domain}/reset-password/{uid}/{token}/'
            subject = 'Reset your password'
            message = (
                f'Hi {user.user_name},\n\n'
                f'Click the link below to reset your password:\n\n'
                f'{reset_url}\n\n'
                f'This link expires in 1 hour.\n'
                f'If you did not request this, please ignore this email.'
            )
            user.email_user(subject, message)

    return Response({'detail': 'If that email exists, a reset link has been sent.'})


@extend_schema(tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset using uid + token from the emailed link."""
    uid = request.data.get('uid', '')
    token = request.data.get('token', '')
    new_password = request.data.get('new_password', '')
    new_password2 = request.data.get('new_password2', '')

    if not all([uid, token, new_password, new_password2]):
        return Response(
            {'error': 'bad_request', 'detail': 'uid, token, new_password and new_password2 are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if new_password != new_password2:
        return Response(
            {'error': 'bad_request', 'detail': 'Passwords do not match.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user_pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_pk, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'invalid_link', 'detail': 'Reset link is invalid or expired.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not default_token_generator.check_token(user, token):
        return Response(
            {'error': 'invalid_link', 'detail': 'Reset link is invalid or expired.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save(update_fields=['password'])
    return Response({'detail': 'Password has been reset successfully.'})


# ── Admin user management ──────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    """
    List all users.
    Optional query params: ?is_active=true|false, ?search=<email or username>
    """
    users = User.objects.all().order_by('-created')

    is_active = request.query_params.get('is_active')
    if is_active is not None:
        users = users.filter(is_active=(is_active.lower() == 'true'))

    search = request.query_params.get('search', '').strip()
    if search:
        users = users.filter(email__icontains=search) | users.filter(user_name__icontains=search)

    return Response(UserSerializer(users, many=True).data)


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_user_detail(request, user_id):
    """Retrieve or update any user account."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(UserSerializer(user).data)

    serializer = UserUpdateSerializer(
        user, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(user).data)


@extend_schema(tags=['admin'])
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_user_deactivate(request, user_id):
    """Deactivate a user account."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    user.is_active = False
    user.save(update_fields=['is_active'])
    return Response({'detail': f'User {user.email} deactivated.'})


# ── Admin dashboard stats ──────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """
    Return aggregate platform stats for the admin dashboard.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.orders.models import Order, OrderStatus
    from apps.store.models import Product

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_30_days = now - timedelta(days=30)

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(created__gte=today_start).count()

    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        is_active=True, stock_quantity__gt=0, stock_quantity__lte=5
    ).count()
    out_of_stock_products = Product.objects.filter(
        is_active=True, stock_quantity=0
    ).count()

    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created__gte=today_start).count()
    pending_orders = Order.objects.filter(status=OrderStatus.PENDING).count()

    from django.db.models import Sum
    revenue_total = (
        Order.objects
        .filter(billing_status=True)
        .aggregate(total=Sum('total_paid'))['total'] or 0
    )
    revenue_last_30_days = (
        Order.objects
        .filter(billing_status=True, created__gte=last_30_days)
        .aggregate(total=Sum('total_paid'))['total'] or 0
    )

    return Response({
        'users': {
            'total': total_users,
            'active': active_users,
            'new_today': new_users_today,
        },
        'products': {
            'total_active': total_products,
            'low_stock': low_stock_products,
            'out_of_stock': out_of_stock_products,
        },
        'orders': {
            'total': total_orders,
            'today': orders_today,
            'pending': pending_orders,
        },
        'revenue': {
            'total': str(revenue_total),
            'last_30_days': str(revenue_last_30_days),
        },
    })
