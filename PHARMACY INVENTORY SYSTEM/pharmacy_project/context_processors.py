from inventory.models import InventoryItem
from datetime import timedelta
from django.utils import timezone

def role_checks(request):
    if not request.user.is_authenticated:
        return {}
    
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    role_name = "Customer"
    if is_admin: role_name = "Admin"
    elif request.user.groups.filter(name='Pharmacist').exists(): role_name = "Pharmacist"
    elif request.user.groups.filter(name='Technician').exists(): role_name = "Technician"
    elif request.user.groups.filter(name='Auditor').exists(): role_name = "Auditor"

    # Global Expiry Alerts
    today = timezone.now().date()
    expiry_limit = today + timedelta(days=30)
    expiring_items_count = InventoryItem.objects.filter(expiry_date__lte=expiry_limit, expiry_date__gt=today).count()
    expired_items_count = InventoryItem.objects.filter(expiry_date__lte=today).count()

    is_pharmacist = is_admin or request.user.groups.filter(name='Pharmacist').exists()
    is_technician = is_admin or request.user.groups.filter(name='Technician').exists()
    is_auditor = is_admin or request.user.groups.filter(name='Auditor').exists()

    return {
        'is_admin': is_admin,
        'is_pharmacist': is_pharmacist,
        'is_technician': is_technician,
        'is_auditor': is_auditor,
        'has_assigned_role': is_admin or is_pharmacist or is_technician or is_auditor,
        'role_name': role_name,
        'expiring_items_count': expiring_items_count,
        'expired_items_count': expired_items_count,
    }
