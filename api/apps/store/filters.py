"""
Store filters — allows query-param filtering on the product list endpoint.

Usage examples:
  /api/v1/products/?category=electronics
  /api/v1/products/?min_price=10&max_price=500
  /api/v1/products/?in_stock=true
  /api/v1/products/?search=laptop
  /api/v1/products/?ordering=-price
"""

import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact',
        label='Category slug',
    )
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum price',
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum price',
    )
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='In stock only',
    )

    class Meta:
        model = Product
        fields = ('category', 'min_price', 'max_price', 'in_stock')

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)
