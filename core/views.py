from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from orders.models import Order, Payment, OrderItem
from reservations.models import Reservation
from .models import Branch, Employee
from django.contrib import messages
from django.db import IntegrityError


@login_required
def dashboard(request):
    # ✅ Check if user is admin/superuser
    if request.user.is_superuser or request.user.is_staff:
        # Admin dashboard with system-wide statistics
        today = timezone.now().date()
        
        # System-wide statistics for admin
        total_branches = Branch.objects.filter(is_active=True).count()
        total_employees = Employee.objects.filter(is_active=True).count()
        
        # Today's statistics - show ALL data for admin
        today_orders = Order.objects.filter(created_at__date=today)
        today_sales = Payment.objects.filter(
            payment_date__date=today, 
            is_successful=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Today's revenue from orders
        today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Today's reservations
        today_reservations = Reservation.objects.filter(reservation_date=today)
        
        # Active employees count
        active_employees = Employee.objects.filter(is_active=True).count()
        
        # Recent orders (last 10)
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
        
        # Popular items today
        popular_items_today = OrderItem.objects.filter(
            order__created_at__date=today
        ).values(
            'menu_item__name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        # Upcoming reservations (next 3 days)
        upcoming_reservations = Reservation.objects.filter(
            reservation_date__range=[today, today + timedelta(days=3)]
        ).select_related('customer', 'table').order_by('reservation_date', 'reservation_time')[:5]
        
        # Get all active branches
        all_branches = Branch.objects.filter(is_active=True)
        
        # Low stock items (if inventory app is available)
        try:
            from inventory.models import Stock
            low_stock_items = Stock.get_low_stock_items()[:5]
            low_stock_count = low_stock_items.count()
        except ImportError:
            low_stock_items = []
            low_stock_count = 0
        
        context = {
            'is_admin': True,
            'total_branches': total_branches,
            'total_employees': total_employees,
            'today_orders_count': today_orders.count(),
            'today_sales': today_sales,
            'today_revenue': today_revenue,
            'pending_orders': today_orders.filter(status='pending').count(),
            'today_reservations': today_reservations.count(),
            'active_employees': active_employees,
            'recent_orders': recent_orders,
            'today_reservations_list': today_reservations,
            'popular_items_today': popular_items_today,
            'upcoming_reservations': upcoming_reservations,
            'low_stock_items': low_stock_items,
            'low_stock_count': low_stock_count,
            'branches': all_branches,
        }
        
        return render(request, 'core/admin_dashboard.html', context)
    
    # Your existing code for regular users
    # Check if user has a specific branch assigned
    user_branch = None
    if hasattr(request.user, 'employee'):
        user_branch = request.user.employee.branch
    
    # If user has a branch, redirect to branch-specific dashboard
    if user_branch:
        return redirect('core:branch_dashboard', branch_id=user_branch.id)
    
    # Admin/superuser or users without branch - show main dashboard
    today = timezone.now().date()
    
    # Get the first active branch for display
    try:
        branch = Branch.objects.filter(is_active=True).first()
        if not branch:
            # Create a default branch if none exists
            branch = Branch.objects.create(
                name="Main Branch",
                address="123 Restaurant Street, City",
                phone="+1234567890",
                email="info@restaurant.com",
                opening_time="09:00:00",
                closing_time="22:00:00",
                is_active=True
            )
    except Exception as e:
        print(f"Branch error: {e}")
        branch = None
    
    # Today's statistics - show ALL data for admin
    today_orders = Order.objects.filter(created_at__date=today)
    today_sales = Payment.objects.filter(
        payment_date__date=today, 
        is_successful=True
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Today's revenue from orders (alternative calculation)
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Today's reservations
    today_reservations = Reservation.objects.filter(reservation_date=today)
    
    # Active employees count
    active_employees = Employee.objects.filter(is_active=True).count()
    
    # Recent orders (last 10)
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    # Popular items today
    popular_items_today = OrderItem.objects.filter(
        order__created_at__date=today
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    # Upcoming reservations (next 3 days)
    upcoming_reservations = Reservation.objects.filter(
        reservation_date__range=[today, today + timedelta(days=3)]
    ).select_related('customer', 'table').order_by('reservation_date', 'reservation_time')[:5]
    
    # Employee list for the branch
    if branch:
        branch_employees = branch.employee_set.filter(is_active=True)[:5]
    else:
        branch_employees = Employee.objects.filter(is_active=True)[:5]
    
    # Low stock items (if inventory app is available)
    try:
        from inventory.models import Stock
        low_stock_items = Stock.get_low_stock_items()[:5]
        low_stock_count = low_stock_items.count()
    except ImportError:
        low_stock_items = []
        low_stock_count = 0
    
    # Get all active branches for selection
    all_branches = Branch.objects.filter(is_active=True)
    
    context = {
        'branch': branch,
        'branches': all_branches,
        'today_orders_count': today_orders.count(),
        'today_sales': today_sales,
        'today_revenue': today_revenue,
        'pending_orders': today_orders.filter(status='pending').count(),
        'today_reservations': today_reservations.count(),
        'active_employees': active_employees,
        'recent_orders': recent_orders,
        'today_reservations_list': today_reservations,
        'popular_items_today': popular_items_today,
        'upcoming_reservations': upcoming_reservations,
        'branch_employees': branch_employees,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'user_has_branch': user_branch is not None,
        'is_admin': False,  # Regular users are not admin
    }
    
    return render(request, 'core/dashboard.html', context)
@login_required
def branch_dashboard(request, branch_id):
    branch = get_object_or_404(Branch, pk=branch_id)
    
    # Check if user has access to this branch
    if hasattr(request.user, 'employee') and request.user.employee.branch != branch and not request.user.is_superuser:
        messages.error(request, "You don't have access to this branch")
        return redirect('core:dashboard')
    
    today = timezone.now().date()
    
    # Branch-specific statistics
    today_orders = Order.objects.filter(branch=branch, created_at__date=today)
    today_sales = Payment.objects.filter(
        payment_date__date=today, 
        is_successful=True,
        order__branch=branch  # Filter payments by branch
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Today's revenue from orders for this branch
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Today's reservations for this branch
    today_reservations = Reservation.objects.filter(branch=branch, reservation_date=today)
    
    # Active employees for this branch
    branch_employees = branch.employee_set.filter(is_active=True)
    active_employees = branch_employees.count()
    
    # Recent orders for this branch (last 10)
    recent_orders = Order.objects.filter(branch=branch).select_related('customer').order_by('-created_at')[:10]
    
    # Popular items today for this branch
    popular_items_today = OrderItem.objects.filter(
        order__branch=branch,
        order__created_at__date=today
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    # Upcoming reservations for this branch (next 3 days)
    upcoming_reservations = Reservation.objects.filter(
        branch=branch,
        reservation_date__range=[today, today + timedelta(days=3)]
    ).select_related('customer', 'table').order_by('reservation_date', 'reservation_time')[:5]
    
    # Low stock items (if inventory app is available) - you might want to filter by branch too
    try:
        from inventory.models import Stock
        low_stock_items = Stock.get_low_stock_items()[:5]
        low_stock_count = low_stock_items.count()
    except ImportError:
        low_stock_items = []
        low_stock_count = 0
    
    context = {
        'branch': branch,
        'today_orders_count': today_orders.count(),
        'today_sales': today_sales,
        'today_revenue': today_revenue,
        'pending_orders': today_orders.filter(status='pending').count(),
        'today_reservations': today_reservations.count(),
        'active_employees': active_employees,
        'recent_orders': recent_orders,
        'today_reservations_list': today_reservations,
        'popular_items_today': popular_items_today,
        'upcoming_reservations': upcoming_reservations,
        'branch_employees': branch_employees,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'user_has_branch': True,
    }
    
    return render(request, 'core/branch_dashboard.html', context)

@login_required
def branch_list(request):
    # If user has a specific branch, only show that branch (unless they're admin)
    if hasattr(request.user, 'employee') and request.user.employee.branch and not (request.user.is_superuser or request.user.is_staff):
        user_branch = request.user.employee.branch
        return redirect('core:branch_detail', pk=user_branch.id)
    
    # Admin/superuser sees all branches
    branches = Branch.objects.filter(is_active=True)
    
    return render(request, 'core/branch_list.html', {
        'branches': branches,
        'is_admin': request.user.is_superuser or request.user.is_staff,  # ✅ Add this line
    })

@login_required
def branch_detail(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    
    # Check if user has access to this branch
    if hasattr(request.user, 'employee') and request.user.employee.branch != branch and not request.user.is_superuser:
        messages.error(request, "You don't have access to this branch")
        return redirect('core:dashboard')
    
    # Branch statistics
    today = timezone.now().date()
    today_orders = Order.objects.filter(
        branch=branch,
        created_at__date=today
    )
    
    today_reservations = Reservation.objects.filter(
        branch=branch,
        reservation_date=today
    )
    
    employees = branch.employee_set.filter(is_active=True)
    
    # Calculate today's revenue
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Weekly revenue trend
    week_ago = today - timedelta(days=7)
    weekly_orders = Order.objects.filter(
        branch=branch,
        created_at__date__gte=week_ago
    )
    weekly_revenue = weekly_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Popular items at this branch
    popular_items = OrderItem.objects.filter(
        order__branch=branch,
        order__created_at__date__gte=week_ago
    ).values(
        'menu_item__name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    return render(request, 'core/branch_detail.html', {
        'branch': branch,
        'today_orders': today_orders,
        'today_reservations': today_reservations,
        'employees': employees,
        'today_revenue': today_revenue,
        'weekly_revenue': weekly_revenue,
        'popular_items': popular_items,
    })

@login_required
def branch_add(request):
    # Only superusers can add branches
    if not request.user.is_superuser:
        messages.error(request, "Only administrators can add new branches")
        return redirect('core:branch_list')
    
    if request.method == 'POST':
        try:
            branch = Branch.objects.create(
                name=request.POST['name'],
                address=request.POST['address'],
                phone=request.POST['phone'],
                email=request.POST['email'],
                opening_time=request.POST['opening_time'],
                closing_time=request.POST['closing_time'],
                is_active=True
            )
            messages.success(request, f'Branch "{branch.name}" added successfully!')
            return redirect('core:branch_list')
        except Exception as e:
            messages.error(request, f'Error adding branch: {str(e)}')
    
    return render(request, 'core/branch_add.html')

@login_required
def branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    
    # Check if user has permission to edit this branch
    if (hasattr(request.user, 'employee') and 
        request.user.employee.branch != branch and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to edit this branch")
        return redirect('core:branch_list')
    
    if request.method == 'POST':
        try:
            branch.name = request.POST['name']
            branch.address = request.POST['address']
            branch.phone = request.POST['phone']
            branch.email = request.POST['email']
            branch.opening_time = request.POST['opening_time']
            branch.closing_time = request.POST['closing_time']
            branch.is_active = 'is_active' in request.POST
            branch.save()
            
            messages.success(request, f'Branch "{branch.name}" updated successfully!')
            return redirect('core:branch_list')
        except Exception as e:
            messages.error(request, f'Error updating branch: {str(e)}')
    
    return render(request, 'core/branch_edit.html', {'branch': branch})

@login_required
def employee_list(request):
    # ✅ Check if user is admin/superuser - show ALL employees
    if request.user.is_superuser or request.user.is_staff:
        employees = Employee.objects.all().select_related('user', 'branch')
        manager_branch = None
        is_admin = True
    else:
        # Regular manager - only show their branch employees
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            manager_branch = manager_employee.branch
            employees = Employee.objects.filter(branch=manager_branch).select_related('user', 'branch')
            is_admin = False
        except Employee.DoesNotExist:
            messages.error(request, "You are not assigned as a manager.")
            return redirect('core:dashboard')
    
    # Statistics - these will work for both admin and manager
    total_employees = employees.count()
    active_employees = employees.filter(is_active=True).count()
    waiters = employees.filter(employee_type='waiter').count()
    chefs = employees.filter(employee_type='chef').count()
    cashiers = employees.filter(employee_type='cashier').count()
    cleaners = employees.filter(employee_type='cleaner').count()
    managers = employees.filter(employee_type='manager').count()
    
    return render(request, 'core/employee_list.html', {
        'employees': employees,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'waiters': waiters,
        'chefs': chefs,
        'cashiers': cashiers,
        'cleaners': cleaners,
        'managers': managers,
        'manager_branch': manager_branch,
        'is_admin': is_admin,  # ✅ Pass this to template
    })

@login_required
def employee_add(request):
    branches = Branch.objects.filter(is_active=True)
    
    # ✅ Check if user is admin/superuser
    if request.user.is_superuser or request.user.is_staff:
        is_admin = True
        manager_branch = None
    else:
        # Regular manager
        is_admin = False
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            manager_branch = manager_employee.branch
        except Employee.DoesNotExist:
            messages.error(request, "Only managers can add employees.")
            return redirect('core:employee_list')
    
    if request.method == 'POST':
        try:
            # Create user account first
            username = request.POST['username']
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists!')
                return render(request, 'core/employee_add.html', {
                    'branches': branches,
                    'is_admin': is_admin,
                    'manager_branch': manager_branch
                })
            
            user = User.objects.create_user(
                username=username,
                password=request.POST['password'],
                email=request.POST.get('email', ''),
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )
            
            # ✅ Determine which branch to assign
            if is_admin:
                # Admin can choose any branch
                branch_id = request.POST.get('branch')
                if branch_id:
                    branch = Branch.objects.get(id=branch_id)
                else:
                    branch = None
            else:
                # Regular manager auto-assigns to their branch
                branch = manager_branch
            
            # Create employee record
            employee = Employee.objects.create(
                user=user,
                employee_id=request.POST['employee_id'],
                employee_type=request.POST['employee_type'],
                phone=request.POST['phone'],
                address=request.POST['address'],
                salary=request.POST['salary'],
                branch=branch,
                is_active=True
            )
            
            messages.success(request, f'Employee {user.get_full_name()} added successfully!')
            return redirect('core:employee_list')
            
        except Exception as e:
            messages.error(request, f'Error adding employee: {str(e)}')
    
    return render(request, 'core/employee_add.html', {
        'branches': branches,
        'is_admin': is_admin,
        'manager_branch': manager_branch
    })
@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            # Update user account
            user = employee.user
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST.get('email', '')
            if request.POST.get('password'):
                user.set_password(request.POST['password'])
            user.save()
            
            # Update employee record
            employee.employee_type = request.POST['employee_type']
            employee.phone = request.POST['phone']
            employee.address = request.POST['address']
            employee.salary = request.POST['salary']
            employee.branch_id = request.POST['branch']
            employee.is_active = 'is_active' in request.POST
            employee.save()
            
            messages.success(request, f'Employee {user.get_full_name()} updated successfully!')
            return redirect('core:employee_list')
            
        except Exception as e:
            messages.error(request, f'Error updating employee: {str(e)}')
    
    return render(request, 'core/employee_edit.html', {
        'employee': employee,
        'branches': branches,
    })

@login_required
def employee_toggle(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = not employee.is_active
    employee.save()
    
    status = "activated" if employee.is_active else "deactivated"
    messages.success(request, f'Employee {employee.user.get_full_name()} has been {status}')
    return redirect('core:employee_list')

@login_required
def admin_branch_dashboard(request, branch_id):
    """Admin access to manage a specific branch like a manager"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Only administrators can access branch management.")
        return redirect('core:dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    today = timezone.now().date()
    
    # Get branch-specific data (similar to manager dashboard)
    employees = branch.employee_set.filter(is_active=True)
    today_orders = Order.objects.filter(branch=branch, created_at__date=today)
    today_reservations = Reservation.objects.filter(branch=branch, reservation_date=today)
    
    # Revenue calculations
    today_sales = Payment.objects.filter(
        order__branch=branch,
        payment_date__date=today, 
        is_successful=True
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent orders (last 10)
    recent_orders = Order.objects.filter(branch=branch).select_related('customer').order_by('-created_at')[:10]
    
    # Popular items today
    popular_items_today = OrderItem.objects.filter(
        order__branch=branch,
        order__created_at__date=today
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    # Upcoming reservations (next 3 days)
    upcoming_reservations = Reservation.objects.filter(
        branch=branch,
        reservation_date__range=[today, today + timedelta(days=3)]
    ).select_related('customer', 'table').order_by('reservation_date', 'reservation_time')[:5]
    
    context = {
        'branch': branch,
        'employees': employees,
        'today_orders_count': today_orders.count(),
        'today_sales': today_sales,
        'today_revenue': today_revenue,
        'pending_orders': today_orders.filter(status='pending').count(),
        'today_reservations': today_reservations.count(),
        'active_employees': employees.count(),
        'recent_orders': recent_orders,
        'today_reservations_list': today_reservations,
        'popular_items_today': popular_items_today,
        'upcoming_reservations': upcoming_reservations,
        'is_admin': True,
        'admin_branch_access': True,  # Flag to show this is admin accessing branch
    }
    
    return render(request, 'core/admin_branch_dashboard.html', context)

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Check permissions
    if not (request.user.is_superuser or request.user.is_staff):
        # Regular managers can only delete employees from their branch
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            if employee.branch != manager_employee.branch:
                messages.error(request, "You can only delete employees from your own branch.")
                return redirect('core:employee_list')
        except Employee.DoesNotExist:
            messages.error(request, "You don't have permission to delete employees.")
            return redirect('core:employee_list')
    
    if request.method == 'POST':
        employee_name = employee.user.get_full_name()
        employee.delete()
        messages.success(request, f'Employee {employee_name} has been deleted successfully.')
        return redirect('core:employee_list')
    
    return render(request, 'core/employee_delete.html', {
        'employee': employee,
    })



def home(request):
    """Home page for Maama Joan Restaurant"""
    context = {
        'restaurant_name': "Maama Joan Restaurant",
        'tagline': "Authentic Ugandan Cuisine & Hospitality",
        'contact_info': {
            'phone': '+256 702 087 693',
            'email': 'info@maamajoan.com',
            'address': 'Kampala, Uganda',
            'hours': 'Mon-Sun: 7:00 AM - 10:00 PM'
        },
        'services': [
            'Traditional Ugandan Dishes',
            'Catering Services',
            'Event Hosting',
            'Takeaway & Delivery',
            'Private Dining'
        ]
    }
    return render(request, 'core/home.html', context)

def root_redirect(request):
    """Redirect root URL based on authentication"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')  # Go to management dashboard
    else:
        return redirect('core:home')       # Go to public home page



