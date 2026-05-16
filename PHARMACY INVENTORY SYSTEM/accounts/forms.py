from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SimpleRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)
        help_texts = {
            'username': None,
        }
