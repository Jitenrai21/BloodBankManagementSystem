from django.urls import path
from . import views

app_name = "donors"

urlpatterns = [
    path("", views.donor_list, name="list"),
    path("profile/", views.donor_profile, name="profile"),
    path("register/", views.donor_register, name="register"),
    path("history/", views.donation_history, name="history"),
]
