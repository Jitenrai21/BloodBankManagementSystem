from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from users.decorators import admin_required, hospital_required
from hospitals.models import Hospital
from inventory.models import BloodInventory
from .models import BloodRequest
from .forms import BloodRequestForm


@login_required
def request_list(request):
    if request.user.role == "admin":
        qs = BloodRequest.objects.select_related("hospital").all()
    elif request.user.role == "hospital":
        try:
            hospital = Hospital.objects.get(user=request.user)
            qs = BloodRequest.objects.filter(hospital=hospital)
        except Hospital.DoesNotExist:
            qs = BloodRequest.objects.none()
    else:
        qs = BloodRequest.objects.none()

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    urgency = request.GET.get("urgency")
    if urgency:
        qs = qs.filter(urgency=urgency)
    qs = qs.order_by("-created_at")
    return render(request, "requests/list.html", {
        "requests_list": qs,
        "status_filter": status,
        "urgency_filter": urgency,
    })


@login_required
@hospital_required
def request_create(request):
    from audit.models import AuditLog
    try:
        hospital = Hospital.objects.get(user=request.user)
    except Hospital.DoesNotExist:
        messages.error(request, "Complete your hospital profile first.")
        return redirect("hospitals:register")

    if not hospital.is_verified:
        messages.error(request, "Your hospital must be verified before making blood requests.")
        return redirect("hospitals:profile")

    if request.method == "POST":
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            br = form.save(commit=False)
            br.hospital = hospital
            br.save()
            AuditLog.log(request.user, "request_created", "BloodRequest", br.pk,
                         f"{br.units_required} units of {br.blood_group} ({br.urgency})", request)
            messages.success(request, "Blood request submitted.")
            return redirect("requests:list")
    else:
        form = BloodRequestForm()
    return render(request, "requests/create.html", {"form": form})


@login_required
def request_detail(request, pk):
    br = get_object_or_404(BloodRequest.objects.select_related("hospital"), pk=pk)
    # Check access
    if request.user.role == "hospital":
        try:
            hospital = Hospital.objects.get(user=request.user)
            if br.hospital != hospital:
                messages.error(request, "Access denied.")
                return redirect("requests:list")
        except Hospital.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect("requests:list")
    elif request.user.role != "admin":
        messages.error(request, "Access denied.")
        return redirect("users:dashboard")

    # Check available inventory
    available = BloodInventory.objects.filter(
        blood_group=br.blood_group, is_available=True
    ).exclude(expiry_date__lt=timezone.now().date())
    from django.db.models import Sum
    total_available = available.aggregate(total=Sum("quantity_units"))["total"] or 0

    return render(request, "requests/detail.html", {
        "blood_request": br,
        "available_units": total_available,
    })


@login_required
@admin_required
def request_update(request, pk):
    """Admin can approve, reject, or fulfill a blood request."""
    from audit.models import AuditLog
    br = get_object_or_404(BloodRequest, pk=pk)
    action = request.POST.get("action") if request.method == "POST" else None

    if action == "approve" and br.status == "pending":
        br.status = "approved"
        br.save(update_fields=["status"])
        AuditLog.log(request.user, "request_approved", "BloodRequest", br.pk,
                     f"Approved {br.blood_group} request", request)
        messages.success(request, f"Request #{br.pk} approved.")

    elif action == "reject" and br.status in ("pending", "approved"):
        br.status = "rejected"
        br.save(update_fields=["status"])
        AuditLog.log(request.user, "request_rejected", "BloodRequest", br.pk,
                     f"Rejected {br.blood_group} request", request)
        messages.success(request, f"Request #{br.pk} rejected.")

    elif action == "fulfill" and br.status == "approved":
        # Atomic inventory deduction
        with transaction.atomic():
            available = (
                BloodInventory.objects
                .filter(blood_group=br.blood_group, is_available=True)
                .exclude(expiry_date__lt=timezone.now().date())
                .order_by("expiry_date")
                .select_for_update()
            )
            needed = br.units_required
            fulfilled_from = []
            for inv in available:
                if needed <= 0:
                    break
                take = min(inv.quantity_units, needed)
                inv.quantity_units -= take
                if inv.quantity_units == 0:
                    inv.is_available = False
                inv.save()
                needed -= take
                fulfilled_from.append(f"inv#{inv.pk}:{take}u")

            if needed > 0:
                # Not enough stock — rollback
                raise Exception(f"Insufficient inventory. Still need {needed} units.")

            br.status = "fulfilled"
            br.fulfilled_at = timezone.now()
            br.save(update_fields=["status", "fulfilled_at"])

        AuditLog.log(request.user, "request_fulfilled", "BloodRequest", br.pk,
                     f"Fulfilled {br.units_required} units {br.blood_group} from {', '.join(fulfilled_from)}",
                     request)
        messages.success(request, f"Request #{br.pk} fulfilled. {br.units_required} units deducted from inventory.")
    elif action:
        messages.error(request, "Invalid action for the current request status.")

    return redirect("requests:detail", pk=br.pk)

