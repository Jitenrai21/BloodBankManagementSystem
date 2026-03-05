from django.urls import path
from . import views

app_name = "fraud"

urlpatterns = [
    path("", views.fraud_log_list, name="list"),
    path("<int:pk>/resolve/", views.resolve_flag, name="resolve"),
]
