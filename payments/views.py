from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
import logging
from .models import PaymentTransaction
from orders.models import Order
from .services.payment_manager import PaymentManager

logger = logging.getLogger(__name__)

@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if order is already paid
    if order.status == 'paid':
        messages.warning(request, 'This order has already been paid.')
        return redirect('orders:order_detail', order_id=order_id)
    
    payment_manager = PaymentManager()
    available_providers = payment_manager.get_available_providers()
    
    if request.method == 'POST':
        provider = request.POST.get('provider')
        phone_number = request.POST.get('phone_number')
        
        if not provider or not phone_number:
            messages.error(request, 'Please select payment provider and enter phone number')
            return redirect('payments:initiate_payment', order_id=order_id)
        
        if provider not in available_providers:
            messages.error(request, 'Selected payment provider is not available')
            return redirect('payments:initiate_payment', order_id=order_id)
        
        success, transaction_id, message = payment_manager.initiate_payment(
            provider, phone_number, order.total_amount, order,
            description=f"Payment for Order #{order.order_number}"
        )
        
        if success:
            messages.success(request, message)
            return redirect('payments:payment_status', transaction_id=transaction_id)
        else:
            messages.error(request, f'Payment failed: {message}')
            return redirect('payments:initiate_payment', order_id=order_id)
    
    return render(request, 'payments/initiate_payment.html', {
        'order': order,
        'available_providers': available_providers
    })

@login_required
def payment_status(request, transaction_id):
    transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
    
    # Check status if still pending
    if transaction.status in ['initiated', 'pending']:
        payment_manager = PaymentManager()
        payment_manager.check_transaction_status(transaction_id)
        transaction.refresh_from_db()
    
    return render(request, 'payments/payment_status.html', {
        'transaction': transaction,
        'order': transaction.order
    })

def payment_webhook(request, provider):
    """Webhook endpoint for payment providers to send callbacks"""
    if request.method == 'POST':
        try:
            # Try to parse JSON data first, then fall back to form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            logger.info(f"{provider.upper()} Webhook received: {data}")
            
            if provider == 'yo':
                return _handle_yo_webhook(data)
            elif provider == 'mtn':
                return _handle_mtn_webhook(data)
            elif provider == 'airtel':
                return _handle_airtel_webhook(data)
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid provider'})
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Processing error'})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'})

def _handle_yo_webhook(data):
    """Handle Yo! Payments webhook"""
    transaction_id = data.get('external_reference')
    status = data.get('transaction_status')
    yo_transaction_id = data.get('transaction_id')
    
    if not transaction_id:
        return JsonResponse({'status': 'error', 'message': 'Missing transaction reference'})
    
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        
        status_map = {
            'SUCCEEDED': 'successful',
            'SUCCESSFUL': 'successful',
            'FAILED': 'failed',
            'PENDING': 'pending',
        }
        
        new_status = status_map.get(status, 'pending')
        
        if transaction.status != new_status:
            transaction.status = new_status
            transaction.provider_transaction_id = yo_transaction_id
            transaction.yo_transaction_status = status
            transaction.save()
            
            # Update order status if payment successful
            if new_status == 'successful':
                transaction.order.status = 'paid'
                transaction.order.save()
                logger.info(f"Order {transaction.order.order_number} marked as paid via Yo! Payments")
        
        return JsonResponse({'status': 'success'})
        
    except PaymentTransaction.DoesNotExist:
        logger.error(f"Yo! Webhook: Transaction not found - {transaction_id}")
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'})

def _handle_mtn_webhook(data):
    """Handle MTN Mobile Money webhook"""
    transaction_id = data.get('externalId')
    status = data.get('status')
    
    if not transaction_id:
        return JsonResponse({'status': 'error', 'message': 'Missing transaction ID'})
    
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        
        status_map = {
            'SUCCESSFUL': 'successful',
            'FAILED': 'failed',
            'PENDING': 'pending',
        }
        
        new_status = status_map.get(status, 'pending')
        
        if transaction.status != new_status:
            transaction.status = new_status
            transaction.provider_transaction_id = data.get('financialTransactionId')
            transaction.save()
            
            if new_status == 'successful':
                transaction.order.status = 'paid'
                transaction.order.save()
                logger.info(f"Order {transaction.order.order_number} marked as paid via MTN")
        
        return JsonResponse({'status': 'success'})
        
    except PaymentTransaction.DoesNotExist:
        logger.error(f"MTN Webhook: Transaction not found - {transaction_id}")
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'})

def _handle_airtel_webhook(data):
    """Handle Airtel Money webhook"""
    transaction_id = data.get('reference') or data.get('transaction', {}).get('id')
    status = data.get('transaction', {}).get('status') or data.get('status')
    
    if not transaction_id:
        return JsonResponse({'status': 'error', 'message': 'Missing transaction ID'})
    
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        
        status_map = {
            'TS': 'successful',  # Transaction Success
            'TF': 'failed',      # Transaction Failed
            'TP': 'pending',     # Transaction Pending
            'SUCCESSFUL': 'successful',
            'FAILED': 'failed',
            'PENDING': 'pending',
        }
        
        new_status = status_map.get(status, 'pending')
        
        if transaction.status != new_status:
            transaction.status = new_status
            transaction.provider_transaction_id = data.get('id') or data.get('transaction_id')
            transaction.save()
            
            if new_status == 'successful':
                transaction.order.status = 'paid'
                transaction.order.save()
                logger.info(f"Order {transaction.order.order_number} marked as paid via Airtel")
        
        return JsonResponse({'status': 'success'})
        
    except PaymentTransaction.DoesNotExist:
        logger.error(f"Airtel Webhook: Transaction not found - {transaction_id}")
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'})

@login_required
def payment_test(request):
    """Test view to check payment setup"""
    payment_manager = PaymentManager()
    available_providers = payment_manager.get_available_providers()
    
    # Test creating a payment transaction
    test_transaction = None
    try:
        test_order = Order.objects.first()
        if test_order:
            test_transaction = PaymentTransaction.objects.create(
                order=test_order,
                transaction_id=f"TEST{123456}",
                provider='yo',
                phone_number='256700000000',
                amount=1000,
                status='pending'
            )
    except Exception as e:
        logger.error(f"Test transaction creation failed: {e}")
    
    return JsonResponse({
        'available_providers': available_providers,
        'test_transaction_created': test_transaction is not None,
        'status': 'ok'
    })