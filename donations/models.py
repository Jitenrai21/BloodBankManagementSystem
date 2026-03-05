from django.db import models
from django.conf import settings


class DonationSlot(models.Model):
    date = models.DateField()
    time = models.TimeField()
    max_capacity = models.PositiveIntegerField(default=10)
    booked_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_full(self):
        return self.booked_count >= self.max_capacity

    def __str__(self):
        return f"Slot {self.date} {self.time} ({self.booked_count}/{self.max_capacity})"


class DonationHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    donor = models.ForeignKey(
        'donors.Donor',
        on_delete=models.CASCADE,
        related_name='donation_history'
    )
    slot = models.ForeignKey(
        DonationSlot,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='donations'
    )
    blood_group = models.CharField(max_length=5)
    units_donated = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    donated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Donation Histories'

    def __str__(self):
        return f"{self.donor} - {self.status} ({self.created_at.date()})"

