from django.contrib import admin
from .models import PaymentTransaction, PaymentProviderConfig

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'provider', 'phone_number', 'amount', 'status', 'created_at']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['transaction_id', 'phone_number', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20

@admin.register(PaymentProviderConfig)
class PaymentProviderConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'is_active', 'yo_username', 'base_url']
    list_editable = ['is_active']
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('provider', 'is_active', 'base_url', 'callback_url')
        }),
        ('Yo! Payments Configuration', {
            'fields': ('yo_username', 'yo_password'),
            'classes': ('collapse',)
        }),
        ('MTN Configuration', {
            'fields': ('api_key', 'api_secret', 'merchant_id'),
            'classes': ('collapse',)
        }),
        ('Airtel Configuration', {
            'fields': (),
            'classes': ('collapse',)
        }),
    )