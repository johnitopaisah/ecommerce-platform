"""
Admin-only store views — product and category management.
All endpoints require authentication plus a specific RBAC permission
(apps.rbac.permissions) — no longer a blanket is_staff check. See
apps.rbac.management.commands.seed_roles for which roles hold what.
"""

from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.core.audit import log_admin_action
from apps.rbac.permissions import RequiresPermission, require_permission, user_has_permission
from .models import Category, Product, ProductImage, Review
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductImageSerializer,
    ReviewModerationSerializer,
)


# ── Category management ────────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_category_list(request):
    if request.method == 'GET':
        require_permission(request, 'store.view_category')
        categories = Category.objects.all().order_by('name')
        return Response(CategorySerializer(categories, many=True).data)

    require_permission(request, 'store.add_category')
    serializer = CategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    name = serializer.validated_data['name']
    slug = slugify(name)
    base_slug = slug
    counter = 1
    while Category.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    serializer.save(slug=slug)
    log_admin_action(request, 'category_create', f'Category: {name}')
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_category_detail(request, slug):
    try:
        category = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        require_permission(request, 'store.view_category')
        return Response(CategorySerializer(category).data)

    if request.method == 'DELETE':
        require_permission(request, 'store.delete_category')
        log_admin_action(request, 'category_delete', f'Category: {category.name}')
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    require_permission(request, 'store.change_category')
    serializer = CategorySerializer(
        category, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_admin_action(request, 'category_update', f'Category: {category.name}', dict(request.data))
    return Response(serializer.data)


# ── Product management ─────────────────────────────────────────────────────────

# Fields covered by the narrower manage_inventory/manage_pricing permissions
# — anything else on the product still needs full change_product. Lets an
# Inventory Manager (stock only) or a role with just manage_pricing touch
# their slice of a product without also being able to rewrite its title,
# description, category, or active status.
_PRICING_FIELDS = {'price', 'discount_price'}
_INVENTORY_FIELDS = {'stock_quantity'}


def _require_product_write_permission(request):
    if user_has_permission(request.user, 'store.change_product'):
        return
    fields = set(request.data.keys())
    other_fields = fields - _PRICING_FIELDS - _INVENTORY_FIELDS
    if other_fields:
        require_permission(request, 'store.change_product')
    if fields & _PRICING_FIELDS:
        require_permission(request, 'store.manage_pricing')
    if fields & _INVENTORY_FIELDS:
        require_permission(request, 'store.manage_inventory')


@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_product_list(request):
    if request.method == 'GET':
        require_permission(request, 'store.view_product')
        products = (
            Product.objects
            .all()
            .select_related('category', 'created_by')
            .order_by('-created')
        )
        return Response(ProductDetailSerializer(products, many=True).data)

    require_permission(request, 'store.add_product')
    serializer = ProductWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product = serializer.save(created_by=request.user)
    log_admin_action(
        request, 'product_create', f'Product: {product.title}',
        {'price': str(product.price), 'stock_quantity': product.stock_quantity},
    )
    return Response(
        ProductDetailSerializer(product).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_product_detail(request, slug):
    try:
        product = (
            Product.objects
            .select_related('category', 'created_by')
            .prefetch_related('images')
            .get(slug=slug)
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        require_permission(request, 'store.view_product')
        return Response(ProductDetailSerializer(product).data)

    if request.method == 'DELETE':
        require_permission(request, 'store.delete_product')
        log_admin_action(request, 'product_delete', f'Product: {product.title}')
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    _require_product_write_permission(request)
    before = {'price': str(product.price), 'stock_quantity': product.stock_quantity}
    serializer = ProductWriteSerializer(
        product, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    after = {'price': str(product.price), 'stock_quantity': product.stock_quantity}
    log_admin_action(
        request, 'product_update', f'Product: {product.title}',
        {'before': before, 'after': after} if before != after else {},
    )
    return Response(ProductDetailSerializer(product).data)


# ── Product image management ───────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_product_image_upload(request, slug):
    """
    Upload an image for a product.
    When is_primary=True (the default from the admin UI), the uploaded image
    is also set as the product's main image field so it appears on the storefront.
    """
    require_permission(request, 'store.change_product')
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ProductImageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product_image = serializer.save(product=product)

    # If this is marked as primary (or it's the first image), also update
    # the product's main image field so the storefront shows it immediately.
    is_primary = request.data.get('is_primary', 'true')
    is_first_image = not ProductImage.objects.filter(
        product=product
    ).exclude(id=product_image.id).exists()

    if is_primary in (True, 'true', 'True', '1') or is_first_image:
        # Clear previous primary flags
        ProductImage.objects.filter(product=product, is_primary=True).exclude(
            id=product_image.id
        ).update(is_primary=False)
        product_image.is_primary = True
        product_image.save(update_fields=['is_primary'])

        # Sync the product's main image field
        product.image = product_image.image
        product.save(update_fields=['image'])

    return Response(
        ProductImageSerializer(product_image).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=['admin'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_product_image_delete(request, slug, image_id):
    require_permission(request, 'store.change_product')
    try:
        image = ProductImage.objects.get(id=image_id, product__slug=slug)
    except ProductImage.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Image not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    was_primary = image.is_primary
    product = image.product
    image.delete()

    # If we deleted the primary image, promote the next image
    # and update the product's main image field
    if was_primary:
        next_image = ProductImage.objects.filter(product=product).first()
        if next_image:
            next_image.is_primary = True
            next_image.save(update_fields=['is_primary'])
            product.image = next_image.image
        else:
            product.image = 'products/default.png'
        product.save(update_fields=['image'])

    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Review moderation ─────────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([RequiresPermission('store.view_review')])
def admin_review_list(request):
    """
    List all reviews for moderation.
    ?is_approved=false — the moderation queue (default view for admin-ui).
    ?is_approved=true  — already-published reviews.
    Omit the param to see everything.
    """
    reviews = Review.objects.select_related('product', 'user').order_by('-created')

    is_approved = request.query_params.get('is_approved')
    if is_approved is not None:
        reviews = reviews.filter(is_approved=is_approved.lower() == 'true')

    return Response(ReviewModerationSerializer(reviews, many=True).data)


@extend_schema(tags=['admin'])
@api_view(['PATCH', 'DELETE'])
@permission_classes([RequiresPermission('store.moderate_reviews')])
def admin_review_detail(request, review_id):
    """PATCH {is_approved: true/false} to moderate; DELETE to remove."""
    try:
        review = Review.objects.select_related('product', 'user').get(id=review_id)
    except Review.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Review not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'DELETE':
        target = f'Review on {review.product.title} by {review.user.email}'
        review.delete()
        log_admin_action(request, 'review_delete', target)
        return Response(status=status.HTTP_204_NO_CONTENT)

    is_approved = request.data.get('is_approved')
    if is_approved is None:
        return Response(
            {'error': 'bad_request', 'detail': 'is_approved is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    review.is_approved = bool(is_approved)
    review.save(update_fields=['is_approved'])
    log_admin_action(
        request,
        'review_approve' if review.is_approved else 'review_reject',
        f'Review on {review.product.title} by {review.user.email}',
    )
    return Response(ReviewModerationSerializer(review).data)
