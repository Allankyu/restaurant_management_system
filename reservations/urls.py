from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.reservation_dashboard, name='reservation_dashboard'),
    path('list/', views.reservation_list, name='reservation_list'),
    path('create/', views.reservation_create, name='reservation_create'),
    path('create-customer-ajax/', views.create_customer_ajax, name='create_customer_ajax'),
    path('check-availability/', views.check_table_availability, name='check_table_availability'),
    path('tables/', views.table_list, name='table_list'),
    path('tables/add/', views.table_add, name='table_add'),
    path('tables/<int:pk>/edit/', views.table_edit, name='table_edit'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),
    path('tables/<int:pk>/toggle/', views.table_toggle, name='table_toggle'),
]



