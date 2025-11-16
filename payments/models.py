from django.db import models
from django.contrib.auth.models import User
from orders.models import Order

class PaymentTransaction(models.Model):
    PAYMENT_PROVIDERS = [
        ('yo', 'Yo! Payments'),
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=10, choices=PAYMENT_PROVIDERS)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='initiated')
    provider_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    yo_transaction_status = models.CharField(max_length=50, blank=True, null=True)  # For Yo! status tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider} - UGX {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-populate phone number from order if not provided
        if not self.phone_number and self.order.customer_phone:
            self.phone_number = self.order.customer_phone
        super().save(*args, **kwargs)

class PaymentProviderConfig(models.Model):
    provider = models.CharField(max_length=10, choices=PaymentTransaction.PAYMENT_PROVIDERS)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.URLField(blank=True, null=True)
    callback_url = models.URLField(blank=True, null=True)
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Yo! Payments specific fields
    yo_username = models.CharField(max_length=100, blank=True, null=True)
    yo_password = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_provider_display()} Config"