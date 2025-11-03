from django.db import models
from django.core.validators import MinValueValidator
from core.models import Customer, Employee, Branch
from inventory.models import MenuItem

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid'),
    ]
    
    ORDER_TYPES = [
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    table_number = models.PositiveIntegerField(null=True, blank=True)
    waiter = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    delivery_address = models.TextField(blank=True, null=True)
    # Add these fields for notifications
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            last_id = last_order.id if last_order else 0
            self.order_number = f"ORD{last_id + 1:06d}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        return sum(item.subtotal for item in self.order_items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    is_custom_combo = models.BooleanField(default=False)
    custom_base_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='custom_base_orders',
        limit_choices_to={'item_type': 'base'}
    )
    custom_protein_source = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custom_source_orders',
        limit_choices_to={'item_type': 'source'}
    )
    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    @property
    def display_name(self):
        if self.is_custom_combo and self.custom_base_item and self.custom_protein_source:
            return f"{self.custom_base_item.name} with {self.custom_protein_source.name}"
        elif self.notes:  # Use custom name from notes if available
            return self.notes
        return self.menu_item.display_name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.total_amount = self.order.calculate_total()
        self.order.save()

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit Card'),
        ('digital', 'Digital Payment'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Payment for {self.order}"