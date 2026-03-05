from django import forms
from django.utils import timezone
import datetime
from .models import Donor


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            "full_name", "date_of_birth", "gender", "blood_group",
            "address", "city",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Full Name"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "gender": forms.Select(),
            "blood_group": forms.Select(),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "Address"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            age = (timezone.now().date() - dob).days // 365
            if age < 18:
                raise forms.ValidationError("Donor must be at least 18 years old.")
            if age > 65:
                raise forms.ValidationError("Donor must be 65 years or younger.")
        return dob

    def clean_full_name(self):
        name = self.cleaned_data.get("full_name", "").strip()
        if len(name) < 3:
            raise forms.ValidationError("Name must be at least 3 characters.")
        return name
