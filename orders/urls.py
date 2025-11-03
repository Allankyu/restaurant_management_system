from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Online ordering URLs - place these BEFORE any catch-all patterns
    path('online/', views.online_order, name='online_order'),
    path('online/submit/', views.submit_online_order, name='submit_online_order'),
    path('online/success/<int:order_id>/', views.online_order_success, name='online_order_success'),
    path('', views.order_list, name='order_list'),
    
    path('create/', views.order_create, name='order_create'),
    path('create-customer-ajax/', views.create_customer_ajax, name='create_customer_ajax'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/update-status/', views.order_update_status, name='order_update_status'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('<int:pk>/print-receipt/', views.print_receipt, name='print_receipt'),
    path('<int:pk>/view-receipt/', views.view_receipt, name='view_receipt'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),

     # Order management URLs
    path('management/', views.order_management, name='order_management'),
    path('management/<int:order_id>/', views.order_detail_management, name='order_detail_management'),
    path('management/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
]