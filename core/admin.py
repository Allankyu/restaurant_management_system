from django.contrib import admin
from .models import Restaurant, Employee, Customer
from import_export.admin import ImportExportModelAdmin

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'opening_time', 'closing_time']

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    list_display = ['employee_id', 'user', 'employee_type', 'phone', 'hire_date', 'is_active']
    list_filter = ['employee_type', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']