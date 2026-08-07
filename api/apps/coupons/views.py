"""
Admin-only coupon management. Coupons are never listed publicly — a
customer applies one by typing its code at checkout (apps/basket/views.py).
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsAdminUser
from apps.core.audit import log_admin_action
from .models import Coupon
from .serializers import CouponSerializer


@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_coupon_list(request):
    if request.method == 'GET':
        coupons = Coupon.objects.all()
        return Response(CouponSerializer(coupons, many=True).data)

    serializer = CouponSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    coupon = serializer.save()
    log_admin_action(request, 'coupon_create', f'Coupon: {coupon.code}')
    return Response(CouponSerializer(coupon).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_coupon_detail(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Coupon not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(CouponSerializer(coupon).data)

    if request.method == 'DELETE':
        log_admin_action(request, 'coupon_delete', f'Coupon: {coupon.code}')
        coupon.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CouponSerializer(
        coupon, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_admin_action(request, 'coupon_update', f'Coupon: {coupon.code}', dict(request.data))
    return Response(serializer.data)
