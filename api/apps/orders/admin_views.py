"""
Admin-only endpoint to manually mark an order as paid.
Used when Stripe is not yet configured or for testing.
"""
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status as drf_status
from apps.core.audit import log_admin_action
from apps.orders.models import Order, OrderStatus
from apps.orders.serializers import OrderSerializer
from apps.rbac.permissions import RequiresPermission


@api_view(['POST'])
@permission_classes([RequiresPermission('orders.advance_status')])
def admin_order_mark_paid(request, order_number):
    """Manually mark an order as paid (billing_status=True, status=confirmed)."""
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Order not found.'},
            status=drf_status.HTTP_404_NOT_FOUND,
        )
    order.billing_status = True
    order.status = OrderStatus.CONFIRMED
    order.save(update_fields=['billing_status', 'status'])
    log_admin_action(request, 'order_mark_paid', f'Order #{order.order_number}')
    return Response(OrderSerializer(order).data)
