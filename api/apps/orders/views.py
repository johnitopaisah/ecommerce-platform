"""
Orders views.

POST   /api/v1/orders/               create order from current basket
GET    /api/v1/orders/               list current user's paid orders
GET    /api/v1/orders/<order_number>/ order detail
POST   /api/v1/orders/<order_number>/cancel/  cancel order

Admin:
GET    /api/v1/admin/orders/                  all orders
PUT    /api/v1/admin/orders/<order_number>/status/  update status
"""

from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.basket import service as basket_service
from apps.core.permissions import IsAdminUser
from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer


# ── Customer endpoints ─────────────────────────────────────────────────────────

@extend_schema(tags=['orders'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    """
    GET  — list the current user's paid orders.
    POST — create a new order from the current basket.
    """
    if request.method == 'GET':
        orders = (
            Order.objects
            .filter(user=request.user, billing_status=True)
            .prefetch_related('items')
            .order_by('-created')
        )
        return Response(OrderSerializer(orders, many=True).data)

    # POST — create order
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Prevent duplicate order for the same payment intent
    if Order.objects.filter(order_key=data['order_key']).exists():
        order = Order.objects.get(order_key=data['order_key'])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    # Pull basket from Redis
    basket_summary = basket_service.get_basket_summary(request)
    if not basket_summary['items']:
        return Response(
            {'error': 'bad_request', 'detail': 'Your basket is empty.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    total = Decimal(basket_summary['subtotal'])

    order = Order.objects.create(
        user=request.user,
        order_key=data['order_key'],
        total_paid=total,
        full_name=data['full_name'],
        email=data['email'],
        phone=data.get('phone', ''),
        address_line_1=data['address_line_1'],
        address_line_2=data.get('address_line_2', ''),
        city=data['city'],
        postcode=data['postcode'],
        country=data['country'],
    )

    for item in basket_summary['items']:
        OrderItem.objects.create(
            order=order,
            product_id=item['product_id'],
            product_title=item['title'],
            price=Decimal(item['price']),
            quantity=item['qty'],
        )

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['orders'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_number):
    """Retrieve a single order belonging to the current user."""
    try:
        order = (
            Order.objects
            .prefetch_related('items')
            .get(order_number=order_number, user=request.user)
        )
    except Order.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(OrderSerializer(order).data)


@extend_schema(tags=['orders'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_cancel(request, order_number):
    """Cancel a pending order."""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    cancellable = (OrderStatus.PENDING, OrderStatus.CONFIRMED)
    if order.status not in cancellable:
        return Response(
            {'error': 'bad_request', 'detail': f'Orders with status "{order.status}" cannot be cancelled.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=['status'])
    return Response(OrderSerializer(order).data)


# ── Shared helper (called by payment webhook) ──────────────────────────────────

def confirm_payment(order_key: str):
    """Mark an order as paid. Called by the Stripe webhook."""
    updated = Order.objects.filter(order_key=order_key).update(
        billing_status=True,
        status=OrderStatus.CONFIRMED,
    )
    return updated > 0


# ── Admin endpoints ────────────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_order_list(request):
    """List all orders with optional status filter."""
    orders = Order.objects.prefetch_related('items').select_related('user').order_by('-created')

    status_filter = request.query_params.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    billing = request.query_params.get('billing_status')
    if billing is not None:
        orders = orders.filter(billing_status=(billing.lower() == 'true'))

    return Response(OrderSerializer(orders, many=True).data)


@extend_schema(tags=['admin'])
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_order_status_update(request, order_number):
    """Update the status of any order."""
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = OrderStatusUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order.status = serializer.validated_data['status']
    order.save(update_fields=['status'])
    return Response(OrderSerializer(order).data)
