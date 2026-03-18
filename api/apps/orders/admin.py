from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_title', 'price', 'quantity', 'line_total')

    def line_total(self, obj):
        return obj.line_total
    line_total.short_description = 'Line total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'status', 'total_paid',
        'billing_status', 'created'
    )
    list_filter = ('status', 'billing_status')
    search_fields = ('order_number', 'user__email', 'full_name')
    readonly_fields = ('order_number', 'order_key', 'created', 'updated')
    list_editable = ('status',)
    inlines = [OrderItemInline]
