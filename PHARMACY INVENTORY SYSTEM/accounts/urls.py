from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-role/<int:user_id>/', views.update_role, name='update_role'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
