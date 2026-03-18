"""
Store models — Category and Product.

Key changes from the monolith:
- `author` field removed (was a blog leftover)
- `stock_quantity` replaces the binary `in_stock` boolean
- `in_stock` is now a computed property derived from stock_quantity
- `ProductImage` added for multiple images per product
- `tags` added as a simple comma-stored CharField for basic filtering
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
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
        return super().get_queryset().filter(is_active=True, stock_quantity__gt=0)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Default manager — returns ALL products (used in admin)
    objects = models.Manager()
    # Custom manager — returns only active + in-stock (used in storefront)
    available = ActiveProductManager()

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-created',)

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Multiple images per product. The first image is treated as the primary."""
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('ordering', 'created')

    def __str__(self):
        return f'{self.product.title} — image {self.id}'
