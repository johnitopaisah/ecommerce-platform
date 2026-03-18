from django.urls import path
from . import views

app_name = 'basket'

urlpatterns = [
    path('', views.basket_detail, name='basket_detail'),
    path('items/', views.basket_add, name='basket_add'),
    path('items/<int:product_id>/', views.basket_update, name='basket_update'),
    path('items/<int:product_id>/remove/', views.basket_remove, name='basket_remove'),
    path('merge/', views.basket_merge, name='basket_merge'),
]
