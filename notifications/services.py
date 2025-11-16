# restaurant_management/notifications/services.py
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Template, Context
from django.template.loader import render_to_string
from .models import NotificationChannel, NotificationTemplate, NotificationLog
import requests
import json
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.email_channel = NotificationChannel.objects.filter(
            channel_type='email', is_active=True
        ).first()
        self.sms_channel = NotificationChannel.objects.filter(
            channel_type='sms', is_active=True
        ).first()
        
        # Debug logging
        if self.sms_channel:
            logger.info(f"SMS Channel loaded: {self.sms_channel.name}")
            logger.info(f"SMS Config username: {self.sms_channel.config.get('username', 'NOT SET')}")
        if self.email_channel:
            logger.info(f"Email Channel loaded: {self.email_channel.name}")
        else:
            logger.warning("No active email channel found")
    
    def send_notification(self, notification_type, recipient, context_data):
        """Main method to send notifications"""
        try:
            template = NotificationTemplate.objects.get(
                notification_type=notification_type, 
                is_active=True
            )
            
            notifications_sent = []
            
            # Send Email
            if self.email_channel and recipient.get('email'):
                email_log = self._send_email(template, recipient['email'], context_data)
                notifications_sent.append(email_log)
            
            # Send SMS
            if self.sms_channel and recipient.get('phone'):
                sms_log = self._send_sms(template, recipient['phone'], context_data)
                notifications_sent.append(sms_log)
            
            return notifications_sent
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template not found for type: {notification_type}")
            return []
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return []
    
    def _send_email(self, template, email, context_data):
        """Send email notification with enhanced features"""
        try:
            # Render templates with context
            subject_template = Template(template.subject_template)
            message_template = Template(template.message_template)
            
            context = Context(context_data)
            subject = subject_template.render(context)
            plain_message = message_template.render(context)
            
            # Enhanced: Try to render HTML template if it exists
            html_message = None
            if template.html_template:
                try:
                    html_template = Template(template.html_template)
                    html_message = html_template.render(context)
                except Exception as html_error:
                    logger.warning(f"HTML template rendering failed: {html_error}")
                    html_message = None
            
            # Enhanced: Send email with HTML support
            if html_message:
                # Send both plain text and HTML versions
                email_msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                    reply_to=[getattr(settings, 'DEFAULT_REPLY_TO', settings.DEFAULT_FROM_EMAIL)]
                )
                email_msg.attach_alternative(html_message, "text/html")
                email_msg.send()
                print(f"📧 HTML Email sent to: {email}")
            else:
                # Send plain text only
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                print(f"📧 Plain Email sent to: {email}")
            
            # Log successful email
            log = NotificationLog.objects.create(
                template=template,
                channel=self.email_channel,
                recipient=email,
                subject=subject,
                message=plain_message,
                status='sent',
                context_data=context_data
            )
            logger.info(f"Email sent successfully to {email}")
            return log
            
        except Exception as e:
            # Log failed email
            error_msg = str(e)
            log = NotificationLog.objects.create(
                template=template,
                channel=self.email_channel,
                recipient=email,
                subject='',
                message='',
                status='failed',
                error_message=error_msg,
                context_data=context_data
            )
            logger.error(f"Email sending failed to {email}: {error_msg}")
            print(f"❌ Email failed to {email}: {error_msg}")
            return log
    
    def _send_sms(self, template, phone, context_data):
        """Send SMS notification - tries Africa's Talking first, falls back to simulator"""
        
        print("🚨 _send_sms METHOD IS BEING EXECUTED!")
        
        try:
            # Check if SMS channel is configured
            if not self.sms_channel:
                raise Exception("SMS channel not configured")
            
            # Get credentials from database configuration
            api_key = self.sms_channel.config.get('api_key')
            username = self.sms_channel.config.get('username')
            
            # Validate credentials
            if not api_key:
                raise Exception("API Key not found in SMS channel configuration")
            if not username:
                raise Exception("Username not found in SMS channel configuration")
            
            # Render SMS template
            sms_template = Template(template.sms_template or template.message_template)
            context = Context(context_data)
            message = sms_template.render(context)
            
            # Clean phone number
            phone = self._clean_phone_number(phone)
            
            # First, try to send via Africa's Talking with HTTPS
            try:
                print("🔄 Attempting to send via Africa's Talking HTTPS...")
                return self._send_sms_africastalking(template, phone, message, context_data)
                
            except Exception as africa_error:
                print(f"❌ Africa's Talking failed: {africa_error}")
                print("🔄 Falling back to local SMS simulator...")
                return self._send_sms_simulator(template, phone, message, context_data)
                
        except Exception as e:
            print(f"🚨 Exception caught in _send_sms: {type(e).__name__}: {e}")
            
            # Log failed SMS
            log = NotificationLog.objects.create(
                template=template,
                channel=self.sms_channel,
                recipient=phone,
                subject='SMS',
                message=message if 'message' in locals() else '',
                status='failed',
                error_message=str(e),
                context_data=context_data
            )
            logger.error(f"SMS sending failed to {phone}: {str(e)}")
            return log
    
    def _send_sms_africastalking(self, template, phone, message, context_data):
        """Actual Africa's Talking API call"""
        api_key = self.sms_channel.config.get('api_key')
        username = self.sms_channel.config.get('username')
        
        headers = {
            'ApiKey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        data = {
            'username': username,
            'to': phone,
            'message': message,
        }
        
        sender_id = self.sms_channel.config.get('sender_id')
        if sender_id:
            data['from'] = sender_id
        
        # Use HTTPS (the proper way)
        api_url = 'https://api.sandbox.africastalking.com/version1/messaging'
        if self.sms_channel.config.get('environment') == 'production':
            api_url = 'https://api.africastalking.com/version1/messaging'
        
        print(f"🔗 Using URL: {api_url}")
        
        response = requests.post(api_url, headers=headers, data=data, timeout=30, verify=False)
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"✅ SMS sent successfully via Africa's Talking: {response_data}")
            
            log = NotificationLog.objects.create(
                template=template,
                channel=self.sms_channel,
                recipient=phone,
                subject='SMS',
                message=message,
                status='sent',
                context_data=context_data
            )
            return log
        else:
            error_msg = f"SMS API error {response.status_code}: {response.text}"
            raise Exception(error_msg)
    
    def _send_sms_simulator(self, template, phone, message, context_data):
        """Local SMS simulator for development when Africa's Talking is unavailable"""
        print("=" * 60)
        print("📱 LOCAL SMS SIMULATOR ACTIVATED")
        print("=" * 60)
        print(f"📞 To: {phone}")
        print(f"💬 Message: {message}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"�️ Restaurant: {context_data.get('restaurant', 'Unknown')}")
        print(f"👤 Customer: {context_data.get('user_name', 'Unknown')}")
        print("=" * 60)
        
        # Simulate different scenarios
        scenarios = [
            "✅ SMS delivered successfully",
            "✅ Message queued for delivery", 
            "✅ SMS sent to provider",
            "✅ Notification processed"
        ]
        
        simulated_status = random.choice(scenarios)
        print(f"📊 Status: {simulated_status}")
        
        # Simulate a realistic Africa's Talking response
        simulated_response = {
            "SMSMessageData": {
                "Message": f"Sent to 1/1. {simulated_status}",
                "Recipients": [
                    {
                        "statusCode": 101,
                        "number": phone,
                        "status": "Success",
                        "cost": "UGX 0.0000",
                        "messageId": f"ATX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
                    }
                ]
            }
        }
        
        print(f"📨 Simulated Response: {simulated_response}")
        print("=" * 60)
        
        # Log as sent (but mark as simulated)
        log = NotificationLog.objects.create(
            template=template,
            channel=self.sms_channel,
            recipient=phone,
            subject='SMS [SIMULATED]',
            message=message,
            status='sent',
            error_message=f'SIMULATED - {simulated_status}. Real SMS would be sent via Africa\'s Talking',
            context_data=context_data
        )
        
        print(f"📝 Log entry created: {log.id}")
        print("🎉 Development can continue! Real SMS will work when network issue is resolved.")
        
        return log
    
    def _clean_phone_number(self, phone):
        """Clean and format phone number for Africa's Talking"""
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(phone)))
        
        # Add country code if missing (uganda)
        if not cleaned.startswith('+') and len(cleaned) == 9:
            cleaned = f"+256{cleaned}"
        elif not cleaned.startswith('+') and len(cleaned) == 10:
            cleaned = f"+256{cleaned[1:]}"
        
        return cleaned

# Singleton instance
notification_service = NotificationService()



