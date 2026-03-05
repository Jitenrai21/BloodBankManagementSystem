from django.contrib import admin
from .models import BloodInventory


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_group', 'blood_type', 'quantity_units', 'collection_date', 'expiry_date', 'is_available')
    list_filter = ('blood_group', 'blood_type', 'is_available')
    search_fields = ('blood_group',)

