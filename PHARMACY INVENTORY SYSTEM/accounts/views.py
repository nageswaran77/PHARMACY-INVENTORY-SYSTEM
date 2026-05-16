from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

from .forms import SimpleRegisterForm

def register(request):
    if request.method == 'POST':
        form = SimpleRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = SimpleRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    users = User.objects.all()
    groups = Group.objects.all()
    return render(request, 'accounts/admin_dashboard.html', {'users': users, 'groups': groups})

@login_required
@user_passes_test(is_admin)
def update_role(request, user_id):
    user_to_update = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            user_to_update.groups.clear()
            user_to_update.groups.add(group)
            messages.success(request, f"Role updated for {user_to_update.username} to {group.name}")
        else:
            user_to_update.groups.clear()
            messages.success(request, f"Role removed for {user_to_update.username}")
        return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete.is_superuser:
        messages.error(request, "Cannot delete a superuser.")
    else:
        user_to_delete.delete()
        messages.success(request, f"User {user_to_delete.username} deleted.")
    return redirect('admin_dashboard')
