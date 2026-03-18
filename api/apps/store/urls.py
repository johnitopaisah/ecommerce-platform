from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),

    # Products
    path('', views.product_list, name='product_list'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.products_by_category, name='products_by_category'),
]
