"""
fraud/ml.py  —  Isolation Forest anomaly detection for donor activity.

Features extracted per donor
─────────────────────────────
  1. total_donations         – completed donation count
  2. frequency_per_year      – completed donations / years since registration
  3. avg_interval_days       – mean days between consecutive completed donations
  4. total_units_donated     – sum of units from all completed donations
  5. registration_age_days   – days since the account was created
  6. days_since_last_donation– days since donor.last_donation_date (9999 if never)
  7. pending_bookings_count  – current pending + approved bookings

Public API
──────────
  build_feature_matrix()        → (donor_ids, numpy array)
  train_and_save()              → fitted IsolationForest + StandardScaler
  load_model()                  → (IsolationForest, StandardScaler) | (None, None)
  score_donor(donor)            → int   risk score 0-100
  run_full_analysis(triggered_by=None)
                                → list[FraudLog]  newly created logs
  score_and_flag_donor(donor, triggered_by=None)
                                → FraudLog | None  (on-demand, per booking)
"""

import os
import pickle
import datetime
import numpy as np

from django.conf import settings
from django.utils import timezone

# ── Paths ───────────────────────────────────────────────────────────────────
_ML_DIR = os.path.join(settings.MEDIA_ROOT, "ml")
_MODEL_PATH = os.path.join(_ML_DIR, "isolation_forest.pkl")

# ── Thresholds ───────────────────────────────────────────────────────────────
FLAG_THRESHOLD = 40          # risk_score >= this → create FraudLog
CONTAMINATION = 0.2          # expected anomaly fraction (20%)


# ── Feature Extraction ───────────────────────────────────────────────────────

def _donor_features(donor) -> list:
    """Return the 7-element feature vector for one Donor instance."""
    from donations.models import DonationHistory

    today = timezone.now().date()

    # Completed donations only
    completed = list(
        DonationHistory.objects.filter(donor=donor, status="completed")
        .order_by("donated_at")
        .values_list("donated_at", "units_donated")
    )

    total_donations = len(completed)
    total_units = sum(u for _, u in completed) if completed else 0

    # Registration age in days
    reg_date = donor.user.date_joined.date() if donor.user.date_joined else today
    registration_age_days = max((today - reg_date).days, 1)

    # Frequency per year
    years_registered = registration_age_days / 365.25
    frequency_per_year = total_donations / max(years_registered, 0.5)

    # Average interval between consecutive donations
    if len(completed) >= 2:
        dates = [dt.date() if dt else today for dt, _ in completed]
        intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        avg_interval_days = float(np.mean(intervals))
    else:
        avg_interval_days = 0.0

    # Days since last donation
    if donor.last_donation_date:
        days_since_last_donation = (today - donor.last_donation_date).days
    else:
        days_since_last_donation = 9999

    # Active (pending + approved) bookings right now
    pending_bookings_count = DonationHistory.objects.filter(
        donor=donor, status__in=["pending", "approved"]
    ).count()

    return [
        float(total_donations),
        float(frequency_per_year),
        float(avg_interval_days),
        float(total_units),
        float(registration_age_days),
        float(days_since_last_donation),
        float(pending_bookings_count),
    ]


FEATURE_NAMES = [
    "total_donations",
    "frequency_per_year",
    "avg_interval_days",
    "total_units_donated",
    "registration_age_days",
    "days_since_last_donation",
    "pending_bookings_count",
]


def build_feature_matrix():
    """
    Build the feature matrix over ALL donors.

    Returns
    -------
    donor_ids : list[int]
    X         : np.ndarray shape (n_donors, 7)
    """
    from donors.models import Donor

    donors = list(Donor.objects.select_related("user").all())
    if not donors:
        return [], np.empty((0, len(FEATURE_NAMES)))

    rows = []
    ids = []
    for donor in donors:
        rows.append(_donor_features(donor))
        ids.append(donor.pk)

    return ids, np.array(rows, dtype=float)


# ── Model Persistence ────────────────────────────────────────────────────────

def save_model(clf, scaler):
    os.makedirs(_ML_DIR, exist_ok=True)
    with open(_MODEL_PATH, "wb") as f:
        pickle.dump({"clf": clf, "scaler": scaler}, f)


