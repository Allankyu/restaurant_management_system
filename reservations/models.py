from django.db import models
from core.models import Customer, Branch

class Table(models.Model):
    TABLE_TYPES = [
        ('2_seater', '2 Seater'),
        ('4_seater', '4 Seater'),
        ('6_seater', '6 Seater'),
        ('family', 'Family (8+)'),
    ]
    
    table_number = models.CharField(max_length=10, unique=True)
    table_type = models.CharField(max_length=20, choices=TABLE_TYPES)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    location_description = models.CharField(max_length=100, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Table {self.table_number}"
    
    class Meta:
        ordering = ['table_number']

class Reservation(models.Model):
    RESERVATION_STATUS = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=120)
    number_of_guests = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='pending')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Reservation for {self.customer.name} on {self.reservation_date}"
    
    class Meta:
        ordering = ['-reservation_date', '-reservation_time']
    
    @property
    def end_time(self):
        """Calculate reservation end time based on duration"""
        from datetime import timedelta
        from django.utils import timezone
        
        # Create a datetime object for the reservation
        reservation_datetime = timezone.make_aware(
            timezone.datetime.combine(self.reservation_date, self.reservation_time)
        )
        end_datetime = reservation_datetime + timedelta(minutes=self.duration)
        return end_datetime.time()



