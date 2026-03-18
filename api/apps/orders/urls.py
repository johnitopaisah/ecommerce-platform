from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list_create, name='order_list_create'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
    path('<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),
]
