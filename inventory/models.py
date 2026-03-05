from django.db import models


class BloodInventory(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    BLOOD_TYPE_CHOICES = [
        ('whole', 'Whole Blood'),
        ('rbc', 'Red Blood Cells'),
        ('plasma', 'Plasma'),
        ('platelets', 'Platelets'),
    ]

    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    blood_type = models.CharField(max_length=20, choices=BLOOD_TYPE_CHOICES, default='whole')
    quantity_units = models.PositiveIntegerField(default=0)
    collection_date = models.DateField()
    expiry_date = models.DateField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Blood Inventory'

    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    def __str__(self):
        return f"{self.blood_group} {self.blood_type} - {self.quantity_units} units (Exp: {self.expiry_date})"

