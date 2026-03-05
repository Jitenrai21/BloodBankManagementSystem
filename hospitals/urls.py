from django.urls import path
from . import views

app_name = "hospitals"

urlpatterns = [
    path("", views.hospital_list, name="list"),
    path("profile/", views.hospital_profile, name="profile"),
    path("register/", views.hospital_register, name="register"),
    path("<int:pk>/verify/", views.verify_hospital, name="verify"),
]
