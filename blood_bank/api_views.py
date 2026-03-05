"""
Centralised REST API views for all domain entities.
All endpoints are read-only (GET / list + detail) except where noted.
Authentication: session-based (DRF SessionAuthentication).
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from donors.models import Donor
from hospitals.models import Hospital
from inventory.models import BloodInventory
from donations.models import DonationSlot, DonationHistory
from requests.models import BloodRequest
from fraud.models import FraudLog
from audit.models import AuditLog

from .serializers import (
    DonorSerializer, HospitalSerializer, BloodInventorySerializer,
    DonationSlotSerializer, DonationHistorySerializer,
    BloodRequestSerializer, FraudLogSerializer, AuditLogSerializer,
)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


# ── Donors ───────────────────────────────────────────────────────────────────

class DonorListAPI(generics.ListAPIView):
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Donor.objects.select_related("user").all()


class DonorDetailAPI(generics.RetrieveAPIView):
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Donor.objects.select_related("user").all()


# ── Hospitals ────────────────────────────────────────────────────────────────

class HospitalListAPI(generics.ListAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = Hospital.objects.select_related("user").all()


class HospitalDetailAPI(generics.RetrieveAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Hospital.objects.select_related("user").all()


# ── Inventory ────────────────────────────────────────────────────────────────

class InventoryListAPI(generics.ListAPIView):
    serializer_class = BloodInventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = BloodInventory.objects.all()
        group = self.request.query_params.get("group")
        if group:
            qs = qs.filter(blood_group=group)
        available = self.request.query_params.get("available")
        if available == "1":
            qs = qs.filter(is_available=True)
        return qs


class InventoryDetailAPI(generics.RetrieveAPIView):
    serializer_class = BloodInventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = BloodInventory.objects.all()


# ── Donation Slots ───────────────────────────────────────────────────────────

class SlotListAPI(generics.ListAPIView):
    serializer_class = DonationSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DonationSlot.objects.all().order_by("date", "time")


class SlotDetailAPI(generics.RetrieveAPIView):
    serializer_class = DonationSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DonationSlot.objects.all()


# ── Donation History ─────────────────────────────────────────────────────────

class DonationHistoryListAPI(generics.ListAPIView):
    serializer_class = DonationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return DonationHistory.objects.select_related("donor", "slot").all()
        if user.role == "donor":
            return DonationHistory.objects.filter(
                donor__user=user
            ).select_related("donor", "slot")
        return DonationHistory.objects.none()


# ── Blood Requests ───────────────────────────────────────────────────────────

class BloodRequestListAPI(generics.ListAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return BloodRequest.objects.select_related("hospital").all()
        if user.role == "hospital":
            return BloodRequest.objects.filter(
                hospital__user=user
            ).select_related("hospital")
        return BloodRequest.objects.none()


class BloodRequestDetailAPI(generics.RetrieveAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = BloodRequest.objects.select_related("hospital").all()


class BloodRequestCreateAPI(generics.CreateAPIView):
    """Hospital users can create blood requests via API."""
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        hospital = Hospital.objects.get(user=self.request.user)
        serializer.save(hospital=hospital)


# ── Fraud ────────────────────────────────────────────────────────────────────

class FraudLogListAPI(generics.ListAPIView):
    serializer_class = FraudLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = FraudLog.objects.select_related("user").all().order_by("-created_at")[:200]


# ── Audit ────────────────────────────────────────────────────────────────────

class AuditLogListAPI(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = AuditLog.objects.select_related("actor").all()[:100]
