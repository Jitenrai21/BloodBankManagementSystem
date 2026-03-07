# Blood Bank Management System

A Django-based web application for managing blood bank operations — donors, hospitals, inventory, donation slots, blood requests, and ML-powered fraud detection.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Demo Data](#demo-data)
- [Usage Guide](#usage-guide)
- [ML Anomaly Detection](#ml-anomaly-detection)
- [REST API](#rest-api)
- [Management Commands](#management-commands)
- [Default Credentials](#default-credentials)

---

## Overview

The Blood Bank Management System supports three user roles — **Admin**, **Donor**, and **Hospital** — each with a dedicated dashboard and workflow. It tracks blood inventory with expiry management, manages donation slots with auto-expiry, processes hospital blood requests, and uses an **Isolation Forest** ML model to detect anomalous donor behaviour and flag potential fraud.

---

## Key Features

### Admin
- Dashboard with live alerts: critical inventory, pending bookings, urgent blood requests
- Approve / reject / complete donor bookings
- Manage blood inventory (add, update, expiry tracking)
- Verify hospitals and approve user registrations
- Manage blood requests (approve, reject, fulfil)
- Full audit log of all system actions
- **Run ML anomaly analysis** directly from the Fraud Alerts page
- Review and resolve fraud / anomaly flags

### Donor
- Register profile with blood group, address, and eligibility
- Browse and book available donation slots
- View personal donation history
- Notified if booking triggers a high-severity ML anomaly flag

### Hospital
- Register and await admin verification
- Submit blood requests (urgency: normal / urgent / critical)
- Track request status (pending → approved → fulfilled)

### Inventory
- Track blood units by group (A+, A−, B+, B−, AB+, AB−, O+, O−) and type (whole, RBC, plasma, platelets)
- Auto-marks units as unavailable when expiry date passes
- Expiry alert panel for stock expiring within 7 days

### Donation Slots
- Admin creates time-limited slots with capacity caps
- Slots auto-deactivate once their date/time passes (on page load and model save)
- Booking prevents overbooking via atomic transaction
- Donor eligibility enforced (90-day minimum gap between donations)

### Fraud Detection (ML)
- Isolation Forest trained on 7 donor behavioural features
- Flags anomalous donors with a 0–100 risk score
- Logs stored in `FraudLog` with severity (low / medium / high)
- Triggered on-demand by admin or automatically on each booking

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.2 |
| API | Django REST Framework 3.16.1 |
| ML | scikit-learn 1.8.0, numpy 2.4.2 |
| Database | SQLite (development) |
| Frontend | Django templates, custom CSS |
| Auth | Custom `AbstractBaseUser` with email login |

---

## Project Structure

```
Blood_Bank_Management_System/
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── blood_bank/                  # Django project config
│   ├── settings.py
│   ├── urls.py                  # Root URL conf
│   ├── api_urls.py              # REST API root
│   ├── api_views.py
│   ├── serializers.py
│   ├── asgi.py
│   └── wsgi.py
│
├── users/                       # Auth, roles, dashboards
│   ├── models.py                # Custom User (email-based)
│   ├── views.py                 # Login, register, dashboards
│   ├── forms.py
│   ├── decorators.py            # @admin_required, @donor_required, etc.
│   ├── urls.py
│   ├── api_urls.py
│   ├── api_views.py
│   └── migrations/
│
├── donors/                      # Donor profiles
│   ├── models.py                # Donor (blood group, eligibility, last donation)
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
│
├── hospitals/                   # Hospital profiles & verification
│   ├── models.py                # Hospital (registration number, verified flag)
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
│
├── inventory/                   # Blood stock management
│   ├── models.py                # BloodInventory (auto-expiry on save)
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
│
├── donations/                   # Slots & donation history
│   ├── models.py                # DonationSlot (auto-deactivate), DonationHistory
│   ├── views.py                 # book_slot triggers ML scoring on each booking
│   ├── forms.py
│   ├── urls.py
│   ├── migrations/
│   └── management/
│       └── commands/
│           └── seed_demo_data.py   # Seed Nepal-context demo data
│
├── requests/                    # Hospital blood requests
│   ├── models.py                # BloodRequest (urgency, status)
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
│
├── fraud/                       # Fraud detection & ML
│   ├── models.py                # FraudLog (flag_type, severity, risk_score)
│   ├── ml.py                    # Isolation Forest — feature extraction, training, scoring
│   ├── views.py                 # fraud_log_list, run_ml_analysis, resolve_flag
│   ├── urls.py
│   ├── migrations/
│   └── management/
│       └── commands/
│           └── run_fraud_ml.py  # CLI: train + score all donors
│
├── audit/                       # Audit trail
│   ├── models.py                # AuditLog (action, model, actor, timestamp)
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│
├── scripts/
│   └── create_demo_data.py      # Standalone reference script (use management command instead)
│
├── static/
│   └── css/
│       └── style.css
│
├── templates/
│   ├── base.html
│   ├── audit/list.html
│   ├── donations/
│   │   ├── history.html
│   │   ├── slot_form.html
│   │   └── slot_list.html
│   ├── donors/
│   │   ├── history.html
│   │   ├── list.html
│   │   ├── profile.html
│   │   └── register.html
│   ├── fraud/
│   │   └── list.html            # Fraud alerts + "Run ML Analysis" button
│   ├── hospitals/
│   │   ├── list.html
│   │   ├── profile.html
│   │   └── register.html
│   ├── inventory/
│   │   ├── add.html
│   │   ├── alerts.html
│   │   ├── list.html
│   │   └── update.html
│   ├── requests/
│   │   ├── create.html
│   │   ├── detail.html
│   │   └── list.html
│   └── users/
│       ├── dashboard_admin.html
│       ├── dashboard_donor.html
│       ├── dashboard_hospital.html
│       ├── login.html
│       ├── manage_users.html
│       ├── profile.html
│       └── register.html
│
├── tests/
│   └── test_phase3.py
│
└── media/
    └── ml/
        └── isolation_forest.pkl  # Persisted ML model (auto-created on first run)
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd Blood_Bank_Management_System

# 2. Create and activate virtual environment
python -m venv env
# Windows
env\Scripts\activate
# macOS / Linux
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
py manage.py migrate

# 5. (Optional) Seed Nepal-context demo data
py manage.py seed_demo_data

# 6. Start the development server
py manage.py runserver
```

---

## Demo Data

The `seed_demo_data` management command flushes the database and populates it with realistic Nepal-context records:

| Entity | Count | Details |
|---|---|---|
| Admin | 1 | Jenish Thapa |
| Donors | 8 | Various blood groups; one ineligible |
| Hospitals | 4 | 3 verified, 1 pending |
| Inventory | 13 | Includes expiring-soon and expired items |
| Donation Slots | 6 | 5 upcoming, 1 past (auto-deactivated) |
| Donation History | 6 | Mix of pending / approved / completed / cancelled |
| Blood Requests | 8 | Mix of urgencies and statuses |
| Fraud Logs | 3 | Frequency violation, near-limit warning, suspicious pattern |

```bash
py manage.py seed_demo_data
```

> **Warning:** This command flushes all existing data before seeding.

---

## Usage Guide

### Role Workflows

**Admin**
1. Log in → redirected to Admin Dashboard
2. Review alerts: critical inventory, pending bookings, urgent requests
3. Approve or reject donor booking requests via Donation History
4. Add / update blood inventory items
5. Approve hospital registrations and user accounts
6. Process blood requests from hospitals
7. Navigate to Fraud Alerts → review ML-flagged donors → resolve flags

**Donor**
1. Register → await admin approval
2. Complete donor profile (blood group, city, date of birth)
3. Browse open donation slots → book a slot
4. Track booking status (pending → approved → completed)

**Hospital**
1. Register → await admin verification
2. Submit blood requests with urgency level and patient details
3. Track request status from the hospital dashboard

---

## ML Anomaly Detection

### How It Works

An **Isolation Forest** model is trained on 7 features extracted per donor:

| Feature | Description |
|---|---|
| `total_donations` | Number of completed donations |
| `frequency_per_year` | Donations divided by years since registration |
| `avg_interval_days` | Mean days between consecutive donations |
| `total_units_donated` | Sum of all units donated |
| `registration_age_days` | Days since account creation |
| `days_since_last_donation` | Days since last donation (9999 if never donated) |
| `pending_bookings_count` | Current pending or approved bookings |

Donors with anomalous patterns are assigned a **risk score (0–100)**:

| Score Range | Severity | Action |
|---|---|---|
| 0–39 | — | No flag created |
| 40–49 | Low | FraudLog created silently |
| 50–69 | Medium | FraudLog created silently |
| 70–100 | High | FraudLog created + donor warned on booking |

### Trigger Points

| Trigger | How |
|---|---|
| Admin UI | "Run ML Analysis" button on Fraud Alerts page |
| CLI | `py manage.py run_fraud_ml` |
| Auto on booking | Every `book_slot` call silently scores the donor |

### Model Persistence

The trained model is saved to `media/ml/isolation_forest.pkl`. Subsequent scoring calls reuse this file without retraining. Running "Run ML Analysis" or the management command always retrains with the latest data.

> Accuracy improves as more donation history accumulates — the model learns what "normal" donor behaviour looks like from real data.

---

## REST API

A read-oriented API is available under `/api/`:

| Endpoint | Description |
|---|---|
| `GET /api/inventory/` | List available blood inventory |
| `GET /api/requests/` | List blood requests |
| `GET /api/donors/` | List donors |

Authentication uses Django session auth. Full API routes are defined in `blood_bank/api_urls.py` and `users/api_urls.py`.

---

## Management Commands

```bash
# Seed Nepal-context demo data (flushes DB first)
py manage.py seed_demo_data

# Train Isolation Forest and flag anomalous donors
py manage.py run_fraud_ml

# Train only — save model without creating FraudLog entries
py manage.py run_fraud_ml --train-only

# Score only — use existing saved model, skip retraining
py manage.py run_fraud_ml --score-only
```

---

## Default Credentials

After running `seed_demo_data`:

| Role | Email | Password |
|---|---|---|
| Admin | `jenish.thapa@bloodbank.com` | `admin123` |
| Donor (O+) | `jiten.rai@example.com` | `donor123` |
| Donor (A+) | `sita.gurung@example.com` | `donor123` |
| Donor (B+) | `bishal.tamang@example.com` | `donor123` |
| Donor (AB+) | `anita.shrestha@example.com` | `donor123` |
| Donor (O−, ineligible) | `roshan.karki@example.com` | `donor123` |
| Donor (B−) | `kabita.limbu@example.com` | `donor123` |
| Donor (A−) | `suraj.adhikari@example.com` | `donor123` |
| Donor (A+) | `deepa.rana@example.com` | `donor123` |
| Hospital (verified) | `bir.hospital@example.com` | `hospital123` |
| Hospital (verified) | `gandaki.hospital@example.com` | `hospital123` |
| Hospital (pending) | `koshi.hospital@example.com` | `hospital123` |
| Hospital (verified) | `patan.hospital@example.com` | `hospital123` |
