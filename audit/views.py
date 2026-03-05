from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.decorators import admin_required
from .models import AuditLog


@login_required
@admin_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related("actor").all()[:100]
    return render(request, "audit/list.html", {"logs": logs})
