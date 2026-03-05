from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.decorators import admin_required, hospital_required
from .models import Hospital
from .forms import HospitalProfileForm


@login_required
@admin_required
def hospital_list(request):
    hospitals = Hospital.objects.select_related("user").all().order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        hospitals = hospitals.filter(name__icontains=q)
    verified = request.GET.get("verified")
    if verified == "1":
        hospitals = hospitals.filter(is_verified=True)
    elif verified == "0":
        hospitals = hospitals.filter(is_verified=False)
    return render(request, "hospitals/list.html", {"hospitals": hospitals, "q": q, "verified": verified})


@login_required
def hospital_profile(request):
    if request.user.role == "hospital":
        try:
            hospital = Hospital.objects.get(user=request.user)
        except Hospital.DoesNotExist:
            messages.info(request, "Please complete your hospital profile.")
            return redirect("hospitals:register")
        return render(request, "hospitals/profile.html", {"hospital": hospital})
    elif request.user.role == "admin":
        pk = request.GET.get("pk")
        if pk:
            hospital = get_object_or_404(Hospital, pk=pk)
            return render(request, "hospitals/profile.html", {"hospital": hospital})
        return redirect("hospitals:list")
    messages.error(request, "Not authorised.")
    return redirect("users:dashboard")


@login_required
@hospital_required
def hospital_register(request):
    from audit.models import AuditLog
    try:
        hospital = Hospital.objects.get(user=request.user)
        editing = True
    except Hospital.DoesNotExist:
        hospital = None
        editing = False

    if request.method == "POST":
        form = HospitalProfileForm(request.POST, instance=hospital)
        if form.is_valid():
            h = form.save(commit=False)
            h.user = request.user
            h.save()
            action = "hospital_updated" if editing else "hospital_created"
            AuditLog.log(request.user, action, "Hospital", h.pk,
                         f"{h.name} ({h.registration_number})", request)
            messages.success(request, "Hospital profile saved.")
            return redirect("hospitals:profile")
    else:
        form = HospitalProfileForm(instance=hospital)
    return render(request, "hospitals/register.html", {
        "form": form,
        "editing": editing,
    })


@login_required
@admin_required
def verify_hospital(request, pk):
    from audit.models import AuditLog
    hospital = get_object_or_404(Hospital, pk=pk)
    hospital.is_verified = True
    hospital.save(update_fields=["is_verified"])
    AuditLog.log(request.user, "hospital_verified", "Hospital", hospital.pk,
                 f"Verified {hospital.name}", request)
    messages.success(request, f"{hospital.name} has been verified.")
    return redirect("hospitals:list")

