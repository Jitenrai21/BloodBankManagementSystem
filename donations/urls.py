from django.urls import path
from . import views

app_name = "donations"

urlpatterns = [
    path("slots/", views.slot_list, name="slot_list"),
    path("slots/create/", views.slot_create, name="slot_create"),
    path("slots/<int:pk>/edit/", views.slot_edit, name="slot_edit"),
    path("book/<int:slot_id>/", views.book_slot, name="book_slot"),
    path("history/", views.donation_history, name="history"),
    path("<int:pk>/approve/", views.approve_donation, name="approve"),
    path("<int:pk>/reject/", views.reject_donation, name="reject"),
    path("<int:pk>/complete/", views.complete_donation, name="complete"),
]
