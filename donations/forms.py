from django import forms
from .models import DonationSlot


class DonationSlotForm(forms.ModelForm):
    class Meta:
        model = DonationSlot
        fields = ["date", "time", "max_capacity"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "max_capacity": forms.NumberInput(attrs={"min": 1}),
        }

    def clean_max_capacity(self):
        cap = self.cleaned_data.get("max_capacity")
        if cap is not None and cap < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return cap
