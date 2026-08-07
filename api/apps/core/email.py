"""
Centralised email sending service.

All application emails go through this module so:
- Templates live in one place (templates/emails/)
- Plain-text fallback is always included
- Context is consistent across all emails
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send(subject: str, to_email: str, template: str, context: dict):
    """
    Internal helper — renders an HTML template, generates a plain-text
    fallback, and sends the email via whatever backend is configured.
    """
    # Always inject the frontend URL so templates can build links
    context.setdefault('frontend_url', settings.FRONTEND_URL)

    try:
        html_content = render_to_string(f'emails/{template}.html', context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info('Email sent: %s → %s', subject, to_email)
    except Exception as exc:
        # Never let an email failure crash the request
        logger.error('Email send failed: %s → %s | %s', subject, to_email, exc)


# ── Public API ─────────────────────────────────────────────────────────────────

def send_activation_email(user, activation_url: str):
    """Send the email-activation link after registration."""
    _send(
        subject='Activate your ShopNow account',
        to_email=user.email,
        template='activation',
        context={
            'user': user,
            'activation_url': activation_url,
        },
    )


def send_password_reset_email(user, reset_url: str):
    """Send the password-reset link."""
    _send(
        subject='Reset your ShopNow password',
        to_email=user.email,
        template='password_reset',
        context={
            'user': user,
            'reset_url': reset_url,
        },
    )


def send_order_confirmation_email(order):
    """Send an order confirmation to the customer."""
    _send(
        subject=f'Order confirmed — #{order.order_number}',
        to_email=order.email,
        template='order_confirmation',
        context={
            'order': order,
        },
    )


# Status -> (headline, message) shown in the tracking email. Statuses not
# listed here (e.g. PENDING, CONFIRMED — already covered by the order
# confirmation email) don't trigger a separate notification.
_STATUS_COPY = {
    'processing': (
        "We're getting your order ready",
        "your order is now being prepared for shipment.",
    ),
    'shipped': (
        'Your order is on its way!',
        'your order has shipped and is on its way to you.',
    ),
    'delivered': (
        'Your order has been delivered',
        'your order has been marked as delivered. We hope you love it!',
    ),
    'cancelled': (
        'Your order has been cancelled',
        'your order has been cancelled. If this is unexpected, please get in touch.',
    ),
    'refunded': (
        'Your refund has been processed',
        'your order has been refunded.',
    ),
}


def send_order_status_update_email(order):
    """
    Notify the customer their order moved to a new tracking-relevant status.
    Call only when the status actually changed — see _STATUS_COPY for which
    statuses trigger an email.
    """
    copy = _STATUS_COPY.get(order.status)
    if not copy:
        return
    headline, message = copy
    _send(
        subject=f'Order #{order.order_number} — {order.get_status_display()}',
        to_email=order.email,
        template='order_status_update',
        context={
            'order': order,
            'headline': headline,
            'message': message,
        },
    )
