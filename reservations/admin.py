from django.contrib import admin
from .models import Table, Reservation

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'table_type', 'capacity', 'is_available', 'location_description']
    list_filter = ['table_type', 'is_available']
    search_fields = ['table_number', 'location_description']
    list_editable = ['is_available']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'table', 'reservation_date', 'reservation_time', 'number_of_guests', 'status']
    list_filter = ['status', 'reservation_date', 'table']
    search_fields = ['customer__name', 'table__table_number']
    list_editable = ['status']
    date_hierarchy = 'reservation_date'



