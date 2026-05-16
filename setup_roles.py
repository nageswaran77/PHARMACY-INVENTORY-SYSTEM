import os
import django

def setup_roles():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_project.settings')
    django.setup()

    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from inventory.models import InventoryItem, AuditLog

    # Define Roles
    roles = {
        'Admin': {
            'permissions': ['add_inventoryitem', 'change_inventoryitem', 'delete_inventoryitem', 'view_inventoryitem', 'can_dispense', 'view_auditlog'],
        },
        'Pharmacist': {
            'permissions': ['view_inventoryitem', 'can_dispense'],
        },
        'Technician': {
            'permissions': ['view_inventoryitem', 'change_inventoryitem'], # Can update stock but not dispense depending on your logic
        },
        'Auditor': {
            'permissions': ['view_inventoryitem', 'view_auditlog'],
        }
    }

    for role_name, data in roles.items():
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            print(f"Created group: {role_name}")
        
        # Clear existing permissions to sync
        group.permissions.clear()
        
        for perm_codename in data['permissions']:
            try:
                # Most permissions are under inventory app
                perm = Permission.objects.get(codename=perm_codename)
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"Warning: Permission {perm_codename} not found")

    print("Successfully set up pharmacy roles and permissions.")

if __name__ == '__main__':
    setup_roles()
