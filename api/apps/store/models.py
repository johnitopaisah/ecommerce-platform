"""
Store models — Category and Product.

Changes from the original monolith:
- Removed `author` field (blog leftover, irrelevant for e-commerce)
- Added `stock_quantity` (integer) — replaces the binary `in_stock` bool
  in_stock is now a computed property: stock_quantity > 0
- Added `ProductImage` model (multiple images per product)
- `created_by` FK kept — tracks which admin/staff created the product
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ('name',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ActiveProductManager(models.Manager):
    """Returns only active, in-stock products."""
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_active=True, stock_quantity__gt=0)
        )


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='products',
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_('Optional sale price. If set, shown instead of regular price.')
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text=_('Set to 0 to mark as out of stock.')
    )

    # Main image (kept for backwards compat — additional images via ProductImage)
    image = models.ImageField(upload_to='products/', default='products/default.png')

    # Flags
    is_active = models.BooleanField(default=True)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()           # all products (used in admin)
    active = ActiveProductManager()      # active + in-stock only (used in public API)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ('-created',)
        permissions = [
            ('manage_inventory', 'Can update stock levels only'),
            ('manage_pricing', 'Can update prices only'),
        ]

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def effective_price(self):
        """Return discount_price if set, otherwise regular price."""
        return self.discount_price if self.discount_price else self.price

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Additional images for a product (one-to-many)."""
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text=_('If True, this image is used as the main product image.')
    )
    ordering = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ('ordering', 'created')

    def __str__(self):
        return f'{self.product.title} — image {self.id}'


class Review(models.Model):
    """
    A customer review of a product. One review per user per product.
    Held for admin approval before appearing publicly — the public list/
    aggregate endpoints only ever see is_approved=True rows.
    """
    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='reviews',
        on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
    )
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField(blank=True)

    # Set once at creation time from the user's order history — not
    # recomputed later, so it reflects "had they purchased it at the time".
    verified_purchase = models.BooleanField(default=False)

    is_approved = models.BooleanField(default=False, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ('-created',)
        permissions = [
            ('moderate_reviews', 'Can approve, reject, or delete reviews'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='one_review_per_user_per_product'),
        ]

    def __str__(self):
        return f'{self.product.title} — {self.rating}★ by {self.user}'


class WishlistItem(models.Model):
    """A product a user has saved for later. No anonymous support — sign in required."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='wishlist_items',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='wishlisted_by',
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='one_wishlist_entry_per_user_per_product'),
        ]

    def __str__(self):
        return f'{self.user} ♥ {self.product.title}'
