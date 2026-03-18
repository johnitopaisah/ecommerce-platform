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
