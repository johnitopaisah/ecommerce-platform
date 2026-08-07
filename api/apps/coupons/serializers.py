from rest_framework import serializers
from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = (
            'id', 'code', 'discount_type', 'discount_value', 'is_active',
            'valid_from', 'valid_until', 'min_order_value', 'usage_limit',
            'times_used', 'created', 'updated',
        )
        read_only_fields = ('id', 'times_used', 'created', 'updated')

    def validate(self, attrs):
        discount_type = attrs.get('discount_type', getattr(self.instance, 'discount_type', None))
        discount_value = attrs.get('discount_value', getattr(self.instance, 'discount_value', None))
        if discount_type == Coupon.DiscountType.PERCENTAGE and discount_value is not None and discount_value > 100:
            raise serializers.ValidationError(
                {'discount_value': 'Percentage discounts cannot exceed 100.'}
            )

        valid_from = attrs.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_until = attrs.get('valid_until', getattr(self.instance, 'valid_until', None))
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError(
                {'valid_until': 'Must be after the valid-from date.'}
            )
        return attrs

    def validate_code(self, value):
        code = value.upper().strip()
        if not code:
            raise serializers.ValidationError('Code cannot be blank.')
        qs = Coupon.objects.filter(code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A coupon with this code already exists.')
        return code
