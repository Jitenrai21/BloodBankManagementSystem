from django.db import models
from django.conf import settings


class Hospital(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=150)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({'Verified' if self.is_verified else 'Pending'})"

