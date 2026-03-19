"""
Store serializers — Category, Product, ProductImage.
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'is_active', 'product_count')
        read_only_fields = ('id', 'slug')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'ordering')


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no heavy fields."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category_name',
            'price', 'discount_price', 'effective_price',
            'image', 'in_stock', 'stock_quantity', 'created',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view — includes images and category."""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    images = ProductImageSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'description',
            'category', 'category_id',
            'price', 'discount_price', 'effective_price',
            'image', 'images',
            'stock_quantity', 'in_stock',
            'is_active', 'created_by',
            'created', 'updated',
        )
        read_only_fields = ('id', 'slug', 'created', 'updated', 'created_by')


class ProductWriteSerializer(serializers.ModelSerializer):
    """Used by admin endpoints to create/update products."""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
    )

    class Meta:
        model = Product
        fields = (
            'title', 'description', 'category_id',
            'price', 'discount_price',
            'image', 'stock_quantity', 'is_active',
        )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value

    def validate(self, attrs):
        discount = attrs.get('discount_price')
        price = attrs.get('price', getattr(self.instance, 'price', None))
        if discount and price and discount >= price:
            raise serializers.ValidationError(
                {'discount_price': 'Discount price must be less than the regular price.'}
            )
        return attrs
