from django.contrib import admin
from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'blood_group', 'city', 'is_eligible', 'last_donation_date')
    list_filter = ('blood_group', 'gender', 'is_eligible')
    search_fields = ('full_name', 'user__email')

