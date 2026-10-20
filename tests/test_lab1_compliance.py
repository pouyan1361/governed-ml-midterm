"""
LAB 1 TESTS: data compliance, written as controls.

Two kinds of test live here.

  LIST controls read a list from governance/policy.json and check it was
  enforced. They can only catch what somebody already wrote down.

  DETECTIVE controls look at the data itself and catch what the list missed:
  a column that looks like a ZIP code, a column that parses as dates, a column
  that predicts the label too well, a policy that disagrees with the data
  dictionary.

When a detective control fails, do NOT weaken the control. Complete the policy.

Run:   python -m pytest -q tests/test_lab1_compliance.py
"""
import re

import pandas as pd
import pytest

from src.prepare import LABEL, load_dictionary, load_policy, prepare_data

POLICY = load_policy()


@pytest.fixture(scope="module")
def processed():
    return prepare_data(policy=POLICY)


# ---------------- schema and quality ----------------
def test_required_columns_present(processed):
    required = ["years_licensed", "vehicle_age", "vehicle_value", "annual_mileage_declared",
                "prior_insurer_years", "prior_claims_3y", POLICY["protected_attribute"], LABEL]
    missing = [c for c in required if c not in processed.columns]
    assert not missing, f"Missing required columns: {missing}"


def test_no_missing_values_in_numeric_features(processed):
    numeric = processed.select_dtypes("number")
    bad = numeric.columns[numeric.isna().any()].tolist()
    assert not bad, f"Missing values remain in: {bad}"


def test_value_ranges_are_plausible(processed):
    assert (processed["vehicle_value"] > 0).all(), "Non-positive vehicle value found"
    assert processed["years_licensed"].between(0, 80).all(), "years_licensed outside 0 to 80"
    assert (processed["prior_claims_3y"] >= 0).all(), "Negative claim count"


def test_label_is_binary(processed):
    assert set(processed[LABEL].unique()) <= {0, 1}, "Label must be 0 or 1"


# ---------------- LIST controls ----------------
def test_no_pii_columns(processed):
    """PRIVACY CONTROL (list): nothing in policy pii_columns may reach training."""
    leaked = [c for c in POLICY["pii_columns"] if c in processed.columns]
    assert not leaked, f"PII reached the training data: {leaked}"


def test_no_known_leakage_columns(processed):
    """LEAKAGE CONTROL (list): nothing in policy leakage_columns may reach training."""
    leaked = [c for c in POLICY["leakage_columns"] if c in processed.columns]
    assert not leaked, f"Post-decision columns present: {leaked}"


def test_only_protected_attribute_kept_for_audit(processed):
    """Sensitive attributes other than the audited one must be gone."""
    extra = [c for c in POLICY["sensitive_attributes"]
             if c != POLICY["protected_attribute"] and c in processed.columns]
    assert not extra, f"Sensitive attributes present beyond the audited one: {extra}"


# ---------------- DETECTIVE controls ----------------
def test_no_zip_like_column(processed):
    """DETECTIVE: a column whose values are five-digit codes is a quasi-identifier,
    whatever it is called. The fix is in the policy, not here."""
    suspects = []
    for col in processed.columns:
        s = processed[col].astype(str).head(200)
        if (s.str.fullmatch(r"\d{5}").mean()) > 0.95:
            suspects.append(col)
    assert not suspects, f"ZIP-like quasi-identifier columns reached training: {suspects}"


def test_no_date_like_column(processed):
    """DETECTIVE: a column that parses as calendar dates (birth dates, for
    example) is a quasi-identifier. Add it to the policy."""
    suspects = []
    for col in processed.columns:
        if pd.api.types.is_numeric_dtype(processed[col]):
            continue
        s = processed[col].astype(str).head(200)
        if s.str.fullmatch(r"\d{4}-\d{2}-\d{2}").mean() > 0.95:
            suspects.append(col)
    assert not suspects, f"Date-like quasi-identifier columns reached training: {suspects}"


def test_no_suspiciously_predictive_column(processed):
    """DETECTIVE: a column that predicts the label almost perfectly is usually
    leakage, even if nobody put it on a list."""
    limit = POLICY["max_feature_label_correlation"]
    numeric = processed.select_dtypes("number").drop(columns=[LABEL])
    corr = numeric.corrwith(processed[LABEL]).abs()
    suspicious = corr[corr > limit].round(3).to_dict()
    assert not suspicious, f"Columns correlated with the label above {limit}: {suspicious}"


def test_policy_agrees_with_data_dictionary():
    """DETECTIVE: the data dictionary classifies every raw column. Every column
    the dictionary calls an identifier or quasi-identifier must be in
    pii_columns, and every column classed as a post-year outcome must be in
    leakage_columns. A policy that disagrees with the dictionary is incomplete."""
    dic = load_dictionary()
    ids = dic.loc[dic["class"].isin(["identifier", "quasi-identifier"]), "field"].tolist()
    outcomes = dic.loc[dic["class"] == "outcome", "field"].tolist()
    missing_pii = [c for c in ids if c not in POLICY["pii_columns"]]
    missing_leak = [c for c in outcomes if c not in POLICY["leakage_columns"]]
    assert not missing_pii and not missing_leak, (
        f"Policy is incomplete. Add to pii_columns: {missing_pii}. Add to leakage_columns: {missing_leak}.")


# ---------------- CHANGE / FIX LOG ----------------
# Add a dated entry here whenever a change or fix is made in this repository.
# 2026-10-20: Added this log for tracking future changes and fixes.
# 2026-10-20: Added the change/terminal output log convention to MIDTERM.md.
#             No command run for this documentation-only change.
# 2026-10-20: Recorded pip install output in MIDTERM.md.
# 2026-10-20: Added zip/date_of_birth and adjuster_fraud_review to policy lists;
#             tests/test_lab1_compliance.py passed (11 tests).
# 2026-10-20: Clarified Lab 1 control types and dictionary-based list choices in MIDTERM.md.
