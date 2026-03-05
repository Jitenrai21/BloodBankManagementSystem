from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import UserRegistrationForm, LoginForm
from .models import User
from .decorators import admin_required


def register(request):
    """Registration view – donors auto-approved, hospitals await admin."""
    if request.user.is_authenticated:
        return redirect("users:dashboard")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == User.DONOR:
                login(request, user)
                messages.success(request, "Welcome! Your donor account is ready.")
                return redirect("users:dashboard")
            else:
                messages.info(
                    request,
                    "Hospital account created. Please wait for admin approval.",
                )
                return redirect("users:login")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """Login view with role-based redirection."""
    if request.user.is_authenticated:
        return redirect("users:dashboard")
    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.email}!")
            return redirect("users:dashboard")
    else:
        form = LoginForm(request=request)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """Logout and redirect."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("users:login")


@login_required
def dashboard(request):
    """Redirect to the correct role-based dashboard template."""
    role = request.user.role
    if role == User.ADMIN:
        return render(request, "users/dashboard_admin.html", _admin_context(request))
    elif role == User.DONOR:
        return render(request, "users/dashboard_donor.html", _donor_context(request))
    elif role == User.HOSPITAL:
        return render(request, "users/dashboard_hospital.html", _hospital_context(request))
    return redirect("users:login")


@login_required
def profile(request):
    """User profile view."""
    return render(request, "users/profile.html", {"user": request.user})


# ── Context helpers ──────────────────────────────────────────────────────────

def _admin_context(request):
    from donors.models import Donor
    from hospitals.models import Hospital
    from inventory.models import BloodInventory
    from requests.models import BloodRequest
    from fraud.models import FraudLog
    from donations.models import DonationSlot, DonationHistory
    from django.utils import timezone
    from django.db.models import Sum, Count
    import datetime

    today = timezone.now().date()
    expiry_threshold = today + datetime.timedelta(days=7)

    # ── Users ────────────────────────────────────────────────────────────────
    total_users = User.objects.count()
    users_by_role = {
        "admin":    User.objects.filter(role=User.ADMIN).count(),
        "donor":    User.objects.filter(role=User.DONOR).count(),
        "hospital": User.objects.filter(role=User.HOSPITAL).count(),
    }
    pending_users = User.objects.filter(is_approved=False).order_by("-date_joined")
    recent_users  = User.objects.order_by("-date_joined")[:10]

    # ── Hospitals ─────────────────────────────────────────────────────────────
    pending_hospitals_qs = Hospital.objects.filter(is_verified=False).select_related("user")
    verified_hospitals   = Hospital.objects.filter(is_verified=True).count()
    total_hospitals      = Hospital.objects.count()

    # ── Inventory ─────────────────────────────────────────────────────────────
    total_inventory = (
        BloodInventory.objects.filter(is_available=True)
        .aggregate(total=Sum("quantity_units"))["total"] or 0
    )
    expiring_soon_count = BloodInventory.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=expiry_threshold,
        is_available=True
    ).count()
    expired_count = BloodInventory.objects.filter(
        expiry_date__lt=today, is_available=True
    ).count()
    expired_inventory_qs = (
        BloodInventory.objects.filter(expiry_date__lt=today, is_available=True)
        .values("blood_group")
        .annotate(expired_units=Sum("quantity_units"))
        .order_by("blood_group")
    )
    inventory_by_group = (
        BloodInventory.objects.filter(is_available=True)
        .values("blood_group")
        .annotate(total=Sum("quantity_units"))
        .order_by("blood_group")
    )

    # ── Blood Requests ────────────────────────────────────────────────────────
    requests_by_status = {
        "pending":   BloodRequest.objects.filter(status="pending").count(),
        "approved":  BloodRequest.objects.filter(status="approved").count(),
        "fulfilled": BloodRequest.objects.filter(status="fulfilled").count(),
        "rejected":  BloodRequest.objects.filter(status="rejected").count(),
    }
    recent_requests = BloodRequest.objects.select_related("hospital").order_by("-created_at")[:8]
    urgent_critical_count = BloodRequest.objects.filter(
        status="pending", urgency__in=["urgent", "critical"]
    ).count()
    urgent_critical_requests = (
        BloodRequest.objects.filter(status="pending", urgency__in=["urgent", "critical"])
        .select_related("hospital")
        .order_by("-created_at")[:5]
    )
    urgent_critical_has_critical = BloodRequest.objects.filter(
        status="pending", urgency="critical"
    ).exists()

    # ── Donation Slots ────────────────────────────────────────────────────────
    upcoming_slots = DonationSlot.objects.filter(
        date__gte=today, is_active=True
    ).order_by("date", "time")[:5]
    total_slots        = DonationSlot.objects.count()
    pending_donations  = DonationHistory.objects.filter(status="pending").count()
    approved_donations = DonationHistory.objects.filter(status="approved").count()

    # ── Fraud ─────────────────────────────────────────────────────────────────
    active_fraud_flags = FraudLog.objects.filter(is_resolved=False).count()
    fraud_by_severity  = {
        "high":   FraudLog.objects.filter(is_resolved=False, severity="high").count(),
        "medium": FraudLog.objects.filter(is_resolved=False, severity="medium").count(),
        "low":    FraudLog.objects.filter(is_resolved=False, severity="low").count(),
    }

    return {
        # users
        "total_users":          total_users,
        "users_by_role":        users_by_role,
        "pending_users":        pending_users,
        "recent_users":         recent_users,
        # hospitals
        "pending_hospitals":        pending_hospitals_qs.count(),
        "pending_hospitals_qs":     pending_hospitals_qs,
        "verified_hospitals":       verified_hospitals,
        "total_hospitals":          total_hospitals,
        # inventory
        "total_inventory":      total_inventory,
        "expiring_soon":        expiring_soon_count,
        "expired_count":        expired_count,
        "expired_inventory_qs": expired_inventory_qs,
        "inventory_by_group":   inventory_by_group,
        # requests
        "pending_requests":     requests_by_status["pending"],
        "approved_requests":    requests_by_status["approved"],
        "fulfilled_requests":   requests_by_status["fulfilled"],
        "rejected_requests":    requests_by_status["rejected"],
        "requests_by_status":   requests_by_status,
        "recent_requests":      recent_requests,
        "urgent_critical_count":        urgent_critical_count,
        "urgent_critical_requests":     urgent_critical_requests,
        "urgent_critical_has_critical": urgent_critical_has_critical,
        # donations
        "upcoming_slots":       upcoming_slots,
        "total_slots":          total_slots,
        "pending_donations":    pending_donations,
        "approved_donations":   approved_donations,
        "pending_slots":        pending_donations,
        "approved_slots":       approved_donations,
        # fraud
        "active_fraud_flags":   active_fraud_flags,
        "fraud_by_severity":    fraud_by_severity,
        "high_risk_flags":      fraud_by_severity["high"],
        "medium_risk_flags":    fraud_by_severity["medium"],
        "low_risk_flags":       fraud_by_severity["low"],
        # user role counts (flat aliases)
        "admins_count":         users_by_role["admin"],
        "donors_count":         users_by_role["donor"],
        "hospitals_count":      users_by_role["hospital"],
        "pending_approvals":    pending_users.count(),
    }


def _donor_context(request):
    from donors.models import Donor
    from donations.models import DonationHistory
    try:
        donor = Donor.objects.get(user=request.user)
        history = DonationHistory.objects.filter(donor=donor).order_by("-created_at")[:5]
    except Donor.DoesNotExist:
        donor = None
        history = []
    return {"donor": donor, "recent_history": history}


def _hospital_context(request):
    from hospitals.models import Hospital
    from requests.models import BloodRequest
    try:
        hospital = Hospital.objects.get(user=request.user)
        recent_requests = BloodRequest.objects.filter(hospital=hospital).order_by("-created_at")[:5]
        active_count = BloodRequest.objects.filter(hospital=hospital, status="pending").count()
        fulfilled_count = BloodRequest.objects.filter(hospital=hospital, status="fulfilled").count()
    except Hospital.DoesNotExist:
        hospital = None
        recent_requests = []
        active_count = 0
        fulfilled_count = 0
    return {
        "hospital": hospital,
        "recent_requests": recent_requests,
        "active_count": active_count,
        "fulfilled_count": fulfilled_count,
    }


# ── Admin Management Views ──────────────────────────────────────────────────

@login_required
@admin_required
def manage_users(request):
    """Admin view to list all users with filters."""
    role     = request.GET.get("role", "")
    approved = request.GET.get("approved", "")
    active   = request.GET.get("active", "")
    q        = request.GET.get("q", "").strip()

    qs = User.objects.all().order_by("-date_joined")
    if role:
        qs = qs.filter(role=role)
    if approved == "1":
        qs = qs.filter(is_approved=True)
    elif approved == "0":
        qs = qs.filter(is_approved=False)
    if active == "1":
        qs = qs.filter(is_active=True)
    elif active == "0":
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(email__icontains=q)

    return render(request, "users/manage_users.html", {
        "users":    qs,
        "role":     role,
        "approved": approved,
        "active":   active,
        "q":        q,
    })


@login_required
@admin_required
def approve_user(request, pk):
    """Approve a user (hospital) account."""
    from audit.models import AuditLog
    user = get_object_or_404(User, pk=pk)
    user.is_approved = True
    user.save()
    # If hospital, also verify
    if user.role == User.HOSPITAL and hasattr(user, "hospital_profile"):
        user.hospital_profile.is_verified = True
        user.hospital_profile.save()
    AuditLog.log(request.user, "user_approved", "User", user.pk,
                 f"Approved user {user.email}", request)
    messages.success(request, f"User {user.email} has been approved.")
    return redirect("users:manage_users")


@login_required
@admin_required
def block_user(request, pk):
    """Block a user account."""
    from audit.models import AuditLog
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot block yourself.")
        return redirect("users:manage_users")
    user.is_active = False
    user.save()
    AuditLog.log(request.user, "user_blocked", "User", user.pk,
                 f"Blocked user {user.email}", request)
    messages.success(request, f"User {user.email} has been blocked.")
    return redirect("users:manage_users")


@login_required
@admin_required
def unblock_user(request, pk):
    """Unblock a user account."""
    from audit.models import AuditLog
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    AuditLog.log(request.user, "user_unblocked", "User", user.pk,
                 f"Unblocked user {user.email}", request)
    messages.success(request, f"User {user.email} has been unblocked.")
    return redirect("users:manage_users")

