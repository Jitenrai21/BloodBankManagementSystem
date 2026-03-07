"""
Management command: run_fraud_ml

Trains the Isolation Forest model on current donor data and creates / updates
FraudLog entries for anomalous donors.

Usage:
    py manage.py run_fraud_ml
    py manage.py run_fraud_ml --train-only   # train without flagging
    py manage.py run_fraud_ml --score-only   # score using existing model
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Train Isolation Forest on donor data and flag anomalous donors in FraudLog."

    def add_arguments(self, parser):
        parser.add_argument(
            "--train-only",
            action="store_true",
            help="Train and save the model without creating any FraudLog entries.",
        )
        parser.add_argument(
            "--score-only",
            action="store_true",
            help="Skip training—use the existing saved model to score all donors.",
        )

    def handle(self, *args, **options):
        from donors.models import Donor
        from fraud.ml import (
            build_feature_matrix,
            train_and_save,
            load_model,
            run_full_analysis,
            score_donor,
            FEATURE_NAMES,
            FLAG_THRESHOLD,
        )

        train_only = options["train_only"]
        score_only = options["score_only"]

        # ── Show dataset size ────────────────────────────────────────────────
        donor_ids, X = build_feature_matrix()
        n = len(donor_ids)
        self.stdout.write(f"Donors in dataset : {n}")

        if n < 2:
            self.stdout.write(self.style.WARNING(
                "Need at least 2 donors to train. Exiting."
            ))
            return

        # ── Print feature matrix summary ─────────────────────────────────────
        import numpy as np
        self.stdout.write("\n── Feature Summary ─────────────────────────────────────")
        for i, name in enumerate(FEATURE_NAMES):
            col = X[:, i]
            self.stdout.write(
                f"  {name:<30}  min={col.min():.1f}  max={col.max():.1f}  "
                f"mean={col.mean():.2f}"
            )

        # ── Train ────────────────────────────────────────────────────────────
        if not score_only:
            self.stdout.write("\nTraining Isolation Forest ...", ending=" ")
            clf, scaler = train_and_save()
            self.stdout.write(self.style.SUCCESS("done."))
        else:
            clf, scaler = load_model()
            if clf is None:
                self.stdout.write(self.style.ERROR(
                    "No saved model found. Run without --score-only first."
                ))
                return
            self.stdout.write("Using existing saved model.")

        if train_only:
            self.stdout.write(self.style.SUCCESS("\nModel saved. Exiting (--train-only)."))
            return

        # ── Score and flag ───────────────────────────────────────────────────
        self.stdout.write(f"\nScoring donors (flag threshold: {FLAG_THRESHOLD}) ...")
        logs = run_full_analysis()

        # Print per-donor scores
        from sklearn.preprocessing import StandardScaler as _SS
        from fraud.ml import _decision_score_to_risk
        X_scaled = scaler.transform(X)
        raw_scores = clf.decision_function(X_scaled)

        donors = {d.pk: d for d in Donor.objects.select_related("user").filter(pk__in=donor_ids)}

        self.stdout.write("\n── Per-Donor Scores ────────────────────────────────────")
        for donor_id, raw in sorted(
            zip(donor_ids, raw_scores),
            key=lambda t: _decision_score_to_risk(t[1]),
            reverse=True,
        ):
            risk = _decision_score_to_risk(raw)
            donor = donors[donor_id]
            bar = "█" * (risk // 10) + "░" * (10 - risk // 10)
            flag = " ← FLAGGED" if risk >= FLAG_THRESHOLD else ""
            self.stdout.write(
                f"  {donor.full_name:<25}  [{bar}] {risk:>3}/100{flag}"
            )

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Analysis complete. {len(logs)} FraudLog entr"
            f"{'y' if len(logs)==1 else 'ies'} created/updated. ==="
        ))
