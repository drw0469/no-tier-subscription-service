from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomerRegistration(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_customer = True  # Enforce customer role
        if commit:
            user.save()
        return user

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'first_name', 'email', 'phone_number', 'address', 'bio')

class StaffUserCreationForm(UserCreationForm):
    """Used by Admin to spin up staff and other admins."""
    ROLE_CHOICES = [
        ('staff', 'Staff Member'),
        ('admin', 'Admin Member'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address')

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')

        if role == 'admin':
            user.is_admin_member = True
            user.is_staff = True  # Grants access to Core Django Admin Backend
            user.is_superuser = True
        elif role == 'staff':
            user.is_staff_member = True
            user.is_staff = True

        if commit:
            user.save()
        return user


    