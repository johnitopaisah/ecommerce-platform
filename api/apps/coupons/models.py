"""
Coupon model — admin-managed discount codes applied at checkout.

Discount is computed fresh from the live basket subtotal on every request
that needs it (basket summary, PaymentIntent creation, order creation) —
never trusted from the client — so a coupon deactivated or expired mid-
checkout is caught before the customer is charged.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED = 'fixed', _('Fixed amount')

    code = models.CharField(max_length=32, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Percentage (0-100) or a fixed £ amount, depending on discount type.'),
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_('Minimum basket subtotal required to use this coupon.'),
    )
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text=_('Leave blank for unlimited redemptions.'),
    )
    times_used = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def is_valid(self, subtotal: Decimal) -> tuple[bool, str]:
        """Returns (valid, error_message). error_message is '' when valid."""
        if not self.is_active:
            return False, 'This coupon is no longer active.'
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False, 'This coupon is not active yet.'
        if self.valid_until and now > self.valid_until:
            return False, 'This coupon has expired.'
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False, 'This coupon has reached its usage limit.'
        if self.min_order_value and subtotal < self.min_order_value:
            return False, f'This coupon requires a minimum order of £{self.min_order_value}.'
        return True, ''

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """Discount amount for the given subtotal — never exceeds the subtotal itself."""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = subtotal * (self.discount_value / Decimal('100'))
        else:
            discount = self.discount_value
        return min(discount, subtotal).quantize(Decimal('0.01'))
