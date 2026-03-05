from django.db import models


class BloodRequest(models.Model):
    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    units_required = models.PositiveIntegerField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='normal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    patient_name = models.CharField(max_length=150, blank=True)
    reason = models.TextField(blank=True)
    required_by = models.DateField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hospital} - {self.blood_group} x{self.units_required} [{self.urgency}] ({self.status})"

