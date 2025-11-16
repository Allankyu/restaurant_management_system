import requests
import json
import base64
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AirtelMoneyService:
    def __init__(self):
        from payments.models import PaymentProviderConfig
        try:
            self.config = PaymentProviderConfig.objects.get(provider='airtel', is_active=True)
        except PaymentProviderConfig.DoesNotExist:
            logger.error("Airtel Money configuration not found")
            # Fallback to environment variables
            self.config = None
    
    def _get_access_token(self):
        """Get OAuth2 access token from Airtel"""
        if not self.config:
            return None
            
        url = f"{self.config.base_url}/auth/oauth2/token"
        
        credentials = base64.b64encode(
            f"{self.config.api_key}:{self.config.api_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Airtel Token Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtel Token Request Error: {str(e)}")
            return None
    
    def initiate_payment(self, phone_number, amount, transaction_id, description="Restaurant Order"):
        """Initiate Airtel Money payment"""
        access_token = self._get_access_token()
        if not access_token:
            return False, "Failed to authenticate with Airtel"
        
        url = f"{self.config.base_url}/merchant/v1/payments/"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'X-Country': 'UG',
            'X-Currency': 'UGX'
        }
        
        payload = {
            "reference": transaction_id,
            "subscriber": {
                "country": "UG",
                "currency": "UGX",
                "msisdn": self._format_phone_number(phone_number)
            },
            "transaction": {
                "amount": amount,
                "country": "UG",
                "currency": "UGX",
                "id": transaction_id
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('status') == 'TS':
                    return True, "Payment initiated successfully"
                else:
                    error_msg = data.get('data', {}).get('message', 'Unknown error')
                    return False, error_msg
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Airtel Payment Initiation Failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtel Payment Request Error: {str(e)}")
            return False, f"Network error: {str(e)}"
    
    def check_payment_status(self, transaction_id):
        """Check Airtel payment status"""
        access_token = self._get_access_token()
        if not access_token:
            return None
        
        url = f"{self.config.base_url}/standard/v1/payments/{transaction_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'X-Country': 'UG',
            'X-Currency': 'UGX'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('status')
            else:
                logger.error(f"Airtel Status Check Failed: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtel Status Check Error: {str(e)}")
            return None
    
    def _format_phone_number(self, phone_number):
        """Format phone number to Airtel format (256XXXXXXXXX)"""
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif cleaned.startswith('7'):
            cleaned = '256' + cleaned
        
        return cleaned