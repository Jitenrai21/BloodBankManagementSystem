from django.contrib import admin
from .models import Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'registration_number', 'contact_person', 'is_verified')
    list_filter = ('is_verified', 'city')
    search_fields = ('name', 'registration_number', 'user__email')
    actions = ["approve_hospitals"]

    @admin.action(description="Approve selected hospitals")
    def approve_hospitals(self, request, queryset):
        for hospital in queryset:
            hospital.is_verified = True
            hospital.save()
            hospital.user.is_approved = True
            hospital.user.save()
        self.message_user(request, f"{queryset.count()} hospital(s) approved.")

