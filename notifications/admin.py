# notifications/admin.py
from django.contrib import admin
from .models import NotificationChannel, NotificationTemplate, NotificationLog

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_active']
    list_filter = ['channel_type', 'is_active']
    list_editable = ['is_active']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active']
    list_filter = ['notification_type', 'is_active']
    list_editable = ['is_active']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['template', 'channel', 'recipient', 'status', 'created_at']
    list_filter = ['status', 'channel', 'template', 'created_at']
    readonly_fields = ['created_at', 'sent_at']
    search_fields = ['recipient', 'subject']