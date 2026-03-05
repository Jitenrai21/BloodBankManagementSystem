from django.contrib import admin
from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'blood_group', 'units_required', 'urgency', 'status', 'required_by', 'created_at')
    list_filter = ('status', 'urgency', 'blood_group')
    search_fields = ('hospital__name', 'patient_name')

