from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_title', 'price', 'quantity', 'line_total')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'order_key', 'status', 'status_display',
            'total_paid', 'billing_status',
            'full_name', 'email', 'phone',
            'address_line_1', 'address_line_2', 'city', 'postcode', 'country',
            'items', 'created', 'updated',
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    """
    Body sent by the front-end to create an order.
    The basket is read from Redis — items are not sent in the request body.
    """
    order_key = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address_line_1 = serializers.CharField(max_length=250)
    address_line_2 = serializers.CharField(max_length=250, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    postcode = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100)


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Admin-only: update order status."""
    status = serializers.ChoiceField(choices=[s[0] for s in Order._meta.get_field('status').choices])
