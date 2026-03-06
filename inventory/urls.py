from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("",                         views.inventory_list,        name="list"),
    path("add/",                     views.inventory_add,         name="add"),
    path("<int:pk>/update/",         views.inventory_update,      name="update"),
    path("<int:pk>/delete/",         views.inventory_delete,      name="delete"),
    path("delete-expired/",          views.delete_expired_bulk,   name="delete_expired"),
    path("alerts/",                  views.expiry_alerts,         name="alerts"),
]
