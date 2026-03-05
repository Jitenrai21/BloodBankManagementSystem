from django import forms
from .models import Hospital


class HospitalProfileForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ["name", "registration_number", "address", "city", "contact_person"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "registration_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if len(name) < 3:
            raise forms.ValidationError("Hospital name must be at least 3 characters.")
        return name

    def clean_registration_number(self):
        reg = self.cleaned_data.get("registration_number", "").strip()
        if len(reg) < 3:
            raise forms.ValidationError("Registration number must be at least 3 characters.")
        qs = Hospital.objects.filter(registration_number=reg)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This registration number is already in use.")
        return reg
