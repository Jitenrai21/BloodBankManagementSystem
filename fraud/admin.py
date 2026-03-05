from django.contrib import admin
from .models import FraudLog


@admin.register(FraudLog)
class FraudLogAdmin(admin.ModelAdmin):
    list_display = ('flag_type', 'severity', 'risk_score', 'user', 'ip_address', 'is_resolved', 'created_at')
    list_filter = ('severity', 'flag_type', 'is_resolved')
    search_fields = ('user__email', 'description')
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected flags as resolved")
    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_by=request.user)
        self.message_user(request, f"{updated} flag(s) marked as resolved.")

