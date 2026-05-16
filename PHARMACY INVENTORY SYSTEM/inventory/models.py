# inventory/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib
from datetime import date

class InventoryItem(models.Model):
    sku = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(help_text="Minimum stock before alert")
    reorder_qty = models.IntegerField(help_text="Quantity to order when restocking")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("can_dispense", "Can dispense medication"),
        ]

    def is_low(self):
        return self.quantity <= self.reorder_level

    def days_until_expiry(self):
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    def __str__(self):
        return f"{self.name} ({self.sku})"

class SaleRecord(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='sales')
    quantity = models.IntegerField()
    unit_price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price_at_sale
        super().save(*args, **kwargs)

class CustomerOrder(models.Model):
    """Stores customer specific purchases/bills."""
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Alert(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.TextField()
    hash = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = timezone.now()
        user_str = self.user.username if self.user else "Anonymous"
        raw = f"{self.timestamp}{user_str}{self.action}{self.details}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        super().save(*args, **kwargs)