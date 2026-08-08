"""
Admin-only coupon management. Coupons are never listed publicly — a
customer applies one by typing its code at checkout (apps/basket/views.py).
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.core.audit import log_admin_action
from apps.rbac.permissions import require_permission
from .models import Coupon
from .serializers import CouponSerializer


@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_coupon_list(request):
    if request.method == 'GET':
        require_permission(request, 'coupons.view_coupon')
        coupons = Coupon.objects.all()
        return Response(CouponSerializer(coupons, many=True).data)

    require_permission(request, 'coupons.add_coupon')
    serializer = CouponSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    coupon = serializer.save()
    log_admin_action(request, 'coupon_create', f'Coupon: {coupon.code}')
    return Response(CouponSerializer(coupon).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_coupon_detail(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Coupon not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        require_permission(request, 'coupons.view_coupon')
        return Response(CouponSerializer(coupon).data)

    if request.method == 'DELETE':
        require_permission(request, 'coupons.delete_coupon')
        log_admin_action(request, 'coupon_delete', f'Coupon: {coupon.code}')
        coupon.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    require_permission(request, 'coupons.change_coupon')
    serializer = CouponSerializer(
        coupon, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_admin_action(request, 'coupon_update', f'Coupon: {coupon.code}', dict(request.data))
    return Response(serializer.data)
