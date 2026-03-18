"""
Store views — public product and category endpoints.

Public endpoints (no auth required):
  GET  /api/v1/products/                    list products (filter, search, paginate)
  GET  /api/v1/products/<slug>/             product detail
  GET  /api/v1/categories/                  list active categories
  GET  /api/v1/categories/<slug>/           category detail
  GET  /api/v1/categories/<slug>/products/  products in a category

Admin endpoints (is_staff required) — in admin_views.py
"""

from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)
from .filters import ProductFilter


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ── Categories ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['categories'])
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """List all active categories with product counts."""
    categories = (
        Category.objects
        .filter(is_active=True)
        .annotate(product_count=Count('products'))
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
            .annotate(product_count=Count('products'))
            .get(slug=slug)
        )
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(CategorySerializer(category).data)


@extend_schema(tags=['categories'])
@api_view(['GET'])
@permission_classes([AllowAny])
def category_products(request, slug):
    """List all active products in a specific category."""
    try:
        category = Category.objects.get(slug=slug, is_active=True)
    except Category.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Category not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    products = (
        Product.active
        .filter(category=category)
        .select_related('category')
    )

    # Apply ordering
    ordering = request.query_params.get('ordering', '-created')
    allowed_orderings = ('price', '-price', 'created', '-created', 'title', '-title')
    if ordering in allowed_orderings:
        products = products.order_by(ordering)

    paginator = ProductPagination()
    page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


# ── Products ───────────────────────────────────────────────────────────────────

@extend_schema(
    tags=['products'],
    parameters=[
        OpenApiParameter('category', str, description='Filter by category slug'),
        OpenApiParameter('min_price', float, description='Minimum price'),
        OpenApiParameter('max_price', float, description='Maximum price'),
        OpenApiParameter('in_stock', bool, description='In stock only'),
        OpenApiParameter('search', str, description='Search in title and description'),
        OpenApiParameter('ordering', str, description='Order by: price, -price, created, -created, title'),
    ],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    """
    List all active products.
    Supports filtering, searching and ordering via query params.
    """
    products = (
        Product.active
        .select_related('category')
        .prefetch_related('images')
    )

    # Filter
    filterset = ProductFilter(request.GET, queryset=products)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
    products = filterset.qs

    # Search
    search = request.query_params.get('search', '').strip()
    if search:
        products = products.filter(
            title__icontains=search
        ) | products.filter(
            description__icontains=search
        )

    # Ordering
    ordering = request.query_params.get('ordering', '-created')
    allowed_orderings = ('price', '-price', 'created', '-created', 'title', '-title')
    if ordering in allowed_orderings:
        products = products.order_by(ordering)

    paginator = ProductPagination()
    page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(page, many=True)
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
            .select_related('category', 'created_by')
            .prefetch_related('images')
            .get(slug=slug)
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ProductDetailSerializer(product).data)
