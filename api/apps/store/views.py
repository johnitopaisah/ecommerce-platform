"""
Store views — public product and category endpoints.

All endpoints are read-only and publicly accessible (no auth required).
Admin write endpoints live in apps/store/admin_views.py and are
mounted under /api/v1/admin/ in Phase 3.
"""

from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .filters import ProductFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


# ── Categories ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['categories'])
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """List all active categories with their product count."""
    categories = (
        Category.objects
        .filter(is_active=True)
        .annotate(product_count=Count('products', filter=__import__('django.db.models', fromlist=['Q']).Q(products__is_active=True)))
        .order_by('name')
    )
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@extend_schema(tags=['categories'])
@api_view(['GET'])
@permission_classes([AllowAny])
def category_detail(request, slug):
    """Retrieve a single category by slug."""
    try:
        category = (
            Category.objects
            .filter(is_active=True)
            .annotate(product_count=Count('products', filter=__import__('django.db.models', fromlist=['Q']).Q(products__is_active=True)))
            .get(slug=slug)
        )
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(CategorySerializer(category).data)


# ── Products ───────────────────────────────────────────────────────────────────

@extend_schema(
    tags=['products'],
    parameters=[
        OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category slug'),
        OpenApiParameter('min_price', OpenApiTypes.FLOAT, description='Minimum price'),
        OpenApiParameter('max_price', OpenApiTypes.FLOAT, description='Maximum price'),
        OpenApiParameter('in_stock', OpenApiTypes.BOOL, description='Filter by stock availability'),
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in title and description'),
        OpenApiParameter('ordering', OpenApiTypes.STR, description='Order by: price, -price, created, -created, title'),
    ],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    """
    List all available products.
    Supports filtering, searching, and ordering via query parameters.
    """
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework.filters import SearchFilter, OrderingFilter

    queryset = (
        Product.available
        .select_related('category')
        .prefetch_related('images')
    )

    # Apply filters
    filterset = ProductFilter(request.GET, queryset=queryset)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
    queryset = filterset.qs

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Ordering
    ordering = request.GET.get('ordering', '-created')
    allowed_orderings = {'price', '-price', 'created', '-created', 'title', '-title'}
    if ordering in allowed_orderings:
        queryset = queryset.order_by(ordering)

    # Pagination
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(queryset, request)
    serializer = ProductListSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@extend_schema(tags=['products'])
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, slug):
    """Retrieve a single product by slug."""
    try:
        product = (
            Product.objects
            .filter(is_active=True)
            .select_related('category')
            .prefetch_related('images')
            .get(slug=slug)
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ProductDetailSerializer(product, context={'request': request}).data)


@extend_schema(tags=['products'])
@api_view(['GET'])
@permission_classes([AllowAny])
def products_by_category(request, category_slug):
    """List all available products within a specific category."""
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    queryset = (
        Product.available
        .filter(category=category)
        .select_related('category')
        .prefetch_related('images')
    )

    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(queryset, request)
    serializer = ProductListSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)
