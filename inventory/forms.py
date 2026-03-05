from django import forms
from .models import BloodInventory


class BloodInventoryForm(forms.ModelForm):
    class Meta:
        model = BloodInventory
        fields = [
            "blood_group", "blood_type", "quantity_units",
            "collection_date", "expiry_date",
        ]
        widgets = {
            "blood_group": forms.Select(),
            "blood_type": forms.Select(),
            "quantity_units": forms.NumberInput(attrs={"min": 1}),
            "collection_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        collection = cleaned.get("collection_date")
        expiry = cleaned.get("expiry_date")
        if collection and expiry and expiry <= collection:
            raise forms.ValidationError("Expiry date must be after collection date.")
        qty = cleaned.get("quantity_units")
        if qty is not None and qty < 1:
            raise forms.ValidationError("Quantity must be at least 1 unit.")
        return cleaned
