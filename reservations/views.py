from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from datetime import datetime, date
from .models import Reservation, Table
from core.models import Customer
from core.models import Branch, Employee 
from notifications.services import notification_service

@login_required
def reservation_dashboard(request):
    # Get selected branch from query parameters
    branch_id = request.GET.get('branch')
    selected_branch = None
    
    # Check if user is admin
    is_admin = request.user.is_superuser or request.user.is_staff
    
    today = timezone.now().date()
    
    if is_admin:
        # Admin can view any branch's reservations
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            selected_branch = get_object_or_404(Branch, id=branch_id)
            # Filter data for selected branch
            reservations = Reservation.objects.filter(branch=selected_branch)
            tables = Table.objects.filter(branch=selected_branch)
        else:
            # Show all reservations for admin (system-wide)
            reservations = Reservation.objects.all()
            tables = Table.objects.all()
    else:
        # Regular manager - only their branch
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            selected_branch = manager_employee.branch
            branches = Branch.objects.filter(id=selected_branch.id)
            reservations = Reservation.objects.filter(branch=selected_branch)
            tables = Table.objects.filter(branch=selected_branch)
        except Employee.DoesNotExist:
            messages.error(request, "You are not authorized to view reservations.")
            return redirect('core:dashboard')
    
    # Today's reservations
    today_reservations = reservations.filter(reservation_date=today)
    
    # Upcoming reservations (next 10)
    upcoming_reservations = reservations.filter(
        reservation_date__gt=today
    ).order_by('reservation_date', 'reservation_time')[:10]
    
    # Available tables
    available_tables = tables.filter(is_available=True).count()
    
    # Total reservations count
    total_reservations = reservations.count()
    
    # Reservations by status
    confirmed_reservations = reservations.filter(status='confirmed').count()
    pending_reservations = reservations.filter(status='pending').count()
    cancelled_reservations = reservations.filter(status='cancelled').count()
    
    context = {
        'today_reservations': today_reservations,
        'upcoming_reservations': upcoming_reservations,
        'available_tables': available_tables,
        'is_admin': is_admin,
        'branches': branches if is_admin else [],
        'selected_branch': selected_branch,
        'total_reservations': total_reservations,
        'confirmed_reservations': confirmed_reservations,
        'pending_reservations': pending_reservations,
        'cancelled_reservations': cancelled_reservations,
    }
    
    return render(request, 'reservations/dashboard.html', context)

@login_required
def reservation_list(request):
    reservations = Reservation.objects.all().select_related('customer', 'table').order_by('-reservation_date')
    
    date_filter = request.GET.get('date')
    if date_filter:
        reservations = reservations.filter(reservation_date=date_filter)
    
    status_filter = request.GET.get('status')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    return render(request, 'reservations/reservation_list.html', {
        'reservations': reservations,
    })

@login_required
def reservation_create(request):
    customers = Customer.objects.all()
    tables = Table.objects.filter(is_available=True)
    
    # Get recent customers (last 5)
    recent_customers = Customer.objects.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        try:
            # Get form data
            customer_id = request.POST.get('customer')
            reservation_date = request.POST.get('reservation_date')
            reservation_time = request.POST.get('reservation_time')
            table_id = request.POST.get('table')
            number_of_guests = request.POST.get('number_of_guests')
            special_requests = request.POST.get('special_requests', '')
            
            # Create datetime object
            reservation_datetime = datetime.strptime(
                f"{reservation_date} {reservation_time}", 
                "%Y-%m-%d %H:%M"
            )
            
            # Check if table is available
            table = Table.objects.get(id=table_id)
            
            # Check for conflicting reservations
            conflicting_reservations = Reservation.objects.filter(
                table=table,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                status__in=['confirmed', 'pending']
            )
            
            if conflicting_reservations.exists():
                messages.error(request, 'Selected table is not available for the chosen date and time.')
                return render(request, 'reservations/reservation_create.html', {
                    'customers': customers,
                    'tables': tables,
                    'recent_customers': recent_customers,
                })
            
            # Check if number of guests exceeds table capacity
            if int(number_of_guests) > table.capacity:
                messages.error(request, f'Number of guests exceeds table capacity. Maximum capacity: {table.capacity}')
                return render(request, 'reservations/reservation_create.html', {
                    'customers': customers,
                    'tables': tables,
                    'recent_customers': recent_customers,
                })
            
            # Create reservation
            reservation = Reservation.objects.create(
                customer_id=customer_id,
                table=table,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                number_of_guests=number_of_guests,
                special_requests=special_requests,
                status='confirmed'
            )
            
            # SMS NOTIFICATION INTEGRATION - FIXED VERSION
            try:
                from notifications.services import notification_service
                
                # Get customer details for SMS
                customer = Customer.objects.get(id=customer_id)
                
                # FIX: Convert string dates to proper format for display
                # Parse the date string to datetime object for formatting
                date_obj = datetime.strptime(reservation_date, "%Y-%m-%d")
                time_obj = datetime.strptime(reservation_time, "%H:%M")
                
                formatted_date = date_obj.strftime('%B %d, %Y')
                formatted_time = time_obj.strftime('%I:%M %p')
                
                # Send reservation confirmation SMS
                notification_service.send_notification(
                    notification_type='reservation_confirm',
                    recipient={'phone': customer.phone},
                    context_data={
                        'user_name': customer.name,
                        'restaurant': 'Fine Dining Restaurant',  # Change to your actual restaurant name
                        'reservation_date': formatted_date,
                        'reservation_time': formatted_time,
                        'table_number': table.table_number,
                        'number_of_guests': number_of_guests
                    }
                )
                
                # Add SMS sent message
                messages.info(request, f'SMS confirmation sent to {customer.name}')
                
            except Exception as sms_error:
                # Log SMS error but don't break the reservation process
                print(f"SMS notification failed: {sms_error}")
                messages.warning(request, 'Reservation created but SMS notification failed')
            
            messages.success(request, f'Reservation #{reservation.id} created successfully!')
            return redirect('reservations:reservation_list')
            
        except Exception as e:
            messages.error(request, f'Error creating reservation: {str(e)}')
    
    return render(request, 'reservations/reservation_create.html', {
        'customers': customers,
        'tables': tables,
        'recent_customers': recent_customers,
    })

