"""
Basket views.

GET    /api/v1/basket/                 retrieve basket with hydrated product data
POST   /api/v1/basket/items/           add item  {product_id, qty}
PUT    /api/v1/basket/items/<id>/      update qty {qty}
DELETE /api/v1/basket/items/<id>/      remove item
DELETE /api/v1/basket/                 clear basket
POST   /api/v1/basket/merge/           merge anonymous basket on login
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.store.models import Product
from . import service


# ── Basket detail + clear ──────────────────────────────────────────────────────

@extend_schema(tags=['basket'])
@api_view(['GET', 'DELETE'])
@permission_classes([AllowAny])
def basket_detail(request):
    """
    GET  — return the full basket with hydrated product data.
    DELETE — clear the entire basket.
    """
    if request.method == 'DELETE':
        service.clear_basket(request)
        return Response({'detail': 'Basket cleared.'}, status=status.HTTP_200_OK)

    summary = service.get_basket_summary(request)
    return Response(summary)


# ── Add item ───────────────────────────────────────────────────────────────────

@extend_schema(tags=['basket'])
@api_view(['POST'])
@permission_classes([AllowAny])
def basket_add(request):
    """
    Add a product to the basket.
    Body: { "product_id": 1, "qty": 2 }
    """
    product_id = request.data.get('product_id')
    qty = request.data.get('qty', 1)

    # Validate
    if not product_id:
        return Response(
            {'error': 'bad_request', 'detail': 'product_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        qty = int(qty)
        if qty < 1:
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            {'error': 'bad_request', 'detail': 'qty must be a positive integer.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        product = Product.active.get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Product not found or out of stock.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if qty > product.stock_quantity:
        return Response(
            {'error': 'bad_request', 'detail': f'Only {product.stock_quantity} units available.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    service.add_item(request, product, qty)
    summary = service.get_basket_summary(request)
    return Response(summary, status=status.HTTP_200_OK)


# ── Update item ────────────────────────────────────────────────────────────────

@extend_schema(tags=['basket'])
@api_view(['PUT'])
@permission_classes([AllowAny])
def basket_update(request, product_id):
    """
    Update the quantity of a basket item.
    Body: { "qty": 3 }
    Set qty to 0 to remove the item.
    """
    qty = request.data.get('qty')
    try:
        qty = int(qty)
        if qty < 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            {'error': 'bad_request', 'detail': 'qty must be a non-negative integer.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Stock check when increasing
    if qty > 0:
        try:
            product = Product.active.get(id=product_id)
            if qty > product.stock_quantity:
                return Response(
                    {'error': 'bad_request', 'detail': f'Only {product.stock_quantity} units available.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Product.DoesNotExist:
            return Response(
                {'error': 'not_found', 'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    service.update_item(request, product_id, qty)
    summary = service.get_basket_summary(request)
    return Response(summary)


# ── Remove item ────────────────────────────────────────────────────────────────

@extend_schema(tags=['basket'])
@api_view(['DELETE'])
@permission_classes([AllowAny])
def basket_remove(request, product_id):
    """Remove a single item from the basket."""
    service.remove_item(request, product_id)
    summary = service.get_basket_summary(request)
    return Response(summary)


# ── Merge (called after login) ─────────────────────────────────────────────────

@extend_schema(tags=['basket'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def basket_merge(request):
    """
    Merge the anonymous session basket into the now-authenticated user basket.
    Call this immediately after a successful login from the front-end.
    """
    service.merge_baskets(request, request.user.id)
    summary = service.get_basket_summary(request)
    return Response(summary)
