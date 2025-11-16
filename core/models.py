from django.db import models
from django.db.models import F  # Add this import
from django.utils import timezone  # Add this import
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    logo = models.ImageField(upload_to='restaurant/', null=True, blank=True)
    
    def __str__(self):
        return self.name

# ADD BRANCH MODEL HERE
class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_branches')
    
    def __str__(self):
        return self.name
    
    def get_low_stock_count(self):
        """Get count of low stock items for this branch"""
        try:
            from inventory.models import Stock
            # Check if Stock model has branch field
            if hasattr(Stock, 'branch'):
                return Stock.objects.filter(
                    branch=self,
                    quantity__lte=F('alert_level')  # Changed from 'minimum_stock' to 'alert_level'
                ).count()
            else:
                # If no branch field, return all low stock items
                return Stock.objects.filter(
                    quantity__lte=F('alert_level')  # Changed from 'minimum_stock' to 'alert_level'
                ).count()
        except Exception as e:  # Fixed the exception syntax
            print(f"Error in get_low_stock_count: {e}")
            return 0
    
    def get_reservations_today(self):
        """Get today's reservations count for this branch"""
        try:
            from reservations.models import Reservation
            today = timezone.now().date()
            return Reservation.objects.filter(
                branch=self,
                reservation_date=today
            ).count()
        except ImportError:
            return 0
class Employee(models.Model):
    EMPLOYEE_TYPES = [
        ('manager', 'Manager'),
        ('chef', 'Chef'),
        ('waiter', 'Waiter'),
        ('cashier', 'Cashier'),
        ('cleaner', 'Cleaner'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPES)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    hire_date = models.DateField(auto_now_add=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['branch', 'employee_type', 'user__first_name']
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else 'No Branch'
        return f"{self.user.get_full_name()} - {self.employee_type} - {branch_name}"
    
    @property
    def can_manage_branch(self):
        """Check if employee can manage their branch"""
        return self.employee_type == 'manager' and self.branch is not None
    
    def get_employee_type_display(self):
        """Get human-readable employee type"""
        return dict(self.EMPLOYEE_TYPES).get(self.employee_type, self.employee_type)
    
    def is_manager_of_branch(self, branch=None):
        """Check if this employee is manager of given branch (or any branch)"""
        if self.employee_type != 'manager':
            return False
        if branch:
            return self.branch == branch
        return self.branch is not None
class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    preferred_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def orders_count(self):
        return self.order_set.count()
    
    orders_count.short_description = 'Total Orders'



