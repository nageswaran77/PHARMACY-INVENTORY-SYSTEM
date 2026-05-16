# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('buy/<int:pk>/', views.buy_medication, name='buy_medication'),
    path('bill/<int:order_id>/', views.view_bill, name='view_bill'),
    path('add-medication/', views.add_medication, name='add_medication'),
    path('edit-medication/<int:pk>/', views.edit_medication, name='edit_medication'),
    path('add-stock/<int:pk>/', views.add_stock, name='add_stock'),
    path('dispense/<int:pk>/', views.dispense, name='dispense'),
    path('alerts/', views.alerts_list, name='alerts'),
    path('predict/<int:pk>/', views.predict_restock, name='predict'),
    path('audit/', views.audit_log, name='audit'),
    path('sales/', views.sales_dashboard, name='sales_dashboard'),
]