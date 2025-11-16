import requests
import json
import logging
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class YoPaymentsService:
    def __init__(self):
        from payments.models import PaymentProviderConfig
        try:
            self.config = PaymentProviderConfig.objects.get(provider='yo', is_active=True)
            self.test_mode = False
        except PaymentProviderConfig.DoesNotExist:
            logger.warning("Yo! Payments configuration not found - using test mode")
            self.config = None
            self.test_mode = True
    
    def initiate_payment(self, phone_number, amount, transaction_id, description="Restaurant Order"):
        """Initiate Yo! Payments mobile money payment"""
        
        # Test mode - simulate payment initiation
        if self.test_mode:
            logger.info(f"TEST MODE: Simulating Yo! payment for {phone_number}, amount: {amount}")
            return True, "TEST MODE: Payment initiated successfully. Please check your phone."
        
        if not self.config or not self.config.yo_username or not self.config.yo_password:
            return False, "Yo! Payments configuration incomplete"
        
        # Yo! Payments API endpoint
        url = "https://paymentsapi.yo.co.ug/yopayments-main/task.php"
        
        # Format phone number for Yo! (256XXXXXXXXX)
        formatted_phone = self._format_phone_number(phone_number)
        
        payload = {
            'method': 'acdepositfunds',
            'username': self.config.yo_username,
            'password': self.config.yo_password,
            'amount': str(amount),
            'account': formatted_phone,
            'narrative': description,
            'external_reference': transaction_id,
            'provider': 'YO',  # Let Yo! handle the provider selection
            'instant_notification_url': self.config.callback_url or f"{settings.BASE_URL}/payments/webhook/yo/",
        }
        
        try:
            logger.info(f"Initiating Yo! payment: {payload}")
            response = requests.post(url, data=payload, timeout=30)
            response_data = response.text
            
            logger.info(f"Yo! Payments response: {response_data}")
            
            # Parse Yo! response (they return plain text)
            if "SUCCEEDED" in response_data.upper() or "OK" in response_data.upper():
                return True, "Payment request sent successfully. Please check your phone to complete the transaction."
            elif "PENDING" in response_data.upper():
                return True, "Payment is being processed. Please check your phone."
            else:
                error_msg = self._parse_yo_error(response_data)
                return False, f"Payment failed: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Yo! Payments Request Error: {str(e)}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Yo! Payments Error: {str(e)}")
            return False, f"Payment processing error: {str(e)}"
    
    def check_payment_status(self, transaction_id):
        """Check Yo! payment status"""
        if self.test_mode:
            # In test mode, simulate status check
            return "SUCCEEDED"
            
        if not self.config or not self.config.yo_username or not self.config.yo_password:
            return None
        
        url = "https://paymentsapi.yo.co.ug/yopayments-main/task.php"
        
        payload = {
            'method': 'transactionquery',
            'username': self.config.yo_username,
            'password': self.config.yo_password,
            'external_reference': transaction_id,
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response_data = response.text
            
            # Parse the status from response
            if "SUCCEEDED" in response_data.upper():
                return "SUCCEEDED"
            elif "PENDING" in response_data.upper():
                return "PENDING"
            elif "FAILED" in response_data.upper():
                return "FAILED"
            else:
                return "UNKNOWN"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Yo! Status Check Error: {str(e)}")
            return None
    
    def _format_phone_number(self, phone_number):
        """Format phone number to Yo! format (256XXXXXXXXX)"""
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif cleaned.startswith('7'):
            cleaned = '256' + cleaned
        
        return cleaned
    
    def _parse_yo_error(self, response_text):
        """Parse Yo! Payments error messages"""
        response_upper = response_text.upper()
        
        if "INSUFFICIENT FUNDS" in response_upper:
            return "Insufficient funds in your mobile money account"
        elif "INVALID ACCOUNT" in response_upper:
            return "Invalid phone number or mobile money account"
        elif "TRANSACTION FAILED" in response_upper:
            return "Transaction was declined by your mobile network"
        elif "TIMEOUT" in response_upper:
            return "Transaction timeout. Please try again"
        elif "DUPLICATE" in response_upper:
            return "Duplicate transaction detected"
        else:
            return f"Payment error: {response_text}"