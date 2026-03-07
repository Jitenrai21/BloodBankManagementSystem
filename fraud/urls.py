from django.urls import path
from . import views

app_name = "fraud"

urlpatterns = [
    path("", views.fraud_log_list, name="list"),
    path("run-ml/", views.run_ml_analysis, name="run_ml"),
    path("<int:pk>/resolve/", views.resolve_flag, name="resolve"),
]