@login_required
@csrf_exempt
def create_customer_ajax(request):
    """AJAX view to create new customers"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer = Customer.objects.create(
                name=data['name'],
                phone=data['phone'],
                email=data.get('email', ''),
                address=data.get('address', '')
            )
            
            return JsonResponse({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def check_table_availability(request):
    """AJAX view to check table availability"""
    if request.method == 'GET':
        date = request.GET.get('date')
        time = request.GET.get('time')
        guests = request.GET.get('guests', 1)
        
        # Get all available tables
        available_tables = Table.objects.filter(is_available=True)
        
        # Filter tables that don't have conflicting reservations
        if date and time:
            conflicting_reservations = Reservation.objects.filter(
                reservation_date=date,
                reservation_time=time,
                status__in=['confirmed', 'pending']
            )
            booked_table_ids = conflicting_reservations.values_list('table_id', flat=True)
            available_tables = available_tables.exclude(id__in=booked_table_ids)
        
        # Filter by capacity if guests provided
        if guests:
            available_tables = available_tables.filter(capacity__gte=int(guests))
        
        tables_data = []
        for table in available_tables:
            tables_data.append({
                'id': table.id,
                'table_number': table.table_number,
                'capacity': table.capacity,
                'table_type': table.table_type
            })
        
        return JsonResponse({
            'success': True,
            'tables': tables_data
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def table_list(request):
    tables = Table.objects.all().order_by('table_number')
    
    # Calculate statistics
    total_tables = tables.count()
    available_tables = tables.filter(is_available=True).count()
    occupied_tables = tables.filter(is_available=False).count()
    total_capacity = sum(table.capacity for table in tables)
    
    return render(request, 'reservations/table_list.html', {
        'tables': tables,
        'total_tables': total_tables,
        'available_tables': available_tables,
        'occupied_tables': occupied_tables,
        'total_capacity': total_capacity,
    })

@login_required
def table_add(request):
    if request.method == 'POST':
        try:
            # Check if table number already exists
            table_number = request.POST['table_number']
            if Table.objects.filter(table_number=table_number).exists():
                messages.error(request, f'Table {table_number} already exists!')
                return render(request, 'reservations/table_add.html')
            
            table = Table.objects.create(
                table_number=table_number,
                table_type=request.POST['table_type'],
                capacity=request.POST['capacity'],
                location_description=request.POST.get('location_description', ''),
                is_available=True
            )
            messages.success(request, f'Table {table.table_number} added successfully!')
            return redirect('reservations:table_list')
        except Exception as e:
            messages.error(request, f'Error adding table: {str(e)}')
    
    return render(request, 'reservations/table_add.html')

@login_required
def table_edit(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.method == 'POST':
        try:
            table.table_number = request.POST['table_number']
            table.table_type = request.POST['table_type']
            table.capacity = request.POST['capacity']
            table.location_description = request.POST.get('location_description', '')
            table.is_available = 'is_available' in request.POST
            table.save()
            
            messages.success(request, f'Table {table.table_number} updated successfully!')
            return redirect('reservations:table_list')
        except Exception as e:
            messages.error(request, f'Error updating table: {str(e)}')
    
    return render(request, 'reservations/table_edit.html', {'table': table})

@login_required
def table_delete(request, pk):
    table = get_object_or_404(Table, pk=pk)
    
    if request.method == 'POST':
        table_number = table.table_number
        table.delete()
        messages.success(request, f'Table {table_number} deleted successfully!')
        return redirect('reservations:table_list')
    
    return render(request, 'reservations/table_confirm_delete.html', {'table': table})

@login_required
def table_toggle(request, pk):
    table = get_object_or_404(Table, pk=pk)
    table.is_available = not table.is_available
    table.save()
    
    status = "available" if table.is_available else "occupied"
    messages.success(request, f'Table {table.table_number} is now {status}')
    return redirect('reservations:table_list')