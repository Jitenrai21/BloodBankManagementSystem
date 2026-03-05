from rest_framework import serializers
from donors.models import Donor
from hospitals.models import Hospital
from inventory.models import BloodInventory
from donations.models import DonationSlot, DonationHistory
from requests.models import BloodRequest
from fraud.models import FraudLog
from audit.models import AuditLog


class DonorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Donor
        fields = [
            "id", "email", "full_name", "date_of_birth", "gender",
            "blood_group", "city", "address", "is_eligible",
            "last_donation_date",
        ]
        read_only_fields = ["id", "email", "is_eligible", "last_donation_date"]


class HospitalSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Hospital
        fields = [
            "id", "email", "name", "registration_number", "address",
            "city", "contact_person", "is_verified", "created_at",
        ]
        read_only_fields = ["id", "email", "is_verified", "created_at"]


class BloodInventorySerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = BloodInventory
        fields = [
            "id", "blood_group", "blood_type", "quantity_units",
            "collection_date", "expiry_date", "is_available", "is_expired",
        ]
        read_only_fields = ["id", "is_expired"]


class DonationSlotSerializer(serializers.ModelSerializer):
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = DonationSlot
        fields = [
            "id", "date", "time", "max_capacity", "booked_count",
            "is_active", "is_full",
        ]
        read_only_fields = ["id", "booked_count", "is_full"]


class DonationHistorySerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source="donor.full_name", read_only=True)
    slot_date = serializers.DateField(source="slot.date", read_only=True)

    class Meta:
        model = DonationHistory
        fields = [
            "id", "donor_name", "slot_date", "blood_group",
            "units_donated", "status", "donated_at", "created_at",
        ]
        read_only_fields = fields


class BloodRequestSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            "id", "hospital_name", "blood_group", "units_required",
            "urgency", "status", "patient_name", "reason",
            "required_by", "fulfilled_at", "created_at",
        ]
        read_only_fields = ["id", "hospital_name", "status", "fulfilled_at", "created_at"]


class FraudLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = FraudLog
        fields = [
            "id", "user_email", "flag_type", "severity", "risk_score",
            "description", "is_resolved", "created_at",
        ]
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_email", "action", "target_type", "target_id",
            "details", "ip_address", "created_at",
        ]
        read_only_fields = fields
