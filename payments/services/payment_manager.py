from .mtn_service import MTNMobileMoneyService
from .yo_service import YoPaymentsService
from payments.models import PaymentTransaction
import logging

logger = logging.getLogger(__name__)

class PaymentManager:
    def __init__(self):
        self.services = {
            'yo': YoPaymentsService,  # Primary service
        }
        
        # Try to import other services, but don't fail if they're not implemented
        try:
            from .mtn_service import MTNMobileMoneyService
            self.services['mtn'] = MTNMobileMoneyService
        except ImportError as e:
            logger.warning("MTNMobileMoneyService not available: %s", str(e))
        
        try:
            from .airtel_service import AirtelMoneyService
            self.services['airtel'] = AirtelMoneyService
        except ImportError as e:
            logger.warning("AirtelMoneyService not available: %s", str(e))
    
    def initiate_payment(self, provider, phone_number, amount, order, description="Restaurant Order"):
        """Main method to initiate payments"""
        try:
            service_class = self.services.get(provider)
            if not service_class:
                return False, None, "Invalid payment provider"
            
            # Create transaction record
            transaction = PaymentTransaction.objects.create(
                order=order,
                transaction_id=self._generate_transaction_id(),
                provider=provider,
                phone_number=phone_number,
                amount=amount,
                status='initiated'
            )
            
            # Initialize service and initiate payment
            service = service_class()
            success, message = service.initiate_payment(
                phone_number, amount, transaction.transaction_id, description
            )
            
            if success:
                transaction.status = 'pending'
                transaction.save()
                return True, transaction.transaction_id, message
            else:
                transaction.status = 'failed'
                transaction.error_message = message
                transaction.save()
                return False, transaction.transaction_id, message
                
        except Exception as e:
            logger.error(f"Payment Manager Error: {str(e)}")
            return False, None, f"System error: {str(e)}"
    
    def check_transaction_status(self, transaction_id):
        """Check status of a transaction"""
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            service_class = self.services.get(transaction.provider)
            
            if not service_class:
                return None
            
            service = service_class()
            provider_status = service.check_payment_status(transaction_id)
            
            if provider_status:
                # Map provider status to our status
                status_map = {
                    'SUCCEEDED': 'successful',
                    'SUCCESSFUL': 'successful',
                    'FAILED': 'failed',
                    'PENDING': 'pending',
                    'TS': 'successful',  # Airtel success
                    'TF': 'failed',      # Airtel failed
                    'TP': 'pending',     # Airtel pending
                }
                
                new_status = status_map.get(provider_status, 'pending')
                
                # Only update if status changed
                if transaction.status != new_status:
                    transaction.status = new_status
                    transaction.yo_transaction_status = provider_status
                    transaction.save()
                    
                    # Update order status if payment successful
                    if new_status == 'successful':
                        transaction.order.status = 'paid'
                        transaction.order.save()
            
            return transaction.status
            
        except PaymentTransaction.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Status Check Error: {str(e)}")
            return None
    
    def _generate_transaction_id(self):
        """Generate unique transaction ID"""
        import uuid
        import time
        return f"YO{int(time.time())}{uuid.uuid4().hex[:6].upper()}"
    
    def get_available_providers(self):
        """Get list of available payment providers"""
        return list(self.services.keys())