import datetime
import hashlib
from collections import defaultdict
from typing import List, Dict, Optional

# ----------------------------------------------------------------------
# RBAC Components
# ----------------------------------------------------------------------
class Permission:
    """A named permission (e.g., 'add_stock', 'view_audit')."""
    def __init__(self, name: str):
        self.name = name

class Role:
    """A role with a set of permissions."""
    def __init__(self, name: str, permissions: List[Permission] = None):
        self.name = name
        self.permissions = permissions or []

    def has_permission(self, perm_name: str) -> bool:
        return any(p.name == perm_name for p in self.permissions)

class User:
    """A system user with a role."""
    def __init__(self, username: str, role: Role):
        self.username = username
        self.role = role

    def can(self, perm_name: str) -> bool:
        return self.role.has_permission(perm_name)

# ----------------------------------------------------------------------
# Transaction Logging (Audit Trail)
# ----------------------------------------------------------------------
class AuditLog:
    """Simple audit trail – logs every action to a list."""
    def __init__(self):
        self.entries = []

    def log(self, user: User, action: str, details: str):
        timestamp = datetime.datetime.now().isoformat()
        entry = {
            'timestamp': timestamp,
            'user': user.username,
            'role': user.role.name,
            'action': action,
            'details': details,
            'hash': self._hash_entry(timestamp, user.username, action, details)
        }
        self.entries.append(entry)
        print(f"[AUDIT] {entry}")  # also print for demo

    def _hash_entry(self, timestamp, user, action, details) -> str:
        # Simple hash to ensure integrity (tamper‑evident)
        raw = f"{timestamp}{user}{action}{details}"
        return hashlib.sha256(raw.encode()).hexdigest()[:8]

    def get_audit_trail(self):
        return self.entries

# ----------------------------------------------------------------------
# Inventory Items and Alerts
# ----------------------------------------------------------------------
class InventoryItem:
    """Represents a medication in the pharmacy."""
    def __init__(self, sku: str, name: str, quantity: int, reorder_level: int, reorder_qty: int):
        self.sku = sku
        self.name = name
        self.quantity = quantity
        self.reorder_level = reorder_level   # threshold for low‑stock alert
        self.reorder_qty = reorder_qty       # amount to order when restocking
        self.usage_history = []               # track dispenses for prediction

    def add_stock(self, qty: int):
        self.quantity += qty

    def remove_stock(self, qty: int) -> bool:
        if self.quantity >= qty:
            self.quantity -= qty
            self.usage_history.append((datetime.date.today(), qty))
            return True
        return False

    def is_low(self) -> bool:
        return self.quantity <= self.reorder_level

    def predict_needed(self, days: int = 7) -> int:
        """Simple moving average of past usage to predict future need."""
        if not self.usage_history:
            return 0
        # average daily usage over last 30 days (or all if less)
        recent = [qty for (date, qty) in self.usage_history[-30:]]
        avg_daily = sum(recent) / max(len(recent), 1)
        return int(avg_daily * days)

class Alert:
    """Represents a low‑stock alert."""
    def __init__(self, item: InventoryItem):
        self.item = item
        self.timestamp = datetime.datetime.now()
        self.message = f"Low stock: {item.name} (SKU: {item.sku}) - only {item.quantity} left."

# ----------------------------------------------------------------------
# Main Inventory System
# ----------------------------------------------------------------------
class PharmacyInventorySystem:
    """Encapsulates the entire system."""
    def __init__(self):
        self.items: Dict[str, InventoryItem] = {}   # SKU -> Item
        self.alerts: List[Alert] = []
        self.audit_log = AuditLog()

    # ---------- Permission‑protected actions ----------
    def add_item(self, user: User, item: InventoryItem):
        if not user.can("add_item"):
            raise PermissionError(f"User {user.username} cannot add items.")
        self.items[item.sku] = item
        self.audit_log.log(user, "ADD_ITEM", f"Added {item.name} (SKU: {item.sku})")

    def remove_item(self, user: User, sku: str):
        if not user.can("remove_item"):
            raise PermissionError(f"User {user.username} cannot remove items.")
        if sku in self.items:
            del self.items[sku]
            self.audit_log.log(user, "REMOVE_ITEM", f"Removed SKU {sku}")

    def add_stock(self, user: User, sku: str, qty: int):
        if not user.can("add_stock"):
            raise PermissionError(f"User {user.username} cannot add stock.")
        if sku in self.items:
            self.items[sku].add_stock(qty)
            self.audit_log.log(user, "ADD_STOCK", f"Added {qty} to {sku}")
        else:
            raise ValueError(f"Item {sku} not found.")

    def dispense(self, user: User, sku: str, qty: int):
        if not user.can("dispense"):
            raise PermissionError(f"User {user.username} cannot dispense medication.")
        if sku not in self.items:
            raise ValueError(f"Item {sku} not found.")
        success = self.items[sku].remove_stock(qty)
        if success:
            self.audit_log.log(user, "DISPENSE", f"Dispensed {qty} of {sku}")
            # Check for low stock after dispensing
            if self.items[sku].is_low():
                alert = Alert(self.items[sku])
                self.alerts.append(alert)
                print(f"[ALERT] {alert.message}")
        else:
            raise ValueError(f"Insufficient stock for {sku} (requested {qty}, available {self.items[sku].quantity}).")

    def view_inventory(self, user: User):
        if not user.can("view_inventory"):
            raise PermissionError(f"User {user.username} cannot view inventory.")
        self.audit_log.log(user, "VIEW_INVENTORY", "Viewed inventory list")
        return self.items

    def view_alerts(self, user: User):
        if not user.can("view_alerts"):
            raise PermissionError(f"User {user.username} cannot view alerts.")
        self.audit_log.log(user, "VIEW_ALERTS", "Viewed alerts")
        return self.alerts

    def predict_restock(self, user: User, sku: str, days_ahead: int = 7):
        if not user.can("predict"):
            raise PermissionError(f"User {user.username} cannot run predictions.")
        if sku not in self.items:
            raise ValueError(f"Item {sku} not found.")
        needed = self.items[sku].predict_needed(days_ahead)
        self.audit_log.log(user, "PREDICT", f"Predicted need for {sku}: {needed} in {days_ahead} days")
        return needed

    # ---------- Helper to generate a restock recommendation ----------
    def recommend_restock(self, user: User):
        if not user.can("view_reports"):
            raise PermissionError(f"User {user.username} cannot view reports.")
        recommendations = []
        for sku, item in self.items.items():
            if item.is_low():
                # Recommend ordering the reorder quantity
                recommendations.append((sku, item.name, item.reorder_qty))
        self.audit_log.log(user, "RESTOCK_RECOMMENDATION", f"Generated {len(recommendations)} recommendations")
        return recommendations

# ----------------------------------------------------------------------
# Setup: Define roles and permissions
# ----------------------------------------------------------------------
# Permissions
perm_add_item = Permission("add_item")
perm_remove_item = Permission("remove_item")
perm_add_stock = Permission("add_stock")
perm_dispense = Permission("dispense")
perm_view_inventory = Permission("view_inventory")
perm_view_alerts = Permission("view_alerts")
perm_predict = Permission("predict")
perm_view_reports = Permission("view_reports")
perm_view_audit = Permission("view_audit")

# Roles
admin_role = Role("Admin", permissions=[
    perm_add_item, perm_remove_item, perm_add_stock, perm_dispense,
    perm_view_inventory, perm_view_alerts, perm_predict, perm_view_reports,
    perm_view_audit
])
pharmacist_role = Role("Pharmacist", permissions=[
    perm_dispense, perm_view_inventory, perm_view_alerts, perm_predict,
    perm_view_reports
])
technician_role = Role("Technician", permissions=[
    perm_add_stock, perm_view_inventory, perm_view_alerts
])
auditor_role = Role("Auditor", permissions=[
    perm_view_inventory, perm_view_audit, perm_view_reports
])

# Users
admin_user = User("alice", admin_role)
pharmacist_user = User("bob", pharmacist_role)
tech_user = User("charlie", technician_role)
auditor_user = User("diana", auditor_role)

# ----------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------
if __name__ == "__main__":
    system = PharmacyInventorySystem()

    # Admin adds items
    print("=== Admin adds items ===")
    item1 = InventoryItem("MED001", "Paracetamol 500mg", 150, reorder_level=50, reorder_qty=200)
    item2 = InventoryItem("MED002", "Amoxicillin 250mg", 30, reorder_level=40, reorder_qty=100)
    system.add_item(admin_user, item1)
    system.add_item(admin_user, item2)

    # Technician adds stock (allowed)
    print("\n=== Technician adds stock ===")
    system.add_stock(tech_user, "MED002", 20)   # now total 50

    # Pharmacist dispenses (allowed)
    print("\n=== Pharmacist dispenses ===")
    system.dispense(pharmacist_user, "MED001", 20)   # Paracetamol now 130
    system.dispense(pharmacist_user, "MED002", 15)   # Amoxicillin now 35 -> low stock (below 40)
    # Low stock alert should trigger automatically

    # View alerts (technician can view)
    print("\n=== Technician views alerts ===")
    alerts = system.view_alerts(tech_user)
    for alert in alerts:
        print(f"  - {alert.message}")

    # Pharmacist runs prediction for a drug
    print("\n=== Pharmacist predicts need ===")
    needed = system.predict_restock(pharmacist_user, "MED001", days_ahead=7)
    print(f"Predicted need for MED001 in next 7 days: {needed} units")

    # Generate restock recommendations (pharmacist can)
    print("\n=== Restock recommendations ===")
    recs = system.recommend_restock(pharmacist_user)
    for sku, name, qty in recs:
        print(f"Recommend ordering {qty} of {name} (SKU: {sku})")

    # Auditor views audit trail
    print("\n=== Auditor views audit log ===")
    log_entries = system.audit_log.get_audit_trail()
    for entry in log_entries[-5:]:  # last 5 entries
        print(f"{entry['timestamp']} | {entry['user']} ({entry['role']}) | {entry['action']} | {entry['details']} | hash: {entry['hash']}")

    # Attempt a forbidden action: technician trying to dispense
    print("\n=== Attempting forbidden action ===")
    try:
        system.dispense(tech_user, "MED001", 5)
    except PermissionError as e:
        print(f"Permission denied (as expected): {e}")