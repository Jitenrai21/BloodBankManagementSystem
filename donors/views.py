from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from users.decorators import donor_required, admin_required
from .models import Donor
from .forms import DonorProfileForm
from donations.models import DonationHistory


def _check_eligibility(donor):
    """Update eligibility: ineligible if last donation was < 90 days ago."""
    if donor.last_donation_date:
        days_since = (timezone.now().date() - donor.last_donation_date).days
        donor.is_eligible = days_since >= 90
    else:
        donor.is_eligible = True
    donor.save(update_fields=["is_eligible"])
    return donor


@login_required
@admin_required
def donor_list(request):
    donors = Donor.objects.select_related("user").all().order_by("-created_at")
    return render(request, "donors/list.html", {"donors": donors})


@login_required
@donor_required
def donor_profile(request):
    try:
        donor = Donor.objects.get(user=request.user)
        donor = _check_eligibility(donor)
    except Donor.DoesNotExist:
        messages.info(request, "Please complete your donor profile.")
        return redirect("donors:register")
    history = DonationHistory.objects.filter(donor=donor).order_by("-created_at")
    return render(request, "donors/profile.html", {
        "donor": donor,
        "history": history,
    })


@login_required
@donor_required
def donor_register(request):
    """Create or update donor profile."""
    try:
        donor = Donor.objects.get(user=request.user)
        editing = True
    except Donor.DoesNotExist:
        donor = None
        editing = False

    if request.method == "POST":
        form = DonorProfileForm(request.POST, instance=donor)
        if form.is_valid():
            donor = form.save(commit=False)
            if not editing:
                donor.user = request.user
            donor.save()
            _check_eligibility(donor)
            messages.success(request, "Donor profile saved successfully.")
            return redirect("donors:profile")
    else:
        form = DonorProfileForm(instance=donor)

    return render(request, "donors/register.html", {
        "form": form,
        "editing": editing,
    })


@login_required
@donor_required
def donation_history(request):
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.info(request, "Please complete your donor profile first.")
        return redirect("donors:register")
    history = DonationHistory.objects.filter(donor=donor).order_by("-created_at")
    return render(request, "donors/history.html", {
        "donor": donor,
        "history": history,
    })

