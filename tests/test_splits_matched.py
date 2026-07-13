"""Toy tests for matched comparison set (Phase 2) and outer splits (Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.matched_cohort import build_matched_manifest, model_input_equality  # noqa: E402
from barrett.data.splits import (  # noqa: E402
    assign_rows_to_folds, make_patient_folds, patient_labels, validate_splits,
)
from barrett.labels.endpoints import LGD2_ENDPOINT

FAMILIES = ["cnv_only", "image_uni2_abmil", "early_fusion"]


def _flagged(n_patients=40):
    rows = []
    for p in range(n_patients):
        rows.append({
            "PatientID_real": f"P{p}", "SampleID": f"S{p}", "BiopsyID_int": p,
            "ImageAbsPath": f"/img/{p}.ndpi", "CNVAbsPath": f"/cnv/{p}.rds",
            LGD2_ENDPOINT: p % 2, "derived_NextBiopsyProgression_LGD2plus": float(p % 2),
            "DaysToNextBiopsy": 100, "DaysFromCurrentToEvent": None,
            "timing_evidence_source": "days_to_next_biopsy_positive",
            "strict_pre_event_eligible": True, "has_image": True, "has_cnv": True,
        })
    return pd.DataFrame(rows)


def test_matched_manifest_one_row_per_sample():
    m, probs = build_matched_manifest(_flagged(), "rel1")
    assert probs == []
    assert m["canonical_row_key"].is_unique and len(m) == 40


def test_matched_manifest_rejects_duplicate_sample():
    f = pd.concat([_flagged(4), _flagged(4).iloc[[0]]], ignore_index=True)
    _, probs = build_matched_manifest(f, "rel1")
    assert any("duplicate" in p for p in probs)


def test_matched_manifest_flags_shared_cnv():
    f = _flagged(4)
    f.loc[1, "CNVAbsPath"] = f.loc[0, "CNVAbsPath"]  # shared CNV across two samples
    m, probs = build_matched_manifest(f, "rel1")
    assert probs == [] and int(m["cnv_shared_with_other_sample"].sum()) == 2


def test_model_input_equality():
    m, _ = build_matched_manifest(_flagged(), "rel1")
    eq = model_input_equality(m, FAMILIES)
    assert eq["equal"] and eq["n_keys"] == 40


def test_splits_deterministic_and_disjoint():
    m, _ = build_matched_manifest(_flagged(50), "rel1")
    labels = patient_labels(m)
    f1 = make_patient_folds(labels, n_folds=5, seed=7)
    f2 = make_patient_folds(labels, n_folds=5, seed=7)
    assert f1.equals(f2)  # deterministic
    assert not f1["patient_id"].duplicated().any()  # each patient one fold
    assert sorted(f1["outer_fold"].unique()) == [1, 2, 3, 4, 5]


def test_splits_validate_and_propagate():
    m, _ = build_matched_manifest(_flagged(50), "rel1")
    labels = patient_labels(m)
    folds = make_patient_folds(labels, n_folds=5, seed=7)
    rows = assign_rows_to_folds(m, folds)
    assert validate_splits(rows, folds) == []  # class presence, completeness, disjoint
    # row-to-patient propagation: every row's fold matches its patient's fold
    pf = dict(zip(folds["patient_id"], folds["outer_fold"]))
    assert (rows["outer_fold"] == rows["patient_id"].map(pf)).all()


def test_splits_detect_cross_fold_patient():
    m, _ = build_matched_manifest(_flagged(50), "rel1")
    labels = patient_labels(m)
    folds = make_patient_folds(labels, n_folds=5, seed=7)
    rows = assign_rows_to_folds(m, folds)
    p0 = rows.iloc[0]["patient_id"]
    other = 1 + (int(rows.iloc[0]["outer_fold"]) % 5)  # a different fold
    extra = rows.iloc[[0]].copy()
    extra["outer_fold"] = other
    extra["canonical_row_key"] = "EXTRA"
    rows2 = pd.concat([rows, extra], ignore_index=True)  # patient p0 now in two folds
    assert any("span multiple" in p for p in validate_splits(rows2, folds))
