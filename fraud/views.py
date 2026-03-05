from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.decorators import admin_required
from .models import FraudLog


@login_required
@admin_required
def fraud_log_list(request):
    qs = FraudLog.objects.select_related("user", "resolved_by").all()
    severity = request.GET.get("severity")
    if severity:
        qs = qs.filter(severity=severity)
    resolved = request.GET.get("resolved")
    if resolved == "1":
        qs = qs.filter(is_resolved=True)
    elif resolved == "0":
        qs = qs.filter(is_resolved=False)
    flag_type = request.GET.get("flag_type")
    if flag_type:
        qs = qs.filter(flag_type=flag_type)
    qs = qs.order_by("-created_at")[:200]
    return render(request, "fraud/list.html", {
        "fraud_logs": qs,
        "severity": severity,
        "resolved": resolved,
        "flag_type": flag_type,
    })


@login_required
@admin_required
def resolve_flag(request, pk):
    from audit.models import AuditLog
    flag = get_object_or_404(FraudLog, pk=pk)
    if flag.is_resolved:
        messages.info(request, "This flag is already resolved.")
        return redirect("fraud:list")
    flag.is_resolved = True
    flag.resolved_by = request.user
    flag.save(update_fields=["is_resolved", "resolved_by"])
    AuditLog.log(request.user, "fraud_resolved", "FraudLog", flag.pk,
                 f"Resolved {flag.flag_type} flag (severity: {flag.severity})", request)
    messages.success(request, f"Fraud flag #{flag.pk} marked as resolved.")
    return redirect("fraud:list")

