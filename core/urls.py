from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
     # Root URL - redirect based on authentication
    path('', views.root_redirect, name='root_redirect'),
    
    # Public home page
    path('home/', views.home, name='home'),
     # Management dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    path('branches/', views.branch_list, name='branch_list'),
    path('branches/<int:pk>/', views.branch_detail, name='branch_detail'),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branch/<int:branch_id>/', views.branch_dashboard, name='branch_dashboard'),
    
     # Employee Management URLs
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/toggle/', views.employee_toggle, name='employee_toggle'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('branches/<int:branch_id>/admin-dashboard/', views.admin_branch_dashboard, name='admin_branch_dashboard'),
]



