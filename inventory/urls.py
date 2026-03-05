from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_list, name="list"),
    path("add/", views.inventory_add, name="add"),
    path("<int:pk>/update/", views.inventory_update, name="update"),
    path("alerts/", views.expiry_alerts, name="alerts"),
]
