# inventory/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventory.models import InventoryItem, AuditLog

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        pharmacist_group, _ = Group.objects.get_or_create(name='Pharmacist')
        tech_group, _ = Group.objects.get_or_create(name='Technician')
        auditor_group, _ = Group.objects.get_or_create(name='Auditor')

        # Get content types for models we need permissions on
        item_ct = ContentType.objects.get_for_model(InventoryItem)
        log_ct = ContentType.objects.get_for_model(AuditLog)

        # Define permissions (you can also create custom ones)
        perms = {
            'add_inventoryitem': Permission.objects.get(content_type=item_ct, codename='add_inventoryitem'),
            'change_inventoryitem': Permission.objects.get(content_type=item_ct, codename='change_inventoryitem'),
            'delete_inventoryitem': Permission.objects.get(content_type=item_ct, codename='delete_inventoryitem'),
            'view_inventoryitem': Permission.objects.get(content_type=item_ct, codename='view_inventoryitem'),
            'view_auditlog': Permission.objects.get(content_type=log_ct, codename='view_auditlog'),
        }
        # Add custom permissions if needed (e.g., 'dispense')
        # You can create them in model Meta and then fetch

        # Assign permissions to groups
        admin_group.permissions.set(perms.values())
        pharmacist_group.permissions.set([perms['view_inventoryitem'], perms['change_inventoryitem']])  # etc.
        tech_group.permissions.set([perms['view_inventoryitem']])
        auditor_group.permissions.set([perms['view_inventoryitem'], perms['view_auditlog']])

        self.stdout.write("Roles and permissions set up.")