"""
Redis-backed basket service.

Basket data is stored in Redis under one of two key patterns:
  - Authenticated user:  basket:user:<user_id>
  - Anonymous session:   basket:session:<session_key>

Structure stored per key:
  {
    "<product_id>": {"price": "19.99", "qty": 2},
    ...
  }

On login, any existing anonymous basket is merged into the user basket.
"""

import json
from decimal import Decimal

from django.conf import settings
from django_redis import get_redis_connection

BASKET_TTL = 60 * 60 * 24 * 30  # 30 days


def _get_redis():
    return get_redis_connection('default')


def _basket_key(request):
    """Derive the Redis key for this request's basket."""
    if request.user.is_authenticated:
        return f'basket:user:{request.user.id}'
    # Ensure the session exists so session_key is never None
    if not request.session.session_key:
        request.session.create()
    return f'basket:session:{request.session.session_key}'


def _coupon_key(request):
    """Same scoping as the basket key — a coupon lives alongside its basket."""
    if request.user.is_authenticated:
        return f'coupon:user:{request.user.id}'
    if not request.session.session_key:
        request.session.create()
    return f'coupon:session:{request.session.session_key}'


def _load(key: str) -> dict:
    redis = _get_redis()
    raw = redis.get(key)
    if raw:
        return json.loads(raw)
    return {}


def _save(key: str, data: dict):
    redis = _get_redis()
    redis.set(key, json.dumps(data), ex=BASKET_TTL)


def _delete(key: str):
    _get_redis().delete(key)


# ── Public API used by views ───────────────────────────────────────────────────

def get_basket(request) -> dict:
    """Return the raw basket dict {product_id: {price, qty}}."""
    return _load(_basket_key(request))


def add_item(request, product, qty: int) -> dict:
    """Add or update a product in the basket. Returns updated basket."""
    key = _basket_key(request)
    basket = _load(key)
    product_id = str(product.id)

    if product_id in basket:
        basket[product_id]['qty'] = qty
    else:
        basket[product_id] = {
            'price': str(product.effective_price),
            'qty': qty,
        }

    _save(key, basket)
    return basket


def update_item(request, product_id: int, qty: int) -> dict:
    """Update the quantity of an existing item. Returns updated basket."""
    key = _basket_key(request)
    basket = _load(key)
    pid = str(product_id)

    if pid in basket:
        if qty <= 0:
            del basket[pid]
        else:
            basket[pid]['qty'] = qty
        _save(key, basket)

    return basket


def remove_item(request, product_id: int) -> dict:
    """Remove an item from the basket. Returns updated basket."""
    key = _basket_key(request)
    basket = _load(key)
    pid = str(product_id)

    if pid in basket:
        del basket[pid]
        _save(key, basket)

    return basket


def clear_basket(request):
    """Delete the entire basket (and any applied coupon — it belongs to this basket)."""
    _delete(_basket_key(request))
    _delete(_coupon_key(request))


def set_coupon(request, code: str):
    _get_redis().set(_coupon_key(request), code, ex=BASKET_TTL)


def get_coupon_code(request) -> str | None:
    raw = _get_redis().get(_coupon_key(request))
    return raw.decode() if raw else None


def clear_coupon(request):
    _delete(_coupon_key(request))


def merge_baskets(request, user_id: int):
    """
    Merge an anonymous session basket into the authenticated user's basket.
    Called at login time from the front-end by hitting POST /api/v1/basket/merge/.
    Items in the user basket take precedence (qty not overwritten if product exists).
    """
    if not request.session.session_key:
        return

    session_key = f'basket:session:{request.session.session_key}'
    user_key = f'basket:user:{user_id}'

    session_basket = _load(session_key)
    if not session_basket:
        return

    user_basket = _load(user_key)

    for product_id, item in session_basket.items():
        if product_id not in user_basket:
            user_basket[product_id] = item

    _save(user_key, user_basket)
    _delete(session_key)


def get_basket_summary(request) -> dict:
    """
    Return a basket summary with full product data hydrated from the DB.
    Expensive (DB query) — used only for the basket detail view.

    Discount is recomputed fresh from the live coupon + subtotal on every
    call — never trusted from anywhere else — so an applied coupon that
    expires, gets deactivated, or hits its usage limit between "apply" and
    checkout is caught here rather than silently over- or under-charging.
    """
    from apps.store.models import Product  # local import to avoid circular

    basket = _load(_basket_key(request))
    if not basket:
        return {
            'items': [], 'total_items': 0, 'subtotal': '0.00',
            'coupon_code': None, 'coupon_error': None,
            'discount_amount': '0.00', 'total': '0.00',
        }

    product_ids = [int(pid) for pid in basket.keys()]
    products = {
        str(p.id): p
        for p in Product.active.filter(id__in=product_ids)
    }

    items = []
    subtotal = Decimal('0.00')

    for product_id, item_data in basket.items():
        product = products.get(product_id)
        if not product:
            # Product was removed or deactivated — skip silently
            continue

        qty = item_data['qty']
        price = Decimal(item_data['price'])
        line_total = price * qty
        subtotal += line_total

        items.append({
            'product_id': int(product_id),
            'title': product.title,
            'slug': product.slug,
            'image': product.image.url if product.image else None,
            'price': str(price),
            'qty': qty,
            'line_total': str(line_total),
            'stock_quantity': product.stock_quantity,
        })

    coupon_code = get_coupon_code(request)
    applied_code = None
    coupon_error = None
    discount_amount = Decimal('0.00')

    if coupon_code:
        from apps.coupons.models import Coupon  # local import to avoid circular
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            valid, error = coupon.is_valid(subtotal)
            if valid:
                applied_code = coupon.code
                discount_amount = coupon.calculate_discount(subtotal)
            else:
                coupon_error = error
        except Coupon.DoesNotExist:
            coupon_error = 'Coupon not found.'

    return {
        'items': items,
        'total_items': sum(i['qty'] for i in items),
        'subtotal': str(subtotal),
        'coupon_code': applied_code,
        'coupon_error': coupon_error,
        'discount_amount': str(discount_amount),
        'total': str(subtotal - discount_amount),
    }
