"""
Phase 3 — Core integration tests for the Blood Bank Management System.
Run:  py manage.py test tests --verbosity=2
"""
import datetime
from django.test import TestCase, Client
from django.utils import timezone
from users.models import User
from donors.models import Donor
from hospitals.models import Hospital
from inventory.models import BloodInventory
from donations.models import DonationSlot, DonationHistory
from requests.models import BloodRequest
from fraud.models import FraudLog
from audit.models import AuditLog


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_admin(email="admin@test.com"):
    u = User.objects.create_user(email=email, password="pass123",
                                 role="admin", phone="0000000001")
    u.is_approved = True
    u.is_staff = True
    u.save()
    return u


def _make_donor(email="donor@test.com"):
    u = User.objects.create_user(email=email, password="pass123",
                                 role="donor", phone="0000000002")
    u.is_approved = True
    u.save()
    d = Donor.objects.create(
        user=u, full_name="Test Donor",
        date_of_birth=datetime.date(1995, 1, 1),
        gender="M", blood_group="A+",
        city="TestCity", address="123 St",
        is_eligible=True,
    )
    return u, d


def _make_hospital(email="hosp@test.com", verified=True):
    u = User.objects.create_user(email=email, password="pass123",
                                 role="hospital", phone="0000000003")
    u.is_approved = True
    u.save()
    h = Hospital.objects.create(
        user=u, name="Test Hospital", registration_number="REG-001",
        address="456 Ave", city="TestCity",
        contact_person="Dr. Who", is_verified=verified,
    )
    return u, h


# ── Auth Tests ───────────────────────────────────────────────────────────────

class AuthTests(TestCase):
    def test_login_page_loads(self):
        resp = self.client.get("/users/login/")
        self.assertEqual(resp.status_code, 200)

    def test_register_page_loads(self):
        resp = self.client.get("/users/register/")
        self.assertEqual(resp.status_code, 200)

    def test_login_redirect_for_admin(self):
        admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")
        resp = self.client.get("/users/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Admin Dashboard")

    def test_login_redirect_for_donor(self):
        user, _ = _make_donor()
        self.client.login(email="donor@test.com", password="pass123")
        resp = self.client.get("/users/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Donor Dashboard")


# ── Admin User Management Tests ──────────────────────────────────────────────

class AdminUserMgmtTests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")

    def test_manage_users_page(self):
        resp = self.client.get("/users/manage/")
        self.assertEqual(resp.status_code, 200)

    def test_approve_user(self):
        u = User.objects.create_user(email="new@test.com", password="x",
                                     role="hospital", phone="1234")
        resp = self.client.get(f"/users/{u.pk}/approve/")
        self.assertEqual(resp.status_code, 302)
        u.refresh_from_db()
        self.assertTrue(u.is_approved)

    def test_block_unblock_user(self):
        u = User.objects.create_user(email="bl@test.com", password="x",
                                     role="donor", phone="5678")
        self.client.get(f"/users/{u.pk}/block/")
        u.refresh_from_db()
        self.assertFalse(u.is_active)
        self.client.get(f"/users/{u.pk}/unblock/")
        u.refresh_from_db()
        self.assertTrue(u.is_active)


# ── Donor Tests ──────────────────────────────────────────────────────────────

class DonorTests(TestCase):
    def setUp(self):
        self.user, self.donor = _make_donor()
        self.client.login(email="donor@test.com", password="pass123")

    def test_donor_profile_page(self):
        resp = self.client.get("/donors/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Donor")

    def test_donor_register_edit(self):
        resp = self.client.post("/donors/register/", {
            "full_name": "Updated Name",
            "date_of_birth": "1995-01-01",
            "gender": "M",
            "blood_group": "A+",
            "city": "NewCity",
            "address": "999 Blvd",
        })
        self.assertEqual(resp.status_code, 302)
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.full_name, "Updated Name")


# ── Inventory Tests ──────────────────────────────────────────────────────────

