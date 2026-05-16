# inventory/forms.py
from django import forms
from .models import InventoryItem, CustomerOrder

class StockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)

class MedicationForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["name", "expiry_date", "unit_price", "quantity", "sku", "reorder_level", "reorder_qty"]
        labels = {
            'name': 'Tablet Name',
            'expiry_date': 'Expired Date',
            'unit_price': 'Price per Unit',
            'quantity': 'Initial Quantity',
        }
        widgets = {
            'sku': forms.TextInput(attrs={'placeholder': 'e.g. MED-001'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter tablet name...'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'quantity': forms.NumberInput(attrs={'min': 0}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = CustomerOrder
        fields = ["customer_name", "mobile_number", "quantity"]
        labels = {
            'customer_name': 'Your Name',
            'mobile_number': 'Mobile Number',
            'quantity': 'Tablet in Quantity',
        }
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'e.g. +91 9876543210'}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }