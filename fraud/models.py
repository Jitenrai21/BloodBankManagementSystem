from django.db import models
from django.conf import settings


class FraudLog(models.Model):
    FLAG_TYPE_CHOICES = [
        ('duplicate_email', 'Duplicate Email'),
        ('duplicate_phone', 'Duplicate Phone'),
        ('fuzzy_name_match', 'Fuzzy Name Match'),
        ('donation_frequency', 'Donation Frequency Exceeded'),
        ('multiple_requests_ip', 'Multiple Requests from Same IP'),
        ('suspicious_pattern', 'Suspicious Pattern'),
        ('ml_anomaly', 'ML Anomaly Detected'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fraud_logs'
    )
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    risk_score = models.PositiveSmallIntegerField(default=0, help_text='Risk score 0–100')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_fraud_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity.upper()}] {self.flag_type} - User: {self.user} (Score: {self.risk_score})"

