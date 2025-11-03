from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('financial/', views.financial_report, name='financial_report'),
    path('branch/<int:branch_id>/', views.branch_detailed_report, name='branch_detailed_report'),
    path('customer/', views.customer_report, name='customer_report'),
    path('generate/', views.generate_report, name='generate_report'),
]