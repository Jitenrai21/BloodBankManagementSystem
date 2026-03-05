from django.contrib import admin
from .models import DonationSlot, DonationHistory


@admin.register(DonationSlot)
class DonationSlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'max_capacity', 'booked_count', 'is_active')
    list_filter = ('is_active', 'date')


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_group', 'units_donated', 'status', 'donated_at', 'created_at')
    list_filter = ('status', 'blood_group')
    search_fields = ('donor__full_name',)

