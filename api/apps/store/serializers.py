"""
Store serializers — Category, Product, ProductImage, Review.
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage, Review


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
    category_name = serializers.CharField(source='category.name', read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    # Annotated on the queryset (Avg/Count over approved reviews only) —
    # None/0 when there are no approved reviews yet.
    average_rating = serializers.FloatField(read_only=True, default=None)
    review_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'category_name',
            'price', 'discount_price', 'effective_price',
            'image', 'in_stock', 'stock_quantity', 'created',
            'average_rating', 'review_count',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
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
    average_rating = serializers.FloatField(read_only=True, default=None)
    review_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'slug', 'description',
            'category', 'category_id',
            'price', 'discount_price', 'effective_price',
            'image', 'images',
            'stock_quantity', 'in_stock',
            'is_active', 'created_by',
            'average_rating', 'review_count',
            'created', 'updated',
        )
        read_only_fields = ('id', 'slug', 'created', 'updated', 'created_by')


class ProductWriteSerializer(serializers.ModelSerializer):
    """
    Used by admin endpoints to create/update products via JSON.
    Image is handled separately via the /images/ endpoint (multipart upload).
    The product falls back to the default image until one is uploaded.
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
    )

    class Meta:
        model = Product
        fields = (
            'title', 'description', 'category_id',
            'price', 'discount_price',
            'stock_quantity', 'is_active',
        )
        # image intentionally excluded — use POST /products/{slug}/images/

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


# ── Reviews ──────────────────────────────────────────────────────────────────

class ReviewSerializer(serializers.ModelSerializer):
    """Public read shape — shown once a review is approved."""
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id', 'reviewer_name', 'rating', 'title', 'comment',
            'verified_purchase', 'created',
        )

    def get_reviewer_name(self, obj):
        name = obj.user.get_full_name()
        return name if name else obj.user.user_name


class ReviewCreateSerializer(serializers.ModelSerializer):
    """product/user/verified_purchase are set server-side, not client input."""

    class Meta:
        model = Review
        fields = ('rating', 'title', 'comment')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class ReviewModerationSerializer(serializers.ModelSerializer):
    """Admin list/detail — includes moderation state and identifying info."""
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    reviewer_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'product_title', 'product_slug', 'reviewer_email',
            'rating', 'title', 'comment', 'verified_purchase',
            'is_approved', 'created',
        )
        read_only_fields = fields
