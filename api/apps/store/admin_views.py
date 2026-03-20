"""
Admin-only store views — product and category management.
All endpoints require is_staff=True.
"""

from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsAdminUser
from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductImageSerializer,
)


# ── Category management ────────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all().order_by('name')
        return Response(CategorySerializer(categories, many=True).data)

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
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_category_detail(request, slug):
    try:
        category = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(CategorySerializer(category).data)

    if request.method == 'DELETE':
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CategorySerializer(
        category, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# ── Product management ─────────────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_product_list(request):
    if request.method == 'GET':
        products = (
            Product.objects
            .all()
            .select_related('category', 'created_by')
            .order_by('-created')
        )
        return Response(ProductDetailSerializer(products, many=True).data)

    serializer = ProductWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product = serializer.save(created_by=request.user)
    return Response(
        ProductDetailSerializer(product).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=['admin'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
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
        return Response(ProductDetailSerializer(product).data)

    if request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProductWriteSerializer(
        product, data=request.data, partial=(request.method == 'PATCH')
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(ProductDetailSerializer(product).data)


# ── Product image management ───────────────────────────────────────────────────

@extend_schema(tags=['admin'])
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_product_image_upload(request, slug):
    """
    Upload an image for a product.
    When is_primary=True (the default from the admin UI), the uploaded image
    is also set as the product's main image field so it appears on the storefront.
    """
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
@permission_classes([IsAdminUser])
def admin_product_image_delete(request, slug, image_id):
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
