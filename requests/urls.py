from django.urls import path
from . import views

app_name = "requests"

urlpatterns = [
    path("", views.request_list, name="list"),
    path("create/", views.request_create, name="create"),
    path("<int:pk>/", views.request_detail, name="detail"),
    path("<int:pk>/update/", views.request_update, name="update"),
]
