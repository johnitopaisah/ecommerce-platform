from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('create-intent/', views.create_payment_intent, name='create_intent'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('<str:order_number>/', views.payment_status, name='payment_status'),
]
