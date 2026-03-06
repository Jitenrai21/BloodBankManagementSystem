from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from users.decorators import admin_required
from .models import BloodInventory
from .forms import BloodInventoryForm


@login_required
def inventory_list(request):
    today = timezone.now().date()
    qs = BloodInventory.objects.all().order_by("expiry_date")

    group_filter  = request.GET.get("group", "")
    type_filter   = request.GET.get("type", "")
    avail_filter  = request.GET.get("available", "")
    expired_filter = request.GET.get("expired", "")

    if group_filter:
        qs = qs.filter(blood_group=group_filter)
    if type_filter:
        qs = qs.filter(blood_type=type_filter)
    if avail_filter == "1":
        qs = qs.filter(is_available=True)
    elif avail_filter == "0":
        qs = qs.filter(is_available=False)
    # Admin-only filter: show only expired items
    if expired_filter == "1" and request.user.role == "admin":
        qs = qs.filter(expiry_date__lt=today)

    expiry_threshold = today + datetime.timedelta(days=7)
    # Only count items expiring in the future (not already expired)
    expiring_count = BloodInventory.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=expiry_threshold,
        is_available=True
    ).count()

    # Expired count/items - computed for admin only
    is_admin = request.user.role == "admin"
    expired_count = (
        BloodInventory.objects.filter(expiry_date__lt=today, is_available=True).count()
        if is_admin else 0
    )

    return render(request, "inventory/list.html", {
        "inventory":      qs,
        "group":          group_filter,
        "type":           type_filter,
        "available":      avail_filter,
        "expired_filter": expired_filter,
        "expiring_count": expiring_count,
        "expired_count":  expired_count,
        "is_admin":       is_admin,
        "today":          today,
        "blood_groups":   BloodInventory.BLOOD_GROUP_CHOICES,
        "blood_types":    BloodInventory.BLOOD_TYPE_CHOICES,
    })


@login_required
@admin_required
def inventory_add(request):
    from audit.models import AuditLog
    if request.method == "POST":
        form = BloodInventoryForm(request.POST)
        if form.is_valid():
            inv = form.save()
            AuditLog.log(request.user, "inventory_added", "BloodInventory",
                         inv.pk, f"Added {inv.quantity_units} units of {inv.blood_group} {inv.blood_type}", request)
            messages.success(request, "Blood inventory added successfully.")
            return redirect("inventory:list")
    else:
        form = BloodInventoryForm()
    return render(request, "inventory/add.html", {"form": form})


@login_required
@admin_required
def inventory_update(request, pk):
    from audit.models import AuditLog
    inv = get_object_or_404(BloodInventory, pk=pk)
    if request.method == "POST":
        form = BloodInventoryForm(request.POST, instance=inv)
        if form.is_valid():
            inv = form.save()
            AuditLog.log(request.user, "inventory_updated", "BloodInventory",
                         inv.pk, f"Updated to {inv.quantity_units} units", request)
            messages.success(request, "Inventory updated successfully.")
            return redirect("inventory:list")
    else:
        form = BloodInventoryForm(instance=inv)
    return render(request, "inventory/update.html", {"form": form, "item": inv})


@login_required
@admin_required
def expiry_alerts(request):
    today = timezone.now().date()
    expiry_threshold = today + datetime.timedelta(days=7)
    # Only show items expiring in the FUTURE (>= today), not already expired
    expiring = BloodInventory.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=expiry_threshold,
        is_available=True
    ).order_by("expiry_date")
    expired = BloodInventory.objects.filter(
        expiry_date__lt=today, is_available=True
    ).order_by("expiry_date")
    return render(request, "inventory/alerts.html", {
        "expiring": expiring,
        "expired":  expired,
        "today":    today,
    })


@login_required
@admin_required
def inventory_delete(request, pk):
    """Delete a single inventory record (admin only)."""
    from audit.models import AuditLog
    inv = get_object_or_404(BloodInventory, pk=pk)
    if request.method == "POST":
        desc = (f"Deleted {inv.quantity_units} units of {inv.blood_group} "
                f"{inv.blood_type} (expired {inv.expiry_date})")
        AuditLog.log(request.user, "inventory_deleted", "BloodInventory",
                     inv.pk, desc, request)
        inv.delete()
        messages.success(request, "Inventory record deleted.")
    return redirect("inventory:list")


@login_required
@admin_required
def delete_expired_bulk(request):
    """Bulk-delete all expired inventory records (admin only)."""
    from audit.models import AuditLog
    if request.method == "POST":
        today = timezone.now().date()
        expired_qs = BloodInventory.objects.filter(expiry_date__lt=today)
        count = expired_qs.count()
        expired_qs.delete()
        AuditLog.log(request.user, "inventory_bulk_deleted", "BloodInventory",
                     None, f"Bulk deleted {count} expired inventory records", request)
        messages.success(
            request,
            f"{count} expired record{'s' if count != 1 else ''} permanently deleted."
        )
    return redirect("inventory:list")

