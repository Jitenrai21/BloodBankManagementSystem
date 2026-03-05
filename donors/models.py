from django.db import models
from django.conf import settings


class Donor(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_eligible = models.BooleanField(default=True)
    last_donation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.blood_group})"

