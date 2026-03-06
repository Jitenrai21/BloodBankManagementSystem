from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from users.decorators import admin_required, donor_required
from donors.models import Donor
from .models import DonationSlot, DonationHistory
from .forms import DonationSlotForm


# ── Slot Management (Admin) ─────────────────────────────────────────────────

@login_required
def slot_list(request):
    from django.utils import timezone
    import datetime
    now = timezone.now()

    # Auto-expire past slots: bulk-update is_active=False for passed date/times
    past_slots = DonationSlot.objects.filter(is_active=True, date__lt=now.date())
    past_slots.update(is_active=False)
    # Also expire slots that are today but time has passed
    today_past = DonationSlot.objects.filter(
        is_active=True,
        date=now.date(),
        time__lt=now.time()
    )
    today_past.update(is_active=False)

    is_admin = request.user.role == "admin"

    if is_admin:
        slots = DonationSlot.objects.all().order_by("-date", "-time")
    else:
        # Donors only see active, non-full, future or today slots
        slots = DonationSlot.objects.filter(
            is_active=True
        ).order_by("date", "time")
        # Exclude full slots for donors
        slots = [s for s in slots if not s.is_full()]

    # Pending bookings count for admin context
    pending_bookings_count = DonationHistory.objects.filter(status="pending").count() if is_admin else 0

    return render(request, "donations/slot_list.html", {
        "slots": slots,
        "is_admin": is_admin,
        "pending_bookings_count": pending_bookings_count,
    })


@login_required
@admin_required
def slot_create(request):
    from audit.models import AuditLog
    if request.method == "POST":
        form = DonationSlotForm(request.POST)
        if form.is_valid():
            slot = form.save()
            AuditLog.log(request.user, "slot_created", "DonationSlot",
                         slot.pk, f"Slot on {slot.date} {slot.time}", request)
            messages.success(request, "Donation slot created.")
            return redirect("donations:slot_list")
    else:
        form = DonationSlotForm()
    return render(request, "donations/slot_form.html", {"form": form, "title": "Create Donation Slot"})


@login_required
@admin_required
def slot_edit(request, pk):
    from audit.models import AuditLog
    slot = get_object_or_404(DonationSlot, pk=pk)
    if request.method == "POST":
        form = DonationSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            AuditLog.log(request.user, "slot_updated", "DonationSlot",
                         slot.pk, f"Updated slot {slot.date} {slot.time}", request)
            messages.success(request, "Donation slot updated.")
            return redirect("donations:slot_list")
    else:
        form = DonationSlotForm(instance=slot)
    return render(request, "donations/slot_form.html", {"form": form, "title": "Edit Donation Slot"})


# ── Booking (Donor) ─────────────────────────────────────────────────────────

@login_required
@donor_required
def book_slot(request, slot_id):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Complete your donor profile first.")
        return redirect("donors:register")

    if not donor.is_eligible:
        messages.error(request, "You are not currently eligible to donate (last donation was less than 90 days ago).")
        return redirect("donations:slot_list")

    # Check for existing pending/approved booking
    active_booking = DonationHistory.objects.filter(
        donor=donor, status__in=["pending", "approved"]
    ).exists()
    if active_booking:
        messages.error(request, "You already have an active booking. Wait for it to be completed or cancelled.")
        return redirect("donations:slot_list")

    # Atomic slot booking to prevent overbooking
    with transaction.atomic():
        slot = DonationSlot.objects.select_for_update().get(pk=slot_id)
        if not slot.is_active:
            messages.error(request, "This slot is no longer active.")
            return redirect("donations:slot_list")
        if slot.is_full():
            messages.error(request, "This slot is fully booked.")
            return redirect("donations:slot_list")
        slot.booked_count += 1
        slot.save()
        DonationHistory.objects.create(
            donor=donor,
            slot=slot,
            blood_group=donor.blood_group,
            units_donated=1,
            status="pending",
        )
    messages.success(request, f"Slot booked on {slot.date} at {slot.time}. Awaiting admin approval.")
    return redirect("donations:slot_list")


# ── Donation History ─────────────────────────────────────────────────────────

@login_required
def donation_history(request):
    if request.user.role == "admin":
        history = DonationHistory.objects.select_related("donor", "slot").all().order_by("-created_at")
    elif request.user.role == "donor":
        try:
            donor = Donor.objects.get(user=request.user)
            history = DonationHistory.objects.filter(donor=donor).order_by("-created_at")
        except Donor.DoesNotExist:
            history = []
    else:
        history = []
    return render(request, "donations/history.html", {"history": history})


# ── Admin Approval / Rejection / Completion ──────────────────────────────────

@login_required
@admin_required
def approve_donation(request, pk):
    from audit.models import AuditLog
    donation = get_object_or_404(DonationHistory, pk=pk)
    if donation.status != "pending":
        messages.error(request, "Only pending donations can be approved.")
        return redirect("donations:history")
    donation.status = "approved"
    donation.save()
    AuditLog.log(request.user, "donation_approved", "DonationHistory",
                 donation.pk, f"Approved donation by {donation.donor}", request)
    messages.success(request, f"Donation #{donation.pk} approved.")
    return redirect("donations:history")


@login_required
@admin_required
def reject_donation(request, pk):
    from audit.models import AuditLog
    donation = get_object_or_404(DonationHistory, pk=pk)
    if donation.status not in ("pending", "approved"):
        messages.error(request, "Cannot reject this donation.")
        return redirect("donations:history")
    # Release slot capacity
    if donation.slot:
        with transaction.atomic():
            slot = DonationSlot.objects.select_for_update().get(pk=donation.slot.pk)
            slot.booked_count = max(0, slot.booked_count - 1)
            slot.save()
    donation.status = "rejected"
    donation.save()
    AuditLog.log(request.user, "donation_rejected", "DonationHistory",
                 donation.pk, f"Rejected donation by {donation.donor}", request)
    messages.success(request, f"Donation #{donation.pk} rejected.")
    return redirect("donations:history")


@login_required
@admin_required
def complete_donation(request, pk):
    """Mark donation as completed and update inventory."""
    from audit.models import AuditLog
    from inventory.models import BloodInventory
    import datetime

    donation = get_object_or_404(DonationHistory, pk=pk)
    if donation.status != "approved":
        messages.error(request, "Only approved donations can be completed.")
        return redirect("donations:history")

    donation.status = "completed"
    donation.donated_at = timezone.now()
    donation.save()

    # Update donor's last donation date and eligibility
    donor = donation.donor
    donor.last_donation_date = timezone.now().date()
    donor.is_eligible = False
    donor.save(update_fields=["last_donation_date", "is_eligible"])

    # Add to inventory
    BloodInventory.objects.create(
        blood_group=donation.blood_group,
        blood_type="whole",
        quantity_units=donation.units_donated,
        collection_date=timezone.now().date(),
        expiry_date=timezone.now().date() + datetime.timedelta(days=42),
        is_available=True,
    )

    AuditLog.log(request.user, "donation_completed", "DonationHistory",
                 donation.pk,
                 f"Completed: {donation.units_donated} units of {donation.blood_group} added to inventory",
                 request)
    messages.success(request, f"Donation #{donation.pk} completed. {donation.units_donated} units added to inventory.")
    return redirect("donations:history")

