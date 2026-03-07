"""
Management command to flush and re-seed the database with Nepal-context demo data.

Usage:
    py manage.py seed_demo_data
"""
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Flush all data and populate with Nepal-context demo data for development/ML testing."

    def handle(self, *args, **options):
        from django.core.management import call_command
        from users.models import User
        from donors.models import Donor
        from hospitals.models import Hospital
        from inventory.models import BloodInventory
        from donations.models import DonationSlot, DonationHistory
        from requests.models import BloodRequest
        from fraud.models import FraudLog

        self.stdout.write(self.style.WARNING("Flushing all existing data..."))
        call_command("flush", "--no-input", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Database flushed.\n"))

        today = timezone.now().date()

        # ── Admin ──────────────────────────────────────────────────────────────
        admin_user = User.objects.create_superuser(
            email="jenish.thapa@bloodbank.com",
            password="admin123",
            phone="9841000001",
            role="admin",
            is_approved=True,
        )
        self.stdout.write(f"Admin    : {admin_user.email} / admin123")

        # ── Donors ─────────────────────────────────────────────────────────────
        donors_data = [
            {
                "email": "jiten.rai@example.com", "phone": "9841100001",
                "full_name": "Jiten Rai", "dob": datetime.date(1996, 4, 18),
                "gender": "M", "blood_group": "O+",
                "city": "Dharan", "address": "Bhanu Chowk, Dharan-10",
                "eligible": True, "last_donation": None,
            },
            {
                "email": "sita.gurung@example.com", "phone": "9851200002",
                "full_name": "Sita Gurung", "dob": datetime.date(1993, 9, 5),
                "gender": "F", "blood_group": "A+",
                "city": "Pokhara", "address": "Lakeside Road, Pokhara-6",
                "eligible": True, "last_donation": None,
            },
            {
                "email": "bishal.tamang@example.com", "phone": "9808300003",
                "full_name": "Bishal Tamang", "dob": datetime.date(1990, 12, 25),
                "gender": "M", "blood_group": "B+",
                "city": "Kathmandu", "address": "Balkhu, Kathmandu-15",
                "eligible": True, "last_donation": None,
            },
            {
                "email": "anita.shrestha@example.com", "phone": "9862400004",
                "full_name": "Anita Shrestha", "dob": datetime.date(1999, 6, 12),
                "gender": "F", "blood_group": "AB+",
                "city": "Lalitpur", "address": "Pulchowk, Lalitpur-3",
                "eligible": True, "last_donation": None,
            },
            {
                "email": "roshan.karki@example.com", "phone": "9823500005",
                "full_name": "Roshan Karki", "dob": datetime.date(1987, 2, 28),
                "gender": "M", "blood_group": "O-",
                "city": "Biratnagar", "address": "Traffic Chowk, Biratnagar-4",
                "eligible": False,
                "last_donation": today - datetime.timedelta(days=45),
            },
            {
                "email": "kabita.limbu@example.com", "phone": "9774600006",
                "full_name": "Kabita Limbu", "dob": datetime.date(2000, 11, 3),
                "gender": "F", "blood_group": "B-",
                "city": "Itahari", "address": "Madan Chowk, Itahari-2",
                "eligible": True,
                "last_donation": today - datetime.timedelta(days=120),
            },
            {
                "email": "suraj.adhikari@example.com", "phone": "9745700007",
                "full_name": "Suraj Adhikari", "dob": datetime.date(1994, 7, 19),
                "gender": "M", "blood_group": "A-",
                "city": "Butwal", "address": "Traffick Chowk, Butwal-11",
                "eligible": True, "last_donation": None,
            },
            {
                "email": "deepa.rana@example.com", "phone": "9866800008",
                "full_name": "Deepa Rana", "dob": datetime.date(1997, 3, 8),
                "gender": "F", "blood_group": "A+",
                "city": "Kathmandu", "address": "Baneshwor, Kathmandu-10",
                "eligible": True, "last_donation": None,
            },
        ]

        donor_objects = {}
        for d in donors_data:
            user = User.objects.create_user(
                email=d["email"], password="donor123",
                phone=d["phone"], role="donor", is_approved=True,
            )
            donor_obj = Donor.objects.create(
                user=user,
                full_name=d["full_name"],
                date_of_birth=d["dob"],
                gender=d["gender"],
                blood_group=d["blood_group"],
                city=d["city"],
                address=d["address"],
                is_eligible=d["eligible"],
                last_donation_date=d["last_donation"],
            )
            donor_objects[d["email"]] = donor_obj
            tag = "eligible" if d["eligible"] else "INELIGIBLE"
            self.stdout.write(f"Donor    : {user.email} / donor123  ({d['blood_group']}, {tag})")

        # ── Hospitals ──────────────────────────────────────────────────────────
        hospitals_data = [
            {
                "email": "bir.hospital@example.com", "phone": "014221119",
                "name": "Bir Hospital", "reg": "HOSP-NP-001",
                "city": "Kathmandu", "address": "Mahabauddha, Kathmandu-1",
                "contact": "Dr. Ramesh Poudel", "verified": True,
            },
            {
                "email": "gandaki.hospital@example.com", "phone": "061520066",
                "name": "Gandaki Medical College", "reg": "HOSP-NP-002",
                "city": "Pokhara", "address": "Prithivi Chowk, Pokhara-11",
                "contact": "Dr. Sunita Thapa", "verified": True,
            },
            {
                "email": "koshi.hospital@example.com", "phone": "021525883",
                "name": "Koshi Hospital", "reg": "HOSP-NP-003",
                "city": "Biratnagar", "address": "BP Koirala Way, Biratnagar-2",
                "contact": "Dr. Anil Yadav", "verified": False,
            },
            {
                "email": "patan.hospital@example.com", "phone": "015522266",
                "name": "Patan Hospital", "reg": "HOSP-NP-004",
                "city": "Lalitpur", "address": "Lagankhel, Lalitpur-5",
                "contact": "Dr. Nisha Maharjan", "verified": True,
            },
        ]

        hospital_objects = {}
        for h in hospitals_data:
            user = User.objects.create_user(
                email=h["email"], password="hospital123",
                phone=h["phone"], role="hospital", is_approved=True,
            )
            hosp_obj = Hospital.objects.create(
                user=user,
                name=h["name"],
                registration_number=h["reg"],
                city=h["city"],
                address=h["address"],
                contact_person=h["contact"],
                is_verified=h["verified"],
            )
            hospital_objects[h["email"]] = hosp_obj
            status_str = "verified" if h["verified"] else "pending"
            self.stdout.write(f"Hospital : {user.email} / hospital123  ({status_str})")

        # ── Inventory ──────────────────────────────────────────────────────────
        inventory_items = [
            ("A+",  "whole",     12, today - datetime.timedelta(days=3),  today + datetime.timedelta(days=39)),
            ("A+",  "rbc",        5, today - datetime.timedelta(days=8),  today + datetime.timedelta(days=34)),
            ("O+",  "whole",     10, today - datetime.timedelta(days=5),  today + datetime.timedelta(days=37)),
            ("O+",  "platelets",  4, today - datetime.timedelta(days=1),  today + datetime.timedelta(days=6)),
            ("B+",  "whole",      8, today - datetime.timedelta(days=12), today + datetime.timedelta(days=30)),
            ("B+",  "plasma",     3, today - datetime.timedelta(days=7),  today + datetime.timedelta(days=35)),
            ("AB+", "whole",      6, today - datetime.timedelta(days=4),  today + datetime.timedelta(days=38)),
            ("AB-", "plasma",     2, today - datetime.timedelta(days=2),  today + datetime.timedelta(days=5)),
            ("O-",  "whole",      5, today - datetime.timedelta(days=9),  today + datetime.timedelta(days=33)),
            ("A-",  "rbc",        3, today - datetime.timedelta(days=6),  today + datetime.timedelta(days=36)),
            # Expiring soon
            ("B-",  "platelets",  2, today - datetime.timedelta(days=35), today + datetime.timedelta(days=4)),
            ("O+",  "rbc",        1, today - datetime.timedelta(days=38), today + datetime.timedelta(days=3)),
            # Expired (for admin expiry review testing)
            ("A+",  "whole",      2, today - datetime.timedelta(days=50), today - datetime.timedelta(days=8)),
        ]

        for bg, bt, qty, col, exp in inventory_items:
            is_avail = exp >= today
            BloodInventory.objects.create(
                blood_group=bg, blood_type=bt, quantity_units=qty,
                collection_date=col, expiry_date=exp, is_available=is_avail,
            )
        self.stdout.write(f"Inventory: {len(inventory_items)} items created")

        # ── Donation Slots ─────────────────────────────────────────────────────
        slot_schedule = [
            (today + datetime.timedelta(days=1), datetime.time(9, 0),  10),
            (today + datetime.timedelta(days=1), datetime.time(14, 0),  8),
            (today + datetime.timedelta(days=3), datetime.time(10, 0), 10),
            (today + datetime.timedelta(days=5), datetime.time(9, 30), 12),
            (today + datetime.timedelta(days=7), datetime.time(11, 0),  8),
            # Past slot (auto-deactivated by model save)
            (today - datetime.timedelta(days=2), datetime.time(9, 0),   5),
        ]

        slots = []
        for slot_date, slot_time, capacity in slot_schedule:
            slot = DonationSlot.objects.create(
                date=slot_date, time=slot_time,
                max_capacity=capacity, booked_count=0, is_active=True,
            )
            slots.append(slot)
        self.stdout.write(f"Donation Slots: {len(slots)} created ({len(slots)-1} upcoming, 1 past)")

        # ── Donation History ───────────────────────────────────────────────────
        future_slots = [s for s in slots if s.date >= today]

        history_entries = [
            ("jiten.rai@example.com",      future_slots[0], "O+", 1, "pending",   None),
            ("sita.gurung@example.com",    future_slots[1], "A+", 1, "approved",  None),
            ("bishal.tamang@example.com",  future_slots[0], "B+", 1, "completed",
             timezone.now() - datetime.timedelta(days=95)),
            ("kabita.limbu@example.com",   future_slots[2], "B-", 1, "pending",   None),
            ("suraj.adhikari@example.com", future_slots[3], "A-", 1, "pending",   None),
            ("deepa.rana@example.com",     future_slots[0], "A+", 1, "cancelled", None),
        ]

        for donor_email, slot, bg, units, status, donated_at in history_entries:
            donor_obj = donor_objects[donor_email]
            DonationHistory.objects.create(
                donor=donor_obj, slot=slot, blood_group=bg,
                units_donated=units, status=status, donated_at=donated_at,
            )
            if status in ("pending", "approved"):
                slot.booked_count += 1
                slot.save()
        self.stdout.write(f"Donation History: {len(history_entries)} entries created")

        # ── Blood Requests ─────────────────────────────────────────────────────
        bir     = hospital_objects["bir.hospital@example.com"]
        gandaki = hospital_objects["gandaki.hospital@example.com"]
        koshi   = hospital_objects["koshi.hospital@example.com"]
        patan   = hospital_objects["patan.hospital@example.com"]

        blood_requests = [
            (bir,     "O+",  4, "critical", "pending",   "Dipak Thapa",    "Road accident emergency",       today + datetime.timedelta(days=1)),
            (bir,     "A+",  2, "urgent",   "pending",   "Sunita Basnet",  "Post-operative transfusion",    today + datetime.timedelta(days=2)),
            (gandaki, "B+",  3, "normal",   "approved",  "Hari Adhikari",  "Scheduled surgery",             today + datetime.timedelta(days=5)),
            (patan,   "AB+", 2, "urgent",   "pending",   "Mina Shrestha",  "Thalassemia treatment",         today + datetime.timedelta(days=3)),
            (koshi,   "O-",  1, "critical", "pending",   "Ramesh Yadav",   "Acute blood loss",              today + datetime.timedelta(days=1)),
            (bir,     "A+",  3, "normal",   "fulfilled", "Pratima Karki",  "Elective procedure",            today - datetime.timedelta(days=3)),
            (gandaki, "O+",  2, "normal",   "rejected",  "Bikash Limbu",   "Request outside service area",  today - datetime.timedelta(days=5)),
            (patan,   "B-",  1, "urgent",   "approved",  "Laxmi Tamang",   "Haemophilia complication",      today + datetime.timedelta(days=4)),
        ]

        for hosp, bg, units, urgency, status, patient, reason, req_by in blood_requests:
            BloodRequest.objects.create(
                hospital=hosp, blood_group=bg, units_required=units,
                urgency=urgency, status=status,
                patient_name=patient, reason=reason, required_by=req_by,
            )
        self.stdout.write(f"Blood Requests: {len(blood_requests)} created")

        # ── Fraud Logs ─────────────────────────────────────────────────────────
        jiten_user  = donor_objects["jiten.rai@example.com"].user
        roshan_user = donor_objects["roshan.karki@example.com"].user
        bishal_user = donor_objects["bishal.tamang@example.com"].user

        fraud_entries = [
            (roshan_user, "donation_frequency", "high",   78,
             "Donor attempted to book a slot only 45 days after last donation (within 90-day restriction).",
             "192.168.1.42"),
            (jiten_user,  "donation_frequency", "low",    22,
             "Donor has 3 bookings in the past 10 months — approaching annual limit.",
             "192.168.1.55"),
            (bishal_user, "suspicious_pattern", "medium", 55,
             "Multiple slot booking attempts detected within a short time window.",
             "10.0.0.17"),
        ]

        for user_obj, flag_type, severity, score, desc, ip in fraud_entries:
            FraudLog.objects.create(
                user=user_obj, flag_type=flag_type, severity=severity,
                risk_score=score, description=desc, ip_address=ip,
            )
        self.stdout.write(f"Fraud Logs: {len(fraud_entries)} entries created")

        # ── Summary ────────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n=== Demo Data Created Successfully ==="))
        self.stdout.write("\n── LOGIN CREDENTIALS ──────────────────────────────────")
        self.stdout.write("  Admin    : jenish.thapa@bloodbank.com       / admin123")
        self.stdout.write("  Donor    : jiten.rai@example.com            / donor123  (O+, eligible)")
        self.stdout.write("  Donor    : sita.gurung@example.com          / donor123  (A+, eligible)")
        self.stdout.write("  Donor    : bishal.tamang@example.com        / donor123  (B+, eligible)")
        self.stdout.write("  Donor    : anita.shrestha@example.com       / donor123  (AB+, eligible)")
        self.stdout.write("  Donor    : roshan.karki@example.com         / donor123  (O-, INELIGIBLE)")
        self.stdout.write("  Donor    : kabita.limbu@example.com         / donor123  (B-, eligible)")
        self.stdout.write("  Donor    : suraj.adhikari@example.com       / donor123  (A-, eligible)")
        self.stdout.write("  Donor    : deepa.rana@example.com           / donor123  (A+, eligible)")
        self.stdout.write("  Hospital : bir.hospital@example.com         / hospital123  (verified)")
        self.stdout.write("  Hospital : gandaki.hospital@example.com     / hospital123  (verified)")
        self.stdout.write("  Hospital : koshi.hospital@example.com       / hospital123  (pending)")
        self.stdout.write("  Hospital : patan.hospital@example.com       / hospital123  (verified)")
        self.stdout.write("───────────────────────────────────────────────────────")
