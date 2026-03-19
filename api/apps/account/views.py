"""
Account views — all JSON, no templates.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.permissions import IsAdminUser
from apps.core.email import send_activation_email, send_password_reset_email
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)
from .tokens import account_activation_token

User = get_user_model()


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


# ── Registration ───────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'], request=RegisterSerializer,
               responses={201: OpenApiResponse(description='Account created.')})
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    # Activation still hits the Django API — it will redirect to the front-end after success
    activation_url = f"{request.scheme}://{request.get_host()}/api/v1/auth/activate/{uid}/{token}/"
    send_activation_email(user, activation_url)

    return Response(
        {'detail': 'Account created. Please check your email to activate your account.'},
        status=status.HTTP_201_CREATED,
    )


# ── Activation ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'])
@api_view(['GET'])
@permission_classes([AllowAny])
def activate(request, uidb64, token):
    """
    Activate user account via emailed link.
    On success: redirects to the front-end /account/activated page with tokens
    in the URL so the front-end can log the user in automatically.
    On failure: redirects to front-end /account/activation-failed.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return HttpResponseRedirect(_frontend_url('/activation-failed?reason=invalid'))

    if not account_activation_token.check_token(user, token):
        return HttpResponseRedirect(_frontend_url('/activation-failed?reason=expired'))

    user.is_active = True
    user.save(update_fields=['is_active'])

    # Issue JWT tokens so the user is automatically logged in after activation
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_token = str(refresh)

    # Redirect to front-end with tokens — the /activated page will store them
    redirect_url = _frontend_url(
        f'/activated?access={access}&refresh={refresh_token}'
    )
    return HttpResponseRedirect(redirect_url)


# ── Profile ────────────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'], responses={200: UserSerializer})
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)
    serializer = UserUpdateSerializer(
        request.user, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@extend_schema(tags=['auth'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deactivate_me(request):
    request.user.is_active = False
    request.user.save(update_fields=['is_active'])
    return Response({'detail': 'Account deactivated.'})


# ── Change password ────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'], request=ChangePasswordSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not request.user.check_password(serializer.validated_data['old_password']):
        return Response(
            {'error': 'bad_request', 'detail': 'Current password is incorrect.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save(update_fields=['password'])
    return Response({'detail': 'Password changed successfully.'})


# ── Password reset ─────────────────────────────────────────────────────────────

@extend_schema(tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    email = request.data.get('email', '').lower().strip()
    if email:
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            pass
        else:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = _frontend_url(f'/reset-password/{uid}/{token}/')
            send_password_reset_email(user, reset_url)

    return Response({'detail': 'If that email exists, a reset link has been sent.'})


@extend_schema(tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
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
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'not_found', 'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        return Response(UserSerializer(user).data)
    serializer = UserUpdateSerializer(user, data=request.data, partial=(request.method == 'PATCH'))
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(user).data)


@extend_schema(tags=['admin'])
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_user_deactivate(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'not_found', 'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    user.is_active = False
    user.save(update_fields=['is_active'])
    return Response({'detail': f'User {user.email} deactivated.'})


# ── Admin dashboard stats ──────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum
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
    out_of_stock_products = Product.objects.filter(is_active=True, stock_quantity=0).count()

    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created__gte=today_start).count()
    pending_orders = Order.objects.filter(status=OrderStatus.PENDING).count()

    revenue_qs = Order.objects.exclude(
        status__in=[OrderStatus.CANCELLED, OrderStatus.REFUNDED]
    )
    revenue_total = revenue_qs.aggregate(total=Sum('total_paid'))['total'] or 0
    revenue_last_30 = revenue_qs.filter(created__gte=last_30_days).aggregate(
        total=Sum('total_paid')
    )['total'] or 0
    confirmed_total = Order.objects.filter(billing_status=True).aggregate(
        total=Sum('total_paid')
    )['total'] or 0

    return Response({
        'users': {'total': total_users, 'active': active_users, 'new_today': new_users_today},
        'products': {
            'total_active': total_products,
            'low_stock': low_stock_products,
            'out_of_stock': out_of_stock_products,
        },
        'orders': {'total': total_orders, 'today': orders_today, 'pending': pending_orders},
        'revenue': {
            'total': str(revenue_total),
            'last_30_days': str(revenue_last_30),
            'confirmed_total': str(confirmed_total),
        },
    })
