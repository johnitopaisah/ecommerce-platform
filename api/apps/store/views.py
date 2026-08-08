"""
Store views — public product and category endpoints.

Public endpoints (no auth required):
  GET  /api/v1/products/                    list products (filter, search, paginate)
  GET  /api/v1/products/<slug>/             product detail
  GET  /api/v1/products/<slug>/reviews/     list approved reviews (POST to create, auth required)
  GET  /api/v1/categories/                  list active categories
  GET  /api/v1/categories/<slug>/           category detail
  GET  /api/v1/categories/<slug>/products/  products in a category

Admin endpoints (RBAC-permission gated) — in admin_views.py
"""

from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.orders.models import OrderItem, OrderStatus
from .models import Category, Product, Review, WishlistItem
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    WishlistItemSerializer,
)
from .filters import ProductFilter

# Reused by both product_list and product_detail so the annotation logic
# (and the "approved reviews only" rule) lives in exactly one place.
RATING_ANNOTATIONS = {
    'average_rating': Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
    'review_count': Count('reviews', filter=Q(reviews__is_approved=True)),
}


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ── Categories ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['categories'])
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])  # public storefront browsing, not a brute-force target —
# blanket DEFAULT_THROTTLE_RATES['anon'] broke the homepage: user-ui's SSR
# proxies every visitor's request through http://api:8000 from the same pod
# IP, so all real traffic shared one 100/hour bucket and exhausted it almost
# immediately. Same root cause as the earlier health-check throttle incident.
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
@throttle_classes([])
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
@throttle_classes([])
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
@throttle_classes([])
def product_list(request):
    """
    List all active products.
    Supports filtering, searching and ordering via query params.
    """
    products = (
        Product.active
        .select_related('category')
        .prefetch_related('images')
        .annotate(**RATING_ANNOTATIONS)
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
@throttle_classes([])
def product_detail(request, slug):
    """Retrieve a single product by slug."""
    try:
        product = (
            Product.objects
            .filter(is_active=True)
            .select_related('category', 'created_by')
            .prefetch_related('images')
            .annotate(**RATING_ANNOTATIONS)
            .get(slug=slug)
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ProductDetailSerializer(product).data)


# ── Reviews ──────────────────────────────────────────────────────────────────

@extend_schema(tags=['products'])
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([])
def product_reviews(request, slug):
    """
    GET  — list approved reviews for a product (public).
    POST — submit a review (requires auth; one per user per product).
    """
    try:
        product = Product.objects.get(slug=slug, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        reviews = (
            Review.objects
            .filter(product=product, is_approved=True)
            .select_related('user')
        )
        return Response(ReviewSerializer(reviews, many=True).data)

    # POST — creating a review requires auth, checked explicitly here (not
    # via @permission_classes) so GET stays public on the same endpoint.
    if not request.user.is_authenticated:
        return Response(
            {'error': 'unauthorized', 'detail': 'You must be signed in to leave a review.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if Review.objects.filter(product=product, user=request.user).exists():
        return Response(
            {'error': 'bad_request', 'detail': 'You have already reviewed this product.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    verified_purchase = OrderItem.objects.filter(
        order__user=request.user,
        order__status__in=(OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED),
        product=product,
    ).exists()

    review = serializer.save(product=product, user=request.user, verified_purchase=verified_purchase)
    return Response(
        {**ReviewSerializer(review).data, 'is_approved': False,
         'detail': 'Thanks! Your review will appear once approved.'},
        status=status.HTTP_201_CREATED,
    )


# ── Wishlist ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['wishlist'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def wishlist_list(request):
    """List the current user's wishlist, most recently added first."""
    items = (
        WishlistItem.objects
        .filter(user=request.user)
        .select_related('product', 'product__category')
    )
    return Response(WishlistItemSerializer(items, many=True).data)


@extend_schema(tags=['wishlist'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def wishlist_add(request):
    """
    Add a product to the wishlist.
    Body: { "product_slug": "..." }
    Adding an already-wishlisted product is a no-op (200, not an error).
    """
    slug = request.data.get('product_slug')
    if not slug:
        return Response(
            {'error': 'bad_request', 'detail': 'product_slug is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        product = Product.objects.get(slug=slug, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    return Response(
        WishlistItemSerializer(item).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@extend_schema(tags=['wishlist'])
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def wishlist_remove(request, slug):
    """Remove a product from the current user's wishlist by product slug."""
    deleted, _ = WishlistItem.objects.filter(user=request.user, product__slug=slug).delete()
    if not deleted:
        return Response(
            {'error': 'not_found', 'detail': 'Item not in wishlist.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
