"""
Create demo data for the Blood Bank Management System.

Usage:
    cd D:\Blood_Bank_Management_System
    env\Scripts\activate
    py manage.py shell < scripts\create_demo_data.py
"""
import datetime
from django.utils import timezone
from users.models import User
from donors.models import Donor
from hospitals.models import Hospital
from inventory.models import BloodInventory
from donations.models import DonationSlot, DonationHistory
from requests.models import BloodRequest
from fraud.models import FraudLog

print("=== Creating Demo Data ===\n")

# ── Users ─────────────────────────────────────────────────────────────────────
admin_user, _ = User.objects.get_or_create(
    email="admin@bloodbank.com",
    defaults={"role": "admin", "is_staff": True, "is_superuser": True,
              "is_approved": True, "phone": "9990000000"},
)
admin_user.set_password("admin123")
admin_user.save()
print(f"Admin  : {admin_user.email} / admin123")

donors_data = [
    {"email": "donor1@example.com", "phone": "9001000001", "full_name": "Rahul Sharma",
     "dob": datetime.date(1995, 3, 15), "gender": "M", "blood_group": "A+",
     "city": "Delhi", "address": "Sector 12, Dwarka"},
    {"email": "donor2@example.com", "phone": "9001000002", "full_name": "Priya Patel",
     "dob": datetime.date(1998, 7, 22), "gender": "F", "blood_group": "O+",
     "city": "Mumbai", "address": "Andheri West"},
    {"email": "donor3@example.com", "phone": "9001000003", "full_name": "Amit Kumar",
     "dob": datetime.date(1990, 1, 10), "gender": "M", "blood_group": "B+",
     "city": "Bangalore", "address": "Koramangala"},
]

for d in donors_data:
    user, _ = User.objects.get_or_create(
        email=d["email"],
        defaults={"role": "donor", "is_approved": True, "phone": d["phone"]},
    )
    user.set_password("donor123")
    user.save()
    Donor.objects.update_or_create(
        user=user,
        defaults={
            "full_name": d["full_name"],
            "date_of_birth": d["dob"],
            "gender": d["gender"],
            "blood_group": d["blood_group"],
            "city": d["city"],
            "address": d["address"],
            "is_eligible": True,
        },
    )
    print(f"Donor  : {user.email} / donor123  ({d['blood_group']})")

# ── Hospitals ─────────────────────────────────────────────────────────────────
hospitals_data = [
    {"email": "hospital1@example.com", "phone": "9002000001",
     "name": "City General Hospital", "reg": "HOSp-001",
     "city": "Delhi", "contact": "Dr. Mehta", "verified": True},
    {"email": "hospital2@example.com", "phone": "9002000002",
     "name": "Green Valley Medical Centre", "reg": "HOSP-002",
     "city": "Mumbai", "contact": "Dr. Desai", "verified": False},
]

for h in hospitals_data:
    user, _ = User.objects.get_or_create(
        email=h["email"],
        defaults={"role": "hospital", "is_approved": True, "phone": h["phone"]},
    )
    user.set_password("hospital123")
    user.save()
    Hospital.objects.update_or_create(
        user=user,
        defaults={
            "name": h["name"],
            "registration_number": h["reg"],
            "city": h["city"],
            "address": f"123 Main Street, {h['city']}",
            "contact_person": h["contact"],
            "is_verified": h["verified"],
        },
    )
    status_str = "verified" if h["verified"] else "pending"
    print(f"Hospital: {user.email} / hospital123  ({status_str})")

# ── Inventory ─────────────────────────────────────────────────────────────────
today = timezone.now().date()
inventory_items = [
    ("A+", "whole", 10, today - datetime.timedelta(days=5), today + datetime.timedelta(days=37)),
    ("O+", "whole", 8, today - datetime.timedelta(days=10), today + datetime.timedelta(days=32)),
    ("B+", "rbc", 5, today - datetime.timedelta(days=20), today + datetime.timedelta(days=22)),
    ("AB-", "plasma", 3, today - datetime.timedelta(days=2), today + datetime.timedelta(days=5)),
    ("O-", "platelets", 2, today - datetime.timedelta(days=1), today + datetime.timedelta(days=4)),
]

for bg, bt, qty, col, exp in inventory_items:
    BloodInventory.objects.create(
        blood_group=bg, blood_type=bt, quantity_units=qty,
        collection_date=col, expiry_date=exp, is_available=True,
    )
print(f"\nInventory: {len(inventory_items)} items created")

# ── Donation Slots ────────────────────────────────────────────────────────────
slots = []
for i in range(3):
    slot = DonationSlot.objects.create(
        date=today + datetime.timedelta(days=i + 1),
        time=datetime.time(9 + i, 0),
        max_capacity=5,
        booked_count=0,
        is_active=True,
    )
    slots.append(slot)
print(f"Donation Slots: {len(slots)} created")

# ── Donation History ──────────────────────────────────────────────────────────
donor1 = Donor.objects.get(user__email="donor1@example.com")
DonationHistory.objects.create(
    donor=donor1, slot=slots[0], blood_group="A+",
    units_donated=1, status="pending",
)
print("Donation History: 1 pending booking")

# ── Blood Requests ────────────────────────────────────────────────────────────
hospital1 = Hospital.objects.get(user__email="hospital1@example.com")
BloodRequest.objects.create(
    hospital=hospital1, blood_group="O+", units_required=3,
    urgency="urgent", status="pending",
    patient_name="Patient A", reason="Emergency surgery",
    required_by=today + datetime.timedelta(days=2),
)
BloodRequest.objects.create(
    hospital=hospital1, blood_group="A+", units_required=2,
    urgency="normal", status="approved",
    patient_name="Patient B", reason="Scheduled transfusion",
    required_by=today + datetime.timedelta(days=7),
)
print("Blood Requests: 2 created (1 pending, 1 approved)")

# ── Fraud Flags ───────────────────────────────────────────────────────────────
FraudLog.objects.create(
    user=donor1.user,
    flag_type="donation_frequency",
    severity="medium",
    risk_score=45,
    description="Donor attempted to book a second donation within 30 days.",
    ip_address="192.168.1.50",
)
print("Fraud Logs: 1 flag created")

print("\n=== Demo Data Created Successfully ===")
print("Admin login:    admin@bloodbank.com / admin123")
print("Donor logins:   donor1@example.com / donor123  (etc.)")
print("Hospital login: hospital1@example.com / hospital123")
