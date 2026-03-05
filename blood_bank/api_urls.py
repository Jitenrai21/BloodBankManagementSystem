from django.urls import path
from . import api_views

urlpatterns = [
    # Donors
    path("donors/", api_views.DonorListAPI.as_view(), name="api_donors"),
    path("donors/<int:pk>/", api_views.DonorDetailAPI.as_view(), name="api_donor_detail"),
    # Hospitals
    path("hospitals/", api_views.HospitalListAPI.as_view(), name="api_hospitals"),
    path("hospitals/<int:pk>/", api_views.HospitalDetailAPI.as_view(), name="api_hospital_detail"),
    # Inventory
    path("inventory/", api_views.InventoryListAPI.as_view(), name="api_inventory"),
    path("inventory/<int:pk>/", api_views.InventoryDetailAPI.as_view(), name="api_inventory_detail"),
    # Donation Slots
    path("slots/", api_views.SlotListAPI.as_view(), name="api_slots"),
    path("slots/<int:pk>/", api_views.SlotDetailAPI.as_view(), name="api_slot_detail"),
    # Donation History
    path("donations/", api_views.DonationHistoryListAPI.as_view(), name="api_donations"),
    # Blood Requests
    path("requests/", api_views.BloodRequestListAPI.as_view(), name="api_requests"),
    path("requests/<int:pk>/", api_views.BloodRequestDetailAPI.as_view(), name="api_request_detail"),
    path("requests/create/", api_views.BloodRequestCreateAPI.as_view(), name="api_request_create"),
    # Fraud
    path("fraud/", api_views.FraudLogListAPI.as_view(), name="api_fraud"),
    # Audit
    path("audit/", api_views.AuditLogListAPI.as_view(), name="api_audit"),
]
