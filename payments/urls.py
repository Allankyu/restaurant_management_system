from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('order/<int:order_id>/pay/', views.initiate_payment, name='initiate_payment'),
    path('status/<str:transaction_id>/', views.payment_status, name='payment_status'),
    path('webhook/<str:provider>/', views.payment_webhook, name='payment_webhook'),
    path('test/', views.payment_test, name='payment_test'),  # Add this line for testing
]
