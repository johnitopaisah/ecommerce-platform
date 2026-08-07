from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'discount_value', 'is_active',
        'times_used', 'usage_limit', 'valid_until', 'created',
    )
    list_filter = ('is_active', 'discount_type')
    list_editable = ('is_active',)
    search_fields = ('code',)
    readonly_fields = ('times_used', 'created', 'updated')
