from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import MenuItem, Stock, FoodCategory
from django.contrib import messages
from django.db.models import Sum, F
from core.models import Branch, Employee
from .forms import MenuItemForm

@login_required
def inventory_dashboard(request):
    # Get selected branch from query parameters
    branch_id = request.GET.get('branch')
    selected_branch = None
    
    # Check if user is admin
    is_admin = request.user.is_superuser or request.user.is_staff
    
    if is_admin:
        # Admin can view any branch's inventory
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            selected_branch = get_object_or_404(Branch, id=branch_id)
            # Filter data for selected branch
            stock_items = Stock.objects.filter(branch=selected_branch)
            menu_items = MenuItem.objects.filter(is_available=True)
        else:
            # Show all inventory for admin (system-wide)
            stock_items = Stock.objects.all()
            menu_items = MenuItem.objects.filter(is_available=True)
    else:
        # Regular manager - only their branch
        try:
            manager_employee = Employee.objects.get(user=request.user, employee_type='manager')
            selected_branch = manager_employee.branch
            branches = Branch.objects.filter(id=selected_branch.id)
            stock_items = Stock.objects.filter(branch=selected_branch)
            menu_items = MenuItem.objects.filter(is_available=True)
        except Employee.DoesNotExist:
            messages.error(request, "You are not authorized to view inventory.")
            return redirect('core:dashboard')
    
    # FIX: Use the class method for efficient database query
    low_stock_items = Stock.get_low_stock_items()
    
    # Apply branch filtering to low stock items if a branch is selected
    if selected_branch:
        low_stock_items = low_stock_items.filter(branch=selected_branch)
    
    categories = FoodCategory.objects.filter(is_active=True)
    
    # Calculate inventory statistics - FIXED: Use ingredient__unit_price
    total_items = stock_items.count()
    
    # FIX: Check if unit_price exists in Ingredient model before using it
    try:
        total_value = stock_items.aggregate(
            total=Sum(F('quantity') * F('ingredient__unit_price'))
        )['total'] or 0
    except Exception as e:
        print(f"Error calculating total value: {e}")
        total_value = 0
    
    # Out of stock items
    out_of_stock_items = stock_items.filter(quantity=0)
    
    # Items needing reorder (below alert level) - FIXED: Use alert_level instead of minimum_stock
    reorder_items = stock_items.filter(quantity__lte=F('alert_level'))
    
    context = {
        'menu_items_count': menu_items.count(),
        'low_stock_count': low_stock_items.count(),
        'categories': categories,
        'low_stock_items': low_stock_items,
        'is_admin': is_admin,
        'branches': branches if is_admin else [],
        'selected_branch': selected_branch,
        'total_items': total_items,
        'total_value': total_value,
        'out_of_stock_count': out_of_stock_items.count(),
        'reorder_count': reorder_items.count(),
        'stock_items': stock_items,
    }
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
def menu_list(request):
    # Get all menu items with category and image data
    menu_items = MenuItem.objects.all().select_related('category')
    
    # Apply existing filters
    category_filter = request.GET.get('category')
    if category_filter:
        menu_items = menu_items.filter(category_id=category_filter)
    
    available_filter = request.GET.get('available')
    if available_filter == 'true':
        menu_items = menu_items.filter(is_available=True)
    elif available_filter == 'false':
        menu_items = menu_items.filter(is_available=False)
    
    # Add new item_type filter
    item_type_filter = request.GET.get('item_type')
    if item_type_filter:
        menu_items = menu_items.filter(item_type=item_type_filter)
    
    # Get categories for filter dropdown
    categories = FoodCategory.objects.all()
    
    # Calculate statistics for the dashboard
    total_items = MenuItem.objects.count()
    available_items = MenuItem.objects.filter(is_available=True).count()
    combo_items = MenuItem.objects.filter(item_type='combo').count()
    custom_items = MenuItem.objects.filter(item_type__in=['base', 'source']).count()
    
    # Add profit margin calculation to each item
    for item in menu_items:
        item.profit_margin = item.actual_price - item.cost_price
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'total_items': total_items,
        'available_items': available_items,
        'combo_items': combo_items,
        'custom_items': custom_items,
    }
    
    return render(request, 'inventory/menu_list.html', context)

@login_required
def stock_list(request):
    # FIX: Use the efficient method for low stock filtering
    low_stock_filter = request.GET.get('low_stock')
    
    if low_stock_filter == 'true':
        stock_items = Stock.get_low_stock_items().select_related('ingredient')
    else:
        stock_items = Stock.objects.all().select_related('ingredient')
    
    return render(request, 'inventory/stock_list.html', {
        'stock_items': stock_items,
    })

@login_required
def category_list(request):
    categories = FoodCategory.objects.all()
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
    })

#view management

def is_manager(user):
    return user.groups.filter(name='Manager').exists() or user.is_staff

@login_required
@user_passes_test(is_manager)
def menu_item_list(request):
    menu_items = MenuItem.objects.all().select_related('category')
    return render(request, 'inventory/menu_item_list.html', {
        'menu_items': menu_items
    })

@login_required
@user_passes_test(is_manager)
def menu_item_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save()
            messages.success(request, f'Menu item "{menu_item.name}" created successfully!')
            return redirect('inventory:menu_item_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MenuItemForm()
    
    return render(request, 'inventory/menu_item_form.html', {
        'form': form,
        'title': 'Add New Menu Item'
    })

@login_required
@user_passes_test(is_manager)
def menu_item_edit(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            menu_item = form.save()
            messages.success(request, f'Menu item "{menu_item.name}" updated successfully!')
            return redirect('inventory:menu_item_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MenuItemForm(instance=menu_item)
    
    return render(request, 'inventory/menu_item_form.html', {
        'form': form,
        'title': f'Edit {menu_item.name}',
        'menu_item': menu_item
    })

@login_required
@user_passes_test(is_manager)
def menu_item_delete(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        menu_item_name = menu_item.name
        menu_item.delete()
        messages.success(request, f'Menu item "{menu_item_name}" deleted successfully!')
        return redirect('inventory:menu_item_list')
    
    return render(request, 'inventory/menu_item_confirm_delete.html', {
        'menu_item': menu_item
    })