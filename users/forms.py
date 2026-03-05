from django import forms
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
        min_length=8,
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = ["email", "phone", "role", "password"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Email Address"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone Number"}),
            "role": forms.Select(choices=[
                (User.DONOR, "Donor"),
                (User.HOSPITAL, "Hospital"),
            ]),
        }

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        cpw = cleaned.get("confirm_password")
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Hospitals require admin approval; donors are auto-approved
        user.is_approved = self.cleaned_data["role"] == User.DONOR
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email Address"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(self.request, email=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise forms.ValidationError("Your account has been deactivated.")
            if not user.is_approved and user.role == User.HOSPITAL:
                raise forms.ValidationError(
                    "Your hospital account is pending admin approval."
                )
            self._user = user
        return cleaned

    def get_user(self):
        return self._user
