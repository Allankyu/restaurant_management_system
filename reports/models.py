from django.db import models
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, Payment
from inventory.models import MenuItem

class DailySalesReport(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Sales Report - {self.date}"
    
    @classmethod
    def generate_daily_report(cls, date=None):
        if date is None:
            date = timezone.now().date()
        
        orders = Order.objects.filter(created_at__date=date, status='paid')
        payments = Payment.objects.filter(payment_date__date=date, is_successful=True)
        
        total_sales = payments.aggregate(total=Sum('amount'))['total'] or 0
        total_orders = orders.count()
        total_customers = orders.values('customer').distinct().count()
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        report, created = cls.objects.get_or_create(date=date)
        report.total_sales = total_sales
        report.total_orders = total_orders
        report.total_customers = total_customers
        report.average_order_value = average_order_value
        report.save()
        
        return report

class PopularMenuItem(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    date = models.DateField()
    quantity_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['menu_item', 'date']



