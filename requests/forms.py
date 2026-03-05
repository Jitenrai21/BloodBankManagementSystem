from django import forms
from django.utils import timezone
from .models import BloodRequest


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ["blood_group", "units_required", "urgency", "patient_name", "reason", "required_by"]
        widgets = {
            "blood_group": forms.Select(attrs={"class": "form-control"}),
            "units_required": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "urgency": forms.Select(attrs={"class": "form-control"}),
            "patient_name": forms.TextInput(attrs={"class": "form-control"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "required_by": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean_units_required(self):
        units = self.cleaned_data.get("units_required")
        if units is not None and units < 1:
            raise forms.ValidationError("At least 1 unit must be requested.")
        return units

    def clean_required_by(self):
        d = self.cleaned_data.get("required_by")
        if d and d < timezone.now().date():
            raise forms.ValidationError("Required-by date cannot be in the past.")
        return d
