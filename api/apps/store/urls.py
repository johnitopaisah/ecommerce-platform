from django.urls import path
from . import views, admin_views

app_name = 'store'

urlpatterns = [
    # Public
    path('', views.product_list, name='product_list'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]

# Category and admin urls are registered directly in config/urls.py
# to keep prefixes clean — see config/urls.py
