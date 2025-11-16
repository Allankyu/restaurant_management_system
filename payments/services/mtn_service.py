import requests
import json
import base64
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MTNMobileMoneyService:
    def __init__(self):
        from payments.models import PaymentProviderConfig
        try:
            self.config = PaymentProviderConfig.objects.get(provider='mtn', is_active=True)
        except PaymentProviderConfig.DoesNotExist:
            logger.error("MTN Mobile Money configuration not found")
            # Fallback to environment variables
            self.config = None
    
    def _get_access_token(self):
        """Get OAuth2 access token from MTN"""
        if not self.config:
            return None
            
        url = f"{self.config.base_url}/collection/token/"
        
        credentials = base64.b64encode(
            f"{self.config.api_key}:{self.config.api_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Ocp-Apim-Subscription-Key': self.config.api_key
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"MTN Token Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN Token Request Error: {str(e)}")
            return None
    
    def initiate_payment(self, phone_number, amount, transaction_id, description="Restaurant Order"):
        """Initiate MTN Mobile Money payment request"""
        access_token = self._get_access_token()
        if not access_token:
            return False, "Failed to authenticate with MTN"
        
        url = f"{self.config.base_url}/collection/v1_0/requesttopay"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Reference-Id': transaction_id,
            'X-Target-Environment': 'sandbox',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.config.api_key
        }
        
        payload = {
            "amount": str(amount),
            "currency": "UGX",
            "externalId": transaction_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": self._format_phone_number(phone_number)
            },
            "payerMessage": description,
            "payeeNote": f"Order {transaction_id}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 202:
                return True, "Payment request sent to customer"
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"MTN Payment Initiation Failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN Payment Request Error: {str(e)}")
            return False, f"Network error: {str(e)}"
    
    def _format_phone_number(self, phone_number):
        """Format phone number to MTN format (256XXXXXXXXX)"""
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif cleaned.startswith('7'):
            cleaned = '256' + cleaned
        
        return cleaned