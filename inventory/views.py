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
    qs = BloodInventory.objects.all().order_by("expiry_date")
    group_filter = request.GET.get("group", "")
    type_filter = request.GET.get("type", "")
    avail_filter = request.GET.get("available", "")
    if group_filter:
        qs = qs.filter(blood_group=group_filter)
    if type_filter:
        qs = qs.filter(blood_type=type_filter)
    if avail_filter == "yes":
        qs = qs.filter(is_available=True)
    elif avail_filter == "no":
        qs = qs.filter(is_available=False)

    expiry_threshold = timezone.now().date() + datetime.timedelta(days=7)
    expiring_count = BloodInventory.objects.filter(
        expiry_date__lte=expiry_threshold, is_available=True
    ).count()

    return render(request, "inventory/list.html", {
        "inventory": qs,
        "group_filter": group_filter,
        "type_filter": type_filter,
        "avail_filter": avail_filter,
        "expiring_count": expiring_count,
        "blood_groups": BloodInventory.BLOOD_GROUP_CHOICES,
        "blood_types": BloodInventory.BLOOD_TYPE_CHOICES,
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
    expiry_threshold = timezone.now().date() + datetime.timedelta(days=7)
    expiring = BloodInventory.objects.filter(
        expiry_date__lte=expiry_threshold, is_available=True
    ).order_by("expiry_date")
    return render(request, "inventory/alerts.html", {"expiring": expiring})

