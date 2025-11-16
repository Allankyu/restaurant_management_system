# notifications/management/commands/setup_notifications.py
from django.core.management.base import BaseCommand
from notifications.models import NotificationChannel, NotificationTemplate

class Command(BaseCommand):
    help = 'Setup initial notification channels and templates'
    
    def handle(self, *args, **options):
        # Create notification channels
        email_channel, created = NotificationChannel.objects.get_or_create(
            name='Email Channel',
            channel_type='email',
            defaults={'config': {}}
        )
        
        sms_channel, created = NotificationChannel.objects.get_or_create(
            name='SMS Channel',
            channel_type='sms',
            defaults={'config': {}}
        )
        
        # Create notification templates
        templates_data = [
            {
                'name': 'Order Confirmation',
                'notification_type': 'order_confirmation',
                'subject_template': 'Order Confirmation - {{ order_number }}',
                'message_template': """Dear {{ customer_name }},

Thank you for your order! Your order #{{ order_number }} has been confirmed.

Total: Ugx {{ total_amount }}
Delivery Address: {{ delivery_address }}

Estimated delivery time: {{ estimated_time }}

We'll notify you when your order is out for delivery.

Thank you for choosing us!""",
                'sms_template': 'Order confirmed! #{{ order_number }}. Total: Ugx {{ total_amount }}. Delivery in {{ estimated_time }}.'
            },
            {
                'name': 'Order Status Update',
                'notification_type': 'order_status_update',
                'subject_template': 'Order Update - {{ order_number }}',
                'message_template': """Dear {{ customer_name }},

Your order #{{ order_number }} is now {{ status }}.

We'll let you know when it's ready for delivery.

Thank you for your patience!""",
                'sms_template': 'Order #{{ order_number }} is now {{ status }}.'
            },
            {
                'name': 'New Order Alert',
                'notification_type': 'new_order_alert',
                'subject_template': 'New Online Order - {{ order_number }}',
                'message_template': """New online order received!

Order #: {{ order_number }}
Customer: {{ customer_name }}
Total: Ugx {{ total_amount }}
Items: {{ item_count }}
Delivery: {{ delivery_address }}

Please prepare the order.""",
                'sms_template': 'New order #{{ order_number }} from {{ customer_name }}. Total: Ugx {{ total_amount }}.'
            }
        ]
        
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                notification_type=template_data['notification_type'],
                defaults=template_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup notification system!')
        )



