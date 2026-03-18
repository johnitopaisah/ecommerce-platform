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
    """List all categories or create a new one."""
    if request.method == 'GET':
        categories = Category.objects.all().order_by('name')
        return Response(CategorySerializer(categories, many=True).data)

    serializer = CategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Auto-generate slug from name if not provided
    name = serializer.validated_data['name']
    slug = slugify(name)
    # Ensure uniqueness
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
    """Retrieve, update or delete a category."""
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
    """List all products (including inactive) or create a new one."""
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
    """Retrieve, update or delete a product."""
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
    """Upload an additional image for a product."""
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ProductImageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(product=product)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['admin'])
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_product_image_delete(request, slug, image_id):
    """Delete a product image."""
    try:
        image = ProductImage.objects.get(id=image_id, product__slug=slug)
    except ProductImage.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Image not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    image.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
