from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("user_approved", "User Approved"),
        ("user_blocked", "User Blocked"),
        ("user_unblocked", "User Unblocked"),
        ("hospital_created", "Hospital Created"),
        ("hospital_updated", "Hospital Updated"),
        ("hospital_verified", "Hospital Verified"),
        ("hospital_rejected", "Hospital Rejected"),
        ("inventory_added", "Inventory Added"),
        ("inventory_updated", "Inventory Updated"),
        ("donation_approved", "Donation Approved"),
        ("donation_rejected", "Donation Rejected"),
        ("donation_completed", "Donation Completed"),
        ("request_created", "Request Created"),
        ("request_approved", "Request Approved"),
        ("request_rejected", "Request Rejected"),
        ("request_fulfilled", "Request Fulfilled"),
        ("fraud_resolved", "Fraud Flag Resolved"),
        ("slot_created", "Donation Slot Created"),
        ("slot_updated", "Donation Slot Updated"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions",
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, help_text="e.g. User, Donor, BloodRequest")
    target_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.action}] by {self.actor} on {self.target_type}#{self.target_id}"

    @classmethod
    def log(cls, actor, action, target_type, target_id=None, details="", request=None):
        ip = None
        if request:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
            if ip and "," in ip:
                ip = ip.split(",")[0].strip()
        return cls.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip,
        )
