# notifications/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class NotificationChannel(models.Model):
    CHANNEL_TYPES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ]
    
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)  # For API keys, templates, etc.
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"

class NotificationTemplate(models.Model):
    NOTIFICATION_TYPES = [
        ('welcome', 'Welcome'),
        ('reservation_confirm', 'Reservation Confirmation'),
        ('order_ready', 'Order Ready'),
        ('order_preparing', 'Order Preparing'),
        ('order_served', 'Order Served'),
        ('table_ready', 'Table Ready'),
        ('payment_confirm', 'Payment Confirmation'),
        ('low_stock_alert', 'Low Stock Alert'),
        ('system_alert', 'System Alert'),
    ]

    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, unique=True)
    subject_template = models.CharField(max_length=255)
    message_template = models.TextField()
    sms_template = models.TextField(blank=True, null=True)
    html_template = models.TextField(blank=True, null=True, help_text="HTML version for email notifications")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class NotificationLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]
    
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    recipient = models.CharField(max_length=255)  # Phone number or email
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    context_data = models.JSONField(default=dict)  # Store template context
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template.name} to {self.recipient}"



