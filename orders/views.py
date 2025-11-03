from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Order, OrderItem, Customer
from core.models import Customer, Employee, Branch
from inventory.models import MenuItem
from reservations.models import Table
from django.db.models import Q
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
import tempfile
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect


@login_required
def order_list(request):
    branch_id = request.GET.get('branch')
    selected_branch = None
    
    is_admin = request.user.is_superuser or request.user.is_staff
    
    if is_admin:
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            selected_branch = get_object_or_404(Branch, id=branch_id)
            orders = Order.objects.filter(branch=selected_branch)
        else:
            orders = Order.objects.all()
    else:
        user_branch = None
        if hasattr(request.user, 'employee'):
            user_branch = request.user.employee.branch
        
        if user_branch:
            selected_branch = user_branch
            branches = Branch.objects.filter(id=user_branch.id)
            orders = Order.objects.filter(branch=user_branch)
        else:
            messages.error(request, "You are not assigned to any branch.")
            return redirect('core:dashboard')
    
    orders = orders.order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query)
        )
    
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    context = {
        'orders': orders,
        'status_choices': Order.ORDER_STATUS,
        'is_admin': is_admin,
        'branches': branches if is_admin else [],
        'selected_branch': selected_branch,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have access to this order")
        return redirect('orders:order_list')
    
    order_items = order.order_items.all()
    
    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_create(request):
    user_branch = None
    if hasattr(request.user, 'employee'):
        user_branch = request.user.employee.branch
    
    branches = Branch.objects.filter(is_active=True)
    customers = Customer.objects.all()
    
    if user_branch and not request.user.is_superuser:
        waiters = Employee.objects.filter(
            employee_type='waiter', 
            is_active=True,
            branch=user_branch
        )
        tables = Table.objects.filter(is_available=True, branch=user_branch)
    else:
        waiters = Employee.objects.filter(employee_type='waiter', is_active=True)
        tables = Table.objects.filter(is_available=True)
    
    # Get menu items organized by type
    base_items = MenuItem.objects.filter(item_type='base', is_available=True)
    protein_sources = MenuItem.objects.filter(item_type='source', is_available=True)
    combo_items = MenuItem.objects.filter(item_type='combo', is_available=True)
    beverage_items = MenuItem.objects.filter(item_type='beverage', is_available=True)
    side_items = MenuItem.objects.filter(item_type='side', is_available=True)
    
    recent_customers = Customer.objects.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        try:
            # Validate required fields
            if not request.POST.get('customer'):
                messages.error(request, 'Please select a customer.')
                return render(request, 'orders/order_create.html', context)
            
            if not request.POST.get('waiter'):
                messages.error(request, 'Please select a waiter.')
                return render(request, 'orders/order_create.html', context)
            if request.user.is_superuser and request.POST.get('branch'):
                branch_to_assign = get_object_or_404(Branch, id=request.POST.get('branch'))
            else:
                branch_to_assign = user_branch
                if not branch_to_assign:
                    branch_to_assign = Branch.objects.filter(is_active=True).first()
                    if not branch_to_assign:
                        branch_to_assign = Branch.objects.create(
                            name="Main Branch",
                            address="123 Restaurant Street",
                            phone="+1234567890",
                            opening_time="09:00:00",
                            closing_time="22:00:00",
                            is_active=True
                        )
            
            order = Order.objects.create(
                customer_id=request.POST.get('customer'),
                order_type=request.POST.get('order_type', 'dine_in'),
                table_number=request.POST.get('table_number'),
                waiter_id=request.POST.get('waiter'),
                notes=request.POST.get('notes', ''),
                branch=branch_to_assign
            )
            
            # Process regular menu items
            for key, value in request.POST.items():
                if key.startswith('qty_') and value and int(value) > 0:
                    item_id = key.replace('qty_', '')
                    quantity = int(value)
                    
                    try:
                        menu_item = MenuItem.objects.get(id=item_id)
                        unit_price = menu_item.actual_price or 0
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=menu_item,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                    except MenuItem.DoesNotExist:
                        continue
            
            # Process custom combos and individual items
            custom_base_items = request.POST.getlist('custom_base_items[]')
            custom_source_items = request.POST.getlist('custom_source_items[]')
            custom_quantities = request.POST.getlist('custom_quantities[]')
            custom_types = request.POST.getlist('custom_types[]')
            
            print("DEBUG - Custom data received:")
            print("Base items:", custom_base_items)
            print("Source items:", custom_source_items)
            print("Quantities:", custom_quantities)
            print("Types:", custom_types)
            
            # Process each custom item
            for i in range(len(custom_quantities)):
                if not custom_quantities[i] or int(custom_quantities[i]) <= 0:
                    continue
                    
                quantity = int(custom_quantities[i])
                item_type = custom_types[i] if i < len(custom_types) else 'custom_combo'
                
                # Handle protein only orders
                if item_type == 'protein_only' and i < len(custom_source_items) and custom_source_items[i]:
                    try:
                        source_item = MenuItem.objects.get(id=custom_source_items[i])
                        unit_price = source_item.actual_price or 0
                        display_name = f"{source_item.name} (Protein Only)"
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=source_item,
                            quantity=quantity,
                            unit_price=unit_price,
                            notes=display_name,
                            is_custom_combo=False,
                            custom_protein_source=source_item
                        )
                    except MenuItem.DoesNotExist:
                        continue
                
                # Handle custom combos (base + protein)
                elif item_type == 'custom_combo' and i < len(custom_base_items) and i < len(custom_source_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    source_id = custom_source_items[i]
                    
                    if base_ids and source_id:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            source_item = MenuItem.objects.get(id=source_id)
                            
                            # Calculate total price
                            base_price = sum(base.actual_price or 0 for base in base_items_list)
                            source_price = source_item.actual_price or 0
                            total_price = base_price + source_price
                            
                            # Create display name
                            base_names = " + ".join([base.name for base in base_items_list])
                            display_name = f"Custom: {base_names} with {source_item.name}"
                            
                            # Use the first base item as reference
                            reference_item = base_items_list.first()
                            
                            OrderItem.objects.create(
                                order=order,
                                menu_item=reference_item,
                                quantity=quantity,
                                unit_price=total_price,
                                notes=display_name,
                                is_custom_combo=True,
                                custom_base_item=reference_item,
                                custom_protein_source=source_item
                            )
                        except (MenuItem.DoesNotExist, ValueError):
                            continue
                
                # Handle individual base foods (priced base foods without protein)
                elif item_type == 'base_only' and i < len(custom_base_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    
                    if base_ids:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            
                            # Only create order items for priced base foods
                            for base_item in base_items_list:
                                base_price = base_item.actual_price or 0
                                if base_price > 0:  # Only create if it has a price
                                    display_name = f"{base_item.name} (Base Only)"
                                    
                                    OrderItem.objects.create(
                                        order=order,
                                        menu_item=base_item,
                                        quantity=quantity,
                                        unit_price=base_price,
                                        notes=display_name,
                                        is_custom_combo=False
                                    )
                        except (MenuItem.DoesNotExist, ValueError):
                            continue
            
            # Recalculate order total
            order.total_amount = order.calculate_total()
            order.save()
            
            messages.success(request, f'Order #{order.order_number} created successfully!')
            return redirect('orders:order_detail', pk=order.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            import traceback
            print("ERROR:", traceback.format_exc())
    
    context = {
        'customers': customers,
        'waiters': waiters,
        'tables': tables,
        'base_items': base_items,
        'protein_sources': protein_sources,
        'combo_items': combo_items,
        'beverage_items': beverage_items,
        'side_items': side_items,
        'recent_customers': recent_customers,
        'user_branch': user_branch,
        'branches': branches,
    }
    
    return render(request, 'orders/order_create.html', context)

@require_POST
@csrf_protect
def create_customer_ajax(request):
    """
    AJAX view for creating customers from the order form
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        # Validation
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Customer name is required'
            })

        if not phone:
            return JsonResponse({
                'success': False,
                'error': 'Customer phone number is required'
            })

        # Check for duplicate phone number
        if Customer.objects.filter(phone=phone).exists():
            return JsonResponse({
                'success': False,
                'error': 'A customer with this phone number already exists'
            })

        # Create customer
        customer = Customer.objects.create(
            name=name,
            phone=phone,
            email=email if email else None,
            address=address if address else None
        )

        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email or '',
                'address': customer.address or ''
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to update this order")
        return redirect('orders:order_list')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.ORDER_STATUS):
            old_status = order.status  # Store old status for comparison
            order.status = new_status
            order.save()
            
            # SMS NOTIFICATION INTEGRATION
            try:
                from notifications.services import notification_service
                
                # Check if we have a customer with phone number
                if order.customer and order.customer.phone:
                    
                    # Send SMS when order status changes to "preparing"
                    if new_status == 'preparing' and old_status != 'preparing':
                        notification_service.send_notification(
                            notification_type='order_ready',
                            recipient={'phone': order.customer.phone},
                            context_data={
                                'user_name': order.customer.name,
                                'restaurant': 'Fine Dining Restaurant',
                                'order_number': order.order_number,
                                'order_total': f"UGX {order.total_amount:,.0f}",
                                'status_update': 'is now being prepared'
                            }
                        )
                        messages.info(request, f'Order preparation SMS sent to {order.customer.name}')
                        
                    # Send SMS when order status changes to "ready"
                    elif new_status == 'ready' and old_status != 'ready':
                        notification_service.send_notification(
                            notification_type='order_ready',
                            recipient={'phone': order.customer.phone},
                            context_data={
                                'user_name': order.customer.name,
                                'restaurant': 'Fine Dining Restaurant',
                                'order_number': order.order_number,
                                'order_total': f"UGX {order.total_amount:,.0f}",
                                'status_update': 'is ready for pickup'
                            }
                        )
                        messages.info(request, f'Order ready SMS sent to {order.customer.name}')
                        
                    # Send SMS when order status changes to "served"
                    elif new_status == 'served' and old_status != 'served':
                        notification_service.send_notification(
                            notification_type='order_ready',
                            recipient={'phone': order.customer.phone},
                            context_data={
                                'user_name': order.customer.name,
                                'restaurant': 'Fine Dining Restaurant',
                                'order_number': order.order_number,
                                'order_total': f"UGX {order.total_amount:,.0f}",
                                'status_update': 'has been served'
                            }
                        )
                        messages.info(request, f'Order served SMS sent to {order.customer.name}')
                        
                else:
                    # No customer or phone number available
                    messages.warning(request, 'Order status updated but no customer phone number available for SMS')
                    
            except Exception as sms_error:
                # Log SMS error but don't break the order update process
                print(f"SMS notification failed: {sms_error}")
                messages.warning(request, 'Order status updated but SMS notification failed')
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('orders:order_detail', pk=pk)

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to delete this order")
        return redirect('orders:order_list')
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Order #{order_number} has been deleted.')
        return redirect('orders:order_list')
    
    return render(request, 'orders/order_confirm_delete.html', {'order': order})

@login_required
def order_dashboard(request):
    branch_id = request.GET.get('branch')
    selected_branch = None
    
    is_admin = request.user.is_superuser or request.user.is_staff
    
    today = timezone.now().date()
    
    if is_admin:
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            selected_branch = get_object_or_404(Branch, id=branch_id)
            orders = Order.objects.filter(branch=selected_branch)
        else:
            orders = Order.objects.all()
    else:
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            selected_branch = manager_employee.branch
            branches = Branch.objects.filter(id=selected_branch.id)
            orders = Order.objects.filter(branch=selected_branch)
        except Employee.DoesNotExist:
            messages.error(request, "You are not authorized to view orders.")
            return redirect('core:dashboard')
    
    today_orders = orders.filter(created_at__date=today)
    recent_orders = orders.order_by('-created_at')[:10]
    
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    completed_orders = orders.filter(status='completed').count()
    
    today_revenue = today_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'today_orders_count': today_orders.count(),
        'today_revenue': today_revenue,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
        'is_admin': is_admin,
        'branches': branches if is_admin else [],
        'selected_branch': selected_branch,
    }
    
    return render(request, 'orders/dashboard.html', context)

@login_required
def print_receipt(request, pk):
    """Print receipt as HTML for browser printing"""
    order = get_object_or_404(Order, pk=pk)
    
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to print this receipt")
        return redirect('orders:order_list')
    
    context = {
        'order': order,
        'order_items': order.order_items.all(),
        'business_name': 'MAAMA JOAN RESTAURANT',
        'business_address': 'NAJJERA II STREET',
        'business_phone': '+256 757 389 669',
    }
    
    return render(request, 'orders/receipt_print.html', context)

@login_required
def view_receipt(request, pk):
    """View receipt in browser"""
    order = get_object_or_404(Order, pk=pk)
    
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to view this receipt")
        return redirect('orders:order_list')
    
    context = {
        'order': order,
        'order_items': order.order_items.all(),
        'business_name': 'Your Restaurant Name',
        'business_address': '123 Restaurant Street',
        'business_phone': '+254 712 345 678',
    }
    
    return render(request, 'orders/receipt_view.html', context)

@login_required
def order_edit(request, pk):
    """Edit an existing order"""
    order = get_object_or_404(Order, pk=pk)
    
    # Check permissions
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != order.branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to edit this order")
        return redirect('orders:order_list')
    
    # Get all necessary data (similar to order_create)
    user_branch = None
    if hasattr(request.user, 'employee'):
        user_branch = request.user.employee.branch
    
    branches = Branch.objects.filter(is_active=True)
    customers = Customer.objects.all()
    
    if user_branch and not request.user.is_superuser:
        waiters = Employee.objects.filter(
            employee_type='waiter', 
            is_active=True,
            branch=user_branch
        )
        tables = Table.objects.filter(is_available=True, branch=user_branch)
    else:
        waiters = Employee.objects.filter(employee_type='waiter', is_active=True)
        tables = Table.objects.filter(is_available=True)
    
    # Get menu items organized by type
    base_items = MenuItem.objects.filter(item_type='base', is_available=True)
    protein_sources = MenuItem.objects.filter(item_type='source', is_available=True)
    combo_items = MenuItem.objects.filter(item_type='combo', is_available=True)
    beverage_items = MenuItem.objects.filter(item_type='beverage', is_available=True)
    side_items = MenuItem.objects.filter(item_type='side', is_available=True)
    
    recent_customers = Customer.objects.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        try:
            # Update order details
            order.customer_id = request.POST.get('customer')
            order.order_type = request.POST.get('order_type', 'dine_in')
            order.table_number = request.POST.get('table_number')
            order.waiter_id = request.POST.get('waiter')
            order.notes = request.POST.get('notes', '')
            
            # Update branch if admin
            if request.user.is_superuser and request.POST.get('branch'):
                order.branch_id = request.POST.get('branch')
            
            order.save()
            
            # Clear existing order items
            order.order_items.all().delete()
            
            # Process regular menu items
            for key, value in request.POST.items():
                if key.startswith('qty_') and value and int(value) > 0:
                    item_id = key.replace('qty_', '')
                    quantity = int(value)
                    
                    try:
                        menu_item = MenuItem.objects.get(id=item_id)
                        unit_price = menu_item.actual_price or 0
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=menu_item,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                    except MenuItem.DoesNotExist:
                        continue
            
            # Process custom combos and individual items
            custom_base_items = request.POST.getlist('custom_base_items[]')
            custom_source_items = request.POST.getlist('custom_source_items[]')
            custom_quantities = request.POST.getlist('custom_quantities[]')
            custom_types = request.POST.getlist('custom_types[]')
            
            # Process each custom item
            for i in range(len(custom_quantities)):
                if not custom_quantities[i] or int(custom_quantities[i]) <= 0:
                    continue
                    
                quantity = int(custom_quantities[i])
                item_type = custom_types[i] if i < len(custom_types) else 'custom_combo'
                
                # Handle protein only orders
                if item_type == 'protein_only' and i < len(custom_source_items) and custom_source_items[i]:
                    try:
                        source_item = MenuItem.objects.get(id=custom_source_items[i])
                        unit_price = source_item.actual_price or 0
                        display_name = f"{source_item.name} (Protein Only)"
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=source_item,
                            quantity=quantity,
                            unit_price=unit_price,
                            notes=display_name,
                            is_custom_combo=False,
                            custom_protein_source=source_item
                        )
                    except MenuItem.DoesNotExist:
                        continue
                
                # Handle custom combos (base + protein)
                elif item_type == 'custom_combo' and i < len(custom_base_items) and i < len(custom_source_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    source_id = custom_source_items[i]
                    
                    if base_ids and source_id:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            source_item = MenuItem.objects.get(id=source_id)
                            
                            # Calculate total price
                            base_price = sum(base.actual_price or 0 for base in base_items_list)
                            source_price = source_item.actual_price or 0
                            total_price = base_price + source_price
                            
                            # Create display name
                            base_names = " + ".join([base.name for base in base_items_list])
                            display_name = f"Custom: {base_names} with {source_item.name}"
                            
                            # Use the first base item as reference
                            reference_item = base_items_list.first()
                            
                            OrderItem.objects.create(
                                order=order,
                                menu_item=reference_item,
                                quantity=quantity,
                                unit_price=total_price,
                                notes=display_name,
                                is_custom_combo=True,
                                custom_base_item=reference_item,
                                custom_protein_source=source_item
                            )
                        except (MenuItem.DoesNotExist, ValueError):
                            continue
                
                # Handle individual base foods (priced base foods without protein)
                elif item_type == 'base_only' and i < len(custom_base_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    
                    if base_ids:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            
                            # Only create order items for priced base foods
                            for base_item in base_items_list:
                                base_price = base_item.actual_price or 0
                                if base_price > 0:  # Only create if it has a price
                                    display_name = f"{base_item.name} (Base Only)"
                                    
                                    OrderItem.objects.create(
                                        order=order,
                                        menu_item=base_item,
                                        quantity=quantity,
                                        unit_price=base_price,
                                        notes=display_name,
                                        is_custom_combo=False
                                    )
                        except (MenuItem.DoesNotExist, ValueError):
                            continue
            
            # Recalculate order total
            order.total_amount = order.calculate_total()
            order.save()
            
            messages.success(request, f'Order #{order.order_number} updated successfully!')
            return redirect('orders:order_detail', pk=order.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating order: {str(e)}')
            import traceback
            print("ERROR:", traceback.format_exc())
    
    context = {
        'order': order,
        'customers': customers,
        'waiters': waiters,
        'tables': tables,
        'base_items': base_items,
        'protein_sources': protein_sources,
        'combo_items': combo_items,
        'beverage_items': beverage_items,
        'side_items': side_items,
        'recent_customers': recent_customers,
        'user_branch': user_branch,
        'branches': branches,
        'is_edit': True,  # Flag to indicate edit mode
    }
    
    return render(request, 'orders/order_create.html', context)


def online_order(request):
    """Public online ordering page for delivery - Uses same menu as managers"""
    try:
        print("=== DEBUG: Loading online order with manager's field names ===")
        
        # Use the exact same query as manager's order_create view
        base_items = MenuItem.objects.filter(item_type='base', is_available=True)
        protein_sources = MenuItem.objects.filter(item_type='source', is_available=True)
        combo_items = MenuItem.objects.filter(item_type='combo', is_available=True)
        beverage_items = MenuItem.objects.filter(item_type='beverage', is_available=True)
        side_items = MenuItem.objects.filter(item_type='side', is_available=True)
        
        print(f"DEBUG: Base items: {base_items.count()}")
        print(f"DEBUG: Protein sources: {protein_sources.count()}")
        print(f"DEBUG: Combo items: {combo_items.count()}")
        print(f"DEBUG: Beverage items: {beverage_items.count()}")
        print(f"DEBUG: Side items: {side_items.count()}")
        
        # Debug: Print sample items from each category
        if combo_items.count() > 0:
            print(f"DEBUG: Sample combo: {combo_items.first().name} - Ksh {combo_items.first().actual_price}")
        if beverage_items.count() > 0:
            print(f"DEBUG: Sample beverage: {beverage_items.first().name} - Ksh {beverage_items.first().actual_price}")
        if side_items.count() > 0:
            print(f"DEBUG: Sample side: {side_items.first().name} - Ksh {side_items.first().actual_price}")
        
        context = {
            'combo_items': combo_items,
            'beverage_items': beverage_items,
            'side_items': side_items,
            'base_items': base_items,
            'protein_sources': protein_sources,
        }
        
        print("=== DEBUG: Online order context ready ===")
        return render(request, 'orders/online_order.html', context)
        
    except Exception as e:
        print(f"=== DEBUG: ERROR in online_order: {e} ===")
        import traceback
        traceback.print_exc()
        
        # Fallback with empty querysets
        context = {
            'combo_items': MenuItem.objects.none(),
            'beverage_items': MenuItem.objects.none(),
            'side_items': MenuItem.objects.none(),
            'base_items': MenuItem.objects.none(),
            'protein_sources': MenuItem.objects.none(),
        }
 
        return render(request, 'orders/online_order.html', context)
    
@csrf_exempt
def submit_online_order(request):
    """Handle online order submission including custom combos"""
    if request.method == 'POST':
        try:
            # Get customer information
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')
            customer_email = request.POST.get('customer_email')
            delivery_address = request.POST.get('delivery_address')
            order_notes = request.POST.get('order_notes', '')
            total_amount = request.POST.get('total_amount')
            preferred_delivery_time = request.POST.get('preferred_delivery_time', 'asap')
            
            print(f"DEBUG: Received total_amount from frontend: {total_amount}")
            
            # Find or create customer
            customer, created = Customer.objects.get_or_create(
                phone=customer_phone,
                defaults={
                    'name': customer_name,
                    'email': customer_email,
                    'address': delivery_address
                }
            )
            
            # If customer exists but details are different, update them
            if not created:
                customer.name = customer_name
                if customer_email:
                    customer.email = customer_email
                customer.address = delivery_address
                customer.save()
            
            # Get default branch for online orders
            default_branch = Branch.objects.filter(is_active=True).first()
            if not default_branch:
                # Create a default branch if none exists
                default_branch = Branch.objects.create(
                    name="Main Branch",
                    address="123 Restaurant Street",
                    phone="+1234567890",
                    opening_time="09:00:00",
                    closing_time="22:00:00",
                    is_active=True
                )
            
            # Create order with delivery_address (since you added it to model)
            order = Order.objects.create(
                customer=customer,
                order_type='delivery',
                total_amount=total_amount,  # Use the frontend calculated amount
                status='pending',
                notes=f"Online Order - {order_notes}\nPreferred Delivery: {preferred_delivery_time}",
                delivery_address=delivery_address,  # This is fine since you added it to model
                branch=default_branch
            )
            
            print(f"DEBUG: Created order with initial total: {order.total_amount}")
            
            # Process regular menu items
            regular_items_count = 0
            for key, value in request.POST.items():
                if key.startswith('qty_') and value and int(value) > 0:
                    item_id = key.replace('qty_', '')
                    quantity = int(value)
                    
                    try:
                        menu_item = MenuItem.objects.get(id=item_id)
                        unit_price = menu_item.actual_price or 0
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=menu_item,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                        regular_items_count += 1
                        print(f"DEBUG: Added regular item: {menu_item.name} x {quantity} @ {unit_price}")
                    except MenuItem.DoesNotExist:
                        print(f"DEBUG: Menu item not found: {item_id}")
                        continue
            
            # Process custom combos
            custom_base_items = request.POST.getlist('custom_base_items[]')
            custom_source_items = request.POST.getlist('custom_source_items[]')
            custom_quantities = request.POST.getlist('custom_quantities[]')
            custom_types = request.POST.getlist('custom_types[]')
            
            print("DEBUG - Custom data received:")
            print("Base items:", custom_base_items)
            print("Source items:", custom_source_items)
            print("Quantities:", custom_quantities)
            print("Types:", custom_types)
            
            custom_items_count = 0
            # Process each custom item
            for i in range(len(custom_quantities)):
                if not custom_quantities[i] or int(custom_quantities[i]) <= 0:
                    continue
                    
                quantity = int(custom_quantities[i])
                item_type = custom_types[i] if i < len(custom_types) else 'custom_combo'
                
                # Handle protein only orders
                if item_type == 'protein_only' and i < len(custom_source_items) and custom_source_items[i]:
                    try:
                        source_item = MenuItem.objects.get(id=custom_source_items[i])
                        unit_price = source_item.actual_price or 0
                        display_name = f"{source_item.name} (Protein Only)"
                        
                        OrderItem.objects.create(
                            order=order,
                            menu_item=source_item,
                            quantity=quantity,
                            unit_price=unit_price,
                            notes=display_name,
                            is_custom_combo=False,
                            custom_protein_source=source_item
                        )
                        custom_items_count += 1
                        print(f"DEBUG: Added protein only: {source_item.name} x {quantity} @ {unit_price}")
                    except MenuItem.DoesNotExist:
                        print(f"DEBUG: Protein source not found: {custom_source_items[i]}")
                        continue
                
                # Handle custom combos (base + protein)
                elif item_type == 'custom_combo' and i < len(custom_base_items) and i < len(custom_source_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    source_id = custom_source_items[i]
                    
                    if base_ids and source_id:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            source_item = MenuItem.objects.get(id=source_id)
                            
                            # Calculate total price
                            base_price = sum(base.actual_price or 0 for base in base_items_list)
                            source_price = source_item.actual_price or 0
                            total_price = base_price + source_price
                            
                            # Create display name
                            base_names = " + ".join([base.name for base in base_items_list])
                            display_name = f"Custom: {base_names} with {source_item.name}"
                            
                            # Use the first base item as reference
                            reference_item = base_items_list.first()
                            
                            OrderItem.objects.create(
                                order=order,
                                menu_item=reference_item,
                                quantity=quantity,
                                unit_price=total_price,
                                notes=display_name,
                                is_custom_combo=True,
                                custom_base_item=reference_item,
                                custom_protein_source=source_item
                            )
                            custom_items_count += 1
                            print(f"DEBUG: Added custom combo: {display_name} x {quantity} @ {total_price}")
                        except (MenuItem.DoesNotExist, ValueError) as e:
                            print(f"DEBUG: Custom combo error: {e}")
                            continue
                
                # Handle individual base foods (priced base foods without protein)
                elif item_type == 'base_only' and i < len(custom_base_items):
                    base_ids = custom_base_items[i].split(',') if custom_base_items[i] else []
                    
                    if base_ids:
                        try:
                            base_items_list = MenuItem.objects.filter(id__in=base_ids)
                            
                            # Only create order items for priced base foods
                            for base_item in base_items_list:
                                base_price = base_item.actual_price or 0
                                if base_price > 0:  # Only create if it has a price
                                    display_name = f"{base_item.name} (Base Only)"
                                    
                                    OrderItem.objects.create(
                                        order=order,
                                        menu_item=base_item,
                                        quantity=quantity,
                                        unit_price=base_price,
                                        notes=display_name,
                                        is_custom_combo=False
                                    )
                                    custom_items_count += 1
                                    print(f"DEBUG: Added base only: {base_item.name} x {quantity} @ {base_price}")
                        except (MenuItem.DoesNotExist, ValueError) as e:
                            print(f"DEBUG: Base only error: {e}")
                            continue
            
            # DEBUG: Check what order items were created
            order_items = OrderItem.objects.filter(order=order)
            print(f"DEBUG: Created {order_items.count()} order items total")
            print(f"DEBUG: Regular items: {regular_items_count}, Custom items: {custom_items_count}")
            
            total_calculated = 0
            for item in order_items:
                item_total = item.quantity * item.unit_price
                total_calculated += item_total
                print(f"  - {item.menu_item.name if item.menu_item else 'Custom'} x {item.quantity} @ {item.unit_price} = {item_total}")
            
            print(f"DEBUG: Frontend total: {total_amount}, Backend calculated total: {total_calculated}")
            
            # Use the backend calculated total to ensure accuracy
            order.total_amount = total_calculated
            order.save()
            
            print(f"DEBUG: Final order total saved: {order.total_amount}")
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'order_number': order.order_number,
                'total_amount': float(order.total_amount),  # Send back the actual total
                'message': 'Order placed successfully! We will contact you shortly.'
            })
            
        except Exception as e:
            print(f"ERROR in submit_online_order: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def online_order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/online_order_success.html', {'order': order})

def is_staff_user(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_user)
def order_management(request):
    """View all orders for staff users"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by order type if provided
    order_type_filter = request.GET.get('order_type')
    if order_type_filter:
        orders = orders.filter(order_type=order_type_filter)
    
    context = {
        'orders': orders,
        'status_choices': Order.ORDER_STATUS,
        'order_type_choices': Order.ORDER_TYPES,
    }
    return render(request, 'orders/order_management.html', context)

@login_required
@user_passes_test(is_staff_user)
def order_detail_management(request, order_id):
    """Detailed view of a specific order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/order_detail_management.html', context)

@login_required
@user_passes_test(is_staff_user)
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.GET.get('status')
    
    if new_status and new_status in dict(Order.ORDER_STATUS):
        order.status = new_status
        order.save()
        
        messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('orders:order_detail_management', order_id=order.id)