def load_model():
    """Return (clf, scaler) or (None, None) if no model has been saved yet."""
    if not os.path.exists(_MODEL_PATH):
        return None, None
    try:
        with open(_MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        return bundle["clf"], bundle["scaler"]
    except Exception:
        return None, None


# ── Training ─────────────────────────────────────────────────────────────────

def train_and_save():
    """
    Train Isolation Forest on all donors, persist, and return (clf, scaler).
    Falls back gracefully when fewer than 2 donors exist.
    """
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    donor_ids, X = build_feature_matrix()
    if len(donor_ids) < 2:
        return None, None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use min(contamination, 0.5 − ε) to avoid sklearn errors with tiny datasets
    n = len(donor_ids)
    effective_contamination = min(CONTAMINATION, max(1 / n, 0.01))

    clf = IsolationForest(
        n_estimators=200,
        contamination=effective_contamination,
        random_state=42,
        max_samples="auto",
    )
    clf.fit(X_scaled)

    save_model(clf, scaler)
    return clf, scaler


# ── Scoring ──────────────────────────────────────────────────────────────────

def _decision_score_to_risk(decision_score: float) -> int:
    """
    Convert Isolation Forest decision_function output to a 0-100 risk integer.

    decision_function() is positive for inliers, negative for outliers.
    We invert and sigmoid-normalise so that:
        very anomalous  →  risk close to 100
        very normal     →  risk close to 0
    """
    # Sigmoid inversion: f(x) = 1 / (1 + e^(3*x))
    risk_float = 1.0 / (1.0 + np.exp(3.0 * decision_score))
    return int(np.clip(risk_float * 100, 0, 100))


def score_donor(donor) -> int:
    """
    Score a single donor against the persisted model.

    Returns a risk integer 0-100.  If no model is found, trains one first.
    """
    clf, scaler = load_model()
    if clf is None:
        clf, scaler = train_and_save()
    if clf is None:
        return 0

    features = np.array([_donor_features(donor)], dtype=float)
    X_scaled = scaler.transform(features)
    raw = clf.decision_function(X_scaled)[0]
    return _decision_score_to_risk(raw)


def _severity_from_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


# ── Full-Population Analysis ─────────────────────────────────────────────────

def run_full_analysis(triggered_by=None):
    """
    Train the model on current data, score every donor, and create FraudLog
    entries for donors whose risk_score >= FLAG_THRESHOLD.

    Existing unresolved ml_anomaly logs for the same user are updated in-place
    rather than duplicated.

    Parameters
    ----------
    triggered_by : User instance | None  (admin who triggered the run)

    Returns
    -------
    list[FraudLog]  – newly created or updated log entries
    """
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from donors.models import Donor
    from .models import FraudLog

    donor_ids, X = build_feature_matrix()
    if len(donor_ids) < 2:
        return []

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n = len(donor_ids)
    effective_contamination = min(CONTAMINATION, max(1 / n, 0.01))

    clf = IsolationForest(
        n_estimators=200,
        contamination=effective_contamination,
        random_state=42,
        max_samples="auto",
    )
    clf.fit(X_scaled)
    save_model(clf, scaler)

    raw_scores = clf.decision_function(X_scaled)
    risk_scores = [_decision_score_to_risk(s) for s in raw_scores]

    donors = {d.pk: d for d in Donor.objects.select_related("user").filter(pk__in=donor_ids)}

    created_or_updated = []
    for donor_id, risk_score in zip(donor_ids, risk_scores):
        if risk_score < FLAG_THRESHOLD:
            continue

        donor = donors[donor_id]
        severity = _severity_from_score(risk_score)
        features = _donor_features(donor)
        description = (
            f"[ML Anomaly] Isolation Forest flagged this donor.\n"
            f"  Risk score    : {risk_score}/100\n"
            f"  Completed donations    : {int(features[0])}\n"
            f"  Frequency / year       : {features[1]:.2f}\n"
            f"  Avg interval (days)    : {features[2]:.0f}\n"
            f"  Total units donated    : {int(features[3])}\n"
            f"  Account age (days)     : {int(features[4])}\n"
            f"  Days since last donate : {int(features[5]) if features[5] < 9000 else 'Never'}\n"
            f"  Pending bookings now   : {int(features[6])}"
        )

        existing = FraudLog.objects.filter(
            user=donor.user,
            flag_type="ml_anomaly",
            is_resolved=False,
        ).first()

        if existing:
            existing.risk_score = risk_score
            existing.severity = severity
            existing.description = description
            existing.save(update_fields=["risk_score", "severity", "description"])
            created_or_updated.append(existing)
        else:
            log = FraudLog.objects.create(
                user=donor.user,
                flag_type="ml_anomaly",
                severity=severity,
                risk_score=risk_score,
                description=description,
            )
            created_or_updated.append(log)

    return created_or_updated


# ── Per-Booking On-Demand Scoring ────────────────────────────────────────────

def score_and_flag_donor(donor, triggered_by=None):
    """
    Score a single donor after a new booking and create / update a FraudLog
    entry only if the risk_score >= FLAG_THRESHOLD.

    Called from donations.views.book_slot after each new booking.

    Returns the FraudLog instance or None.
    """
    from .models import FraudLog

    risk_score = score_donor(donor)
    if risk_score < FLAG_THRESHOLD:
        return None

    severity = _severity_from_score(risk_score)
    features = _donor_features(donor)
    description = (
        f"[ML Anomaly – on booking] Risk score: {risk_score}/100\n"
        f"  Completed donations    : {int(features[0])}\n"
        f"  Frequency / year       : {features[1]:.2f}\n"
        f"  Avg interval (days)    : {features[2]:.0f}\n"
        f"  Total units donated    : {int(features[3])}\n"
        f"  Account age (days)     : {int(features[4])}\n"
        f"  Days since last donate : {int(features[5]) if features[5] < 9000 else 'Never'}\n"
        f"  Pending bookings now   : {int(features[6])}"
    )

    existing = FraudLog.objects.filter(
        user=donor.user,
        flag_type="ml_anomaly",
        is_resolved=False,
    ).first()

    if existing:
        existing.risk_score = risk_score
        existing.severity = severity
        existing.description = description
        existing.save(update_fields=["risk_score", "severity", "description"])
        return existing

    return FraudLog.objects.create(
        user=donor.user,
        flag_type="ml_anomaly",
        severity=severity,
        risk_score=risk_score,
        description=description,
    )