class InventoryTests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")

    def test_add_inventory(self):
        today = timezone.now().date()
        resp = self.client.post("/inventory/add/", {
            "blood_group": "O+",
            "blood_type": "whole",
            "quantity_units": 5,
            "collection_date": today.isoformat(),
            "expiry_date": (today + datetime.timedelta(days=42)).isoformat(),
            "is_available": True,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(BloodInventory.objects.count(), 1)

    def test_inventory_list(self):
        resp = self.client.get("/inventory/")
        self.assertEqual(resp.status_code, 200)


# ── Donation Slot & Booking Tests ────────────────────────────────────────────

class DonationTests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.user, self.donor = _make_donor()
        today = timezone.now().date()
        self.slot = DonationSlot.objects.create(
            date=today + datetime.timedelta(days=1),
            time=datetime.time(10, 0),
            max_capacity=2,
            booked_count=0,
            is_active=True,
        )

    def test_slot_list(self):
        self.client.login(email="donor@test.com", password="pass123")
        resp = self.client.get("/donations/slots/")
        self.assertEqual(resp.status_code, 200)

    def test_book_slot(self):
        self.client.login(email="donor@test.com", password="pass123")
        resp = self.client.get(f"/donations/book/{self.slot.pk}/")
        self.assertEqual(resp.status_code, 302)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, 1)
        self.assertEqual(DonationHistory.objects.count(), 1)

    def test_approve_complete_donation(self):
        # Book
        self.client.login(email="donor@test.com", password="pass123")
        self.client.get(f"/donations/book/{self.slot.pk}/")
        donation = DonationHistory.objects.first()
        # Admin approves and completes
        self.client.login(email="admin@test.com", password="pass123")
        self.client.get(f"/donations/{donation.pk}/approve/")
        donation.refresh_from_db()
        self.assertEqual(donation.status, "approved")
        self.client.get(f"/donations/{donation.pk}/complete/")
        donation.refresh_from_db()
        self.assertEqual(donation.status, "completed")
        # Inventory should have 1 unit
        self.assertEqual(BloodInventory.objects.count(), 1)
        # Donor eligibility updated
        self.donor.refresh_from_db()
        self.assertFalse(self.donor.is_eligible)


# ── Blood Request Tests ──────────────────────────────────────────────────────

class BloodRequestTests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.hosp_user, self.hospital = _make_hospital()

    def test_create_request(self):
        self.client.login(email="hosp@test.com", password="pass123")
        today = timezone.now().date()
        resp = self.client.post("/requests/create/", {
            "blood_group": "A+",
            "units_required": 2,
            "urgency": "urgent",
            "patient_name": "Jane Doe",
            "reason": "Surgery",
            "required_by": (today + datetime.timedelta(days=3)).isoformat(),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(BloodRequest.objects.count(), 1)

    def test_fulfill_request_deducts_inventory(self):
        # Create inventory
        today = timezone.now().date()
        BloodInventory.objects.create(
            blood_group="A+", blood_type="whole", quantity_units=5,
            collection_date=today, expiry_date=today + datetime.timedelta(days=42),
            is_available=True,
        )
        # Create request
        br = BloodRequest.objects.create(
            hospital=self.hospital, blood_group="A+", units_required=3,
            urgency="normal", status="approved",
        )
        # Admin fulfills
        self.client.login(email="admin@test.com", password="pass123")
        resp = self.client.post(f"/requests/{br.pk}/update/", {"action": "fulfill"})
        self.assertEqual(resp.status_code, 302)
        br.refresh_from_db()
        self.assertEqual(br.status, "fulfilled")
        inv = BloodInventory.objects.first()
        self.assertEqual(inv.quantity_units, 2)


# ── Fraud Tests ──────────────────────────────────────────────────────────────

class FraudTests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")

    def test_fraud_list(self):
        resp = self.client.get("/fraud/")
        self.assertEqual(resp.status_code, 200)

    def test_resolve_flag(self):
        flag = FraudLog.objects.create(
            flag_type="duplicate_email", severity="low",
            description="Test", risk_score=10,
        )
        resp = self.client.get(f"/fraud/{flag.pk}/resolve/")
        self.assertEqual(resp.status_code, 302)
        flag.refresh_from_db()
        self.assertTrue(flag.is_resolved)


# ── Audit Tests ──────────────────────────────────────────────────────────────

class AuditTests(TestCase):
    def test_audit_log_creation(self):
        admin = _make_admin()
        AuditLog.log(admin, "user_approved", "User", 1, "test detail")
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_audit_page_admin_only(self):
        self.admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")
        resp = self.client.get("/audit/")
        self.assertEqual(resp.status_code, 200)


# ── API Tests ────────────────────────────────────────────────────────────────

class APITests(TestCase):
    def setUp(self):
        self.admin = _make_admin()
        self.client.login(email="admin@test.com", password="pass123")

    def test_api_inventory_list(self):
        resp = self.client.get("/api/inventory/")
        self.assertEqual(resp.status_code, 200)

    def test_api_slots_list(self):
        resp = self.client.get("/api/slots/")
        self.assertEqual(resp.status_code, 200)

    def test_api_donors_list(self):
        resp = self.client.get("/api/donors/")
        self.assertEqual(resp.status_code, 200)

    def test_api_audit_list(self):
        resp = self.client.get("/api/audit/")
        self.assertEqual(resp.status_code, 200)

    def test_api_me(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 200)
