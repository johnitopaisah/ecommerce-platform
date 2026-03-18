"""
Payment views.

POST  /api/v1/payment/create-intent/   create Stripe PaymentIntent, returns client_secret
POST  /api/v1/payment/webhook/         Stripe webhook (CSRF exempt)
GET   /api/v1/payment/<order_number>/  payment status for an order
"""

import json
import logging

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.basket import service as basket_service
from apps.orders.models import Order
from apps.orders.views import confirm_payment
from .models import Payment

logger = logging.getLogger(__name__)


# ── Create PaymentIntent ───────────────────────────────────────────────────────

@extend_schema(tags=['payment'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """
    Create a Stripe PaymentIntent for the current basket total.
    Returns the client_secret needed by Stripe.js on the front-end.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    basket_summary = basket_service.get_basket_summary(request)
    if not basket_summary['items']:
        return Response(
            {'error': 'bad_request', 'detail': 'Your basket is empty.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Stripe expects the amount in the smallest currency unit (pence for GBP)
    from decimal import Decimal
    subtotal = Decimal(basket_summary['subtotal'])
    amount_pence = int(subtotal * 100)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_pence,
            currency='gbp',
            metadata={'user_id': request.user.id},
        )
    except stripe.error.StripeError as exc:
        logger.error('Stripe PaymentIntent creation failed: %s', exc)
        return Response(
            {'error': 'payment_error', 'detail': str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({
        'client_secret': intent.client_secret,
        'payment_intent_id': intent.id,
        'amount': basket_summary['subtotal'],
        'currency': 'gbp',
    })


# ── Stripe Webhook ─────────────────────────────────────────────────────────────

@csrf_exempt
def stripe_webhook(request):
    """
    Handles Stripe webhook events.
    CSRF exempt — Stripe signs the payload instead.
    This is a plain Django view (not DRF) so we can return raw HttpResponse.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError:
        logger.warning('Stripe webhook: invalid payload')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning('Stripe webhook: invalid signature')
        return HttpResponse(status=400)

    # ── Handle events ──────────────────────────────────────────────────────────
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        _handle_payment_succeeded(intent)

    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        _handle_payment_failed(intent)

    else:
        logger.debug('Stripe webhook: unhandled event type %s', event['type'])

    return HttpResponse(status=200)


def _handle_payment_succeeded(intent):
    """Mark order as paid and record the payment."""
    order_key = intent['client_secret']
    payment_intent_id = intent['id']
    amount_pence = intent['amount']

    # Idempotency: skip if already processed
    if Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).exists():
        logger.info('Webhook: payment %s already processed — skipping', payment_intent_id)
        return

    confirmed = confirm_payment(order_key)
    if not confirmed:
        logger.error('Webhook: no order found for order_key %s', order_key)
        return

    try:
        order = Order.objects.get(order_key=order_key)
        from decimal import Decimal
        Payment.objects.create(
            order=order,
            stripe_payment_intent_id=payment_intent_id,
            amount=Decimal(amount_pence) / 100,
            currency=intent.get('currency', 'gbp'),
            status=Payment.PaymentStatus.SUCCEEDED,
        )
        logger.info('Webhook: order %s confirmed, payment recorded', order.order_number)
    except Order.DoesNotExist:
        logger.error('Webhook: order with key %s not found after confirm', order_key)


def _handle_payment_failed(intent):
    """Record a failed payment attempt."""
    payment_intent_id = intent['id']
    order_key = intent['client_secret']

    try:
        order = Order.objects.get(order_key=order_key)
        from decimal import Decimal
        Payment.objects.get_or_create(
            stripe_payment_intent_id=payment_intent_id,
            defaults={
                'order': order,
                'amount': Decimal(intent['amount']) / 100,
                'currency': intent.get('currency', 'gbp'),
                'status': Payment.PaymentStatus.FAILED,
            }
        )
        logger.info('Webhook: payment failed for order %s', order.order_number)
    except Order.DoesNotExist:
        logger.error('Webhook: no order found for failed payment key %s', order_key)


# ── Payment status ─────────────────────────────────────────────────────────────

@extend_schema(tags=['payment'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, order_number):
    """Return the payment record(s) for a given order."""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'not_found', 'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    payments = Payment.objects.filter(order=order).order_by('-created')
    data = [
        {
            'payment_intent_id': p.stripe_payment_intent_id,
            'amount': str(p.amount),
            'currency': p.currency,
            'status': p.status,
            'created': p.created,
        }
        for p in payments
    ]
    return Response({
        'order_number': order.order_number,
        'billing_status': order.billing_status,
        'payments': data,
    })
