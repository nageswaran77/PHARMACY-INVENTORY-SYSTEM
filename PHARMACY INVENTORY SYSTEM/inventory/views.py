from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F
from .models import InventoryItem, SaleRecord, Alert, AuditLog, CustomerOrder
from .forms import StockForm, MedicationForm, PaymentForm
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

# Roles logic
def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_pharmacist_or_admin(user):
    return is_admin(user) or user.groups.filter(name='Pharmacist').exists()

def is_technician_or_admin(user):
    return is_admin(user) or user.groups.filter(name='Technician').exists()

def is_auditor_or_admin(user):
    return is_admin(user) or user.groups.filter(name='Auditor').exists()

@login_required
def inventory_list(request):
    items = InventoryItem.objects.all()
    query = request.GET.get('q')
    if query:
        items = items.filter(name__icontains=query)
    
    # Calculate revenue if Auditor/Admin
    revenue = 0
    if is_auditor_or_admin(request.user):
        revenue = SaleRecord.objects.aggregate(total=Sum('total_price'))['total'] or 0.00
        
    # Check if user has NO roles (customer/non-role)
    has_no_role = not (is_admin(request.user) or 
                       request.user.groups.filter(name__in=['Pharmacist', 'Technician', 'Auditor']).exists())

    # Expiry alert: Find items expiring in <= 30 days
    today = timezone.now().date()
    expiry_limit = today + timedelta(days=30)
    expiring_items_count = items.filter(expiry_date__lte=expiry_limit, expiry_date__gt=today).count()
    expired_items_count = items.filter(expiry_date__lte=today).count()

    # Check if user has roles for messages
    is_staff_user = is_admin(request.user) or request.user.groups.filter(name__in=['Pharmacist', 'Technician', 'Auditor']).exists()

    if is_staff_user:
        if expiring_items_count > 0:
            messages.warning(request, f"Alert: {expiring_items_count} tablet(s) are expiring within 30 days!")
        if expired_items_count > 0:
            messages.error(request, f"Alert: {expired_items_count} tablet(s) have already EXPIRED!")

    return render(request, 'inventory/list.html', {
        'items': items,
        'revenue': revenue,
        'has_no_role': has_no_role,
        'is_admin': is_admin(request.user),
        'is_technician': is_technician_or_admin(request.user),
        'is_auditor': is_auditor_or_admin(request.user),
        'is_pharmacist': is_pharmacist_or_admin(request.user),
    })

@login_required
def buy_medication(request, pk):
    """Payment page for regular users."""
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.item = item
            order.unit_price = item.unit_price
            
            if item.quantity >= order.quantity:
                # Deduct stock
                item.quantity -= order.quantity
                item.save()
                order.save()
                
                # Record as a sale for the auditor to see too
                SaleRecord.objects.create(
                    item=item,
                    quantity=order.quantity,
                    unit_price_at_sale=item.unit_price,
                    user=request.user
                )
                
                AuditLog.objects.create(user=request.user, action='BUY', details=f"Customer Buy: {order.quantity} of {item.sku}")
                return redirect('view_bill', order_id=order.id)
            else:
                messages.error(request, f"Sorry, only {item.quantity} available in stock.")
    else:
        form = PaymentForm()
    
    return render(request, 'inventory/payment.html', {
        'form': form, 
        'item': item,
        'title': 'Secure Payment Gateway'
    })

@login_required
def view_bill(request, order_id):
    order = get_object_or_404(CustomerOrder, id=order_id)
    return render(request, 'inventory/bill.html', {'order': order})

@login_required
@user_passes_test(is_technician_or_admin)
def add_medication(request):
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            item = form.save()
            AuditLog.objects.create(user=request.user, action='ADD_ITEM', details=f"Created new medication: {item.name}")
            messages.success(request, f"Successfully added {item.name} to the system.")
            return redirect('inventory_list')
    else:
        form = MedicationForm()
    return render(request, 'inventory/form.html', {'form': form, 'title': 'Register New Medication'})

@login_required
@user_passes_test(is_technician_or_admin)
def edit_medication(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(user=request.user, action='EDIT_ITEM', details=f"Edited medication details: {item.name}")
            messages.success(request, f"Successfully updated {item.name}.")
            return redirect('inventory_list')
    else:
        form = MedicationForm(instance=item)
    return render(request, 'inventory/form.html', {'form': form, 'item': item, 'title': f'Edit Medication: {item.name}'})

@login_required
@user_passes_test(is_technician_or_admin)
def add_stock(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            item.quantity += qty
            item.save()
            AuditLog.objects.create(user=request.user, action='ADD_STOCK', details=f"Added {qty} to {item.sku}")
            messages.success(request, f"Added stock to {item.name}")
            return redirect('inventory_list')
    else:
        form = StockForm()
    return render(request, 'inventory/form.html', {'form': form, 'item': item, 'title': 'Add Stock'})

@login_required
@user_passes_test(is_pharmacist_or_admin)
def dispense(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            if item.quantity >= qty:
                item.quantity -= qty
                item.save()
                SaleRecord.objects.create(item=item, quantity=qty, unit_price_at_sale=item.unit_price, user=request.user)
                if item.is_low():
                    Alert.objects.create(item=item, message=f"Low stock: {item.name}")
                messages.success(request, f"Dispensed {qty} units.")
                return redirect('inventory_list')
            else:
                messages.error(request, "Insufficient stock.")
    else:
        form = StockForm()
    return render(request, 'inventory/form.html', {'form': form, 'item': item, 'title': 'Dispense Medication'})

@login_required
@user_passes_test(is_auditor_or_admin)
def sales_dashboard(request):
    sales = SaleRecord.objects.all().select_related('item').order_by('-date')
    total_revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0.00
    return render(request, 'inventory/sales.html', {'sales': sales, 'total_revenue': total_revenue})

@login_required
@user_passes_test(is_pharmacist_or_admin)
def predict_restock(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    last_30_days = timezone.now() - timedelta(days=30)
    sales = SaleRecord.objects.filter(item=item, date__gte=last_30_days)
    total_used = sum(s.quantity for s in sales)
    avg_daily = total_used / 30
    return render(request, 'inventory/predict.html', {'item': item, 'needed': int(avg_daily * 7)})

@login_required
def alerts_list(request):
    # Existing alerts from the database
    db_alerts = Alert.objects.filter(resolved=False).order_by('-created_at')
    
    # Dynamic alerts for stock <= 50
    low_stock_items = InventoryItem.objects.filter(quantity__lte=50)
    
    # Dynamic alerts for expiring items (<= 30 days)
    today = timezone.now().date()
    expiry_limit = today + timedelta(days=30)
    expiring_items = InventoryItem.objects.filter(expiry_date__lte=expiry_limit, expiry_date__gt=today)
    expired_items = InventoryItem.objects.filter(expiry_date__lte=today)
    
    return render(request, 'inventory/alerts.html', {
        'alerts': db_alerts,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'expired_items': expired_items,
    })

@login_required
@user_passes_test(is_auditor_or_admin)
def audit_log(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'inventory/audit.html', {'logs': logs})