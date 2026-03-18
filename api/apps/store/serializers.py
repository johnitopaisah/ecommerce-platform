"""
Store serializers — Category, Product list, Product detail, ProductImage.
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'is_active', 'product_count')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'ordering')


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no full description."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category', 'category_name',
            'price', 'stock_quantity', 'in_stock', 'primary_image',
            'created',
        )

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary:
            request = self.context.get('request')
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None

    def get_in_stock(self, obj):
        return obj.in_stock


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view — includes images and description."""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category', 'description',
            'price', 'stock_quantity', 'in_stock', 'images',
            'created', 'updated',
        )

    def get_in_stock(self, obj):
        return obj.in_stock


# ── Admin serializers (write-capable) ─────────────────────────────────────────

class ProductWriteSerializer(serializers.ModelSerializer):
    """Used by admin endpoints to create and update products."""

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category', 'description',
            'price', 'stock_quantity', 'is_active',
        )
        read_only_fields = ('id',)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value

    def validate_slug(self, value):
        qs = Product.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A product with this slug already exists.')
        return value


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'is_active')
        read_only_fields = ('id',)

    def validate_slug(self, value):
        qs = Category.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A category with this slug already exists.')
        return value
