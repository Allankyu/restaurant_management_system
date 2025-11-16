from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    path('menu/', views.menu_list, name='menu_list'),
    
    # New menu item management routes with image upload
    path('menu/create/', views.menu_item_create, name='menu_item_create'),
    path('menu/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),
    
    path('stock/', views.stock_list, name='stock_list'),
    path('categories/', views.category_list, name='category_list'),
]



