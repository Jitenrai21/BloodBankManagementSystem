from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "ip_address", "created_at")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("actor__email", "target_type", "details")
    readonly_fields = ("actor", "action", "target_type", "target_id", "details", "ip_address", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
