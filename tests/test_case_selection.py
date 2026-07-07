"""Toy-data tests for LGD2+ interpretation case-selection logic."""

import importlib.util
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "select_cases_mod", REPO_ROOT / "scripts" / "05_select_lgd2_interpretation_cases.py"
)
sel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sel)


def toy_wide():
    # patient, true, cnv, image, fusion, days, at_event flag driver
    rows = [
        # A: TP early (true=1, fusion high, days>0)
        dict(patient_id="pA", y_true=1, cnv_prob=0.8, image_prob=0.8, fusion_prob=0.90, rep_days_to_event=300),
        # B: FN (true=1, fusion low)
        dict(patient_id="pB", y_true=1, cnv_prob=0.2, image_prob=0.2, fusion_prob=0.10, rep_days_to_event=200),
        # C: FP (true=0, fusion high)
        dict(patient_id="pC", y_true=0, cnv_prob=0.8, image_prob=0.8, fusion_prob=0.85, rep_days_to_event=200),
        # D: TN (true=0, fusion low)
        dict(patient_id="pD", y_true=0, cnv_prob=0.1, image_prob=0.1, fusion_prob=0.05, rep_days_to_event=200),
        # E: CNV rescue (true=1, cnv correct high, image wrong low, fusion correct)
        dict(patient_id="pE", y_true=1, cnv_prob=0.9, image_prob=0.2, fusion_prob=0.60, rep_days_to_event=200),
        # F: histology rescue (true=1, image correct, cnv wrong, fusion correct)
        dict(patient_id="pF", y_true=1, cnv_prob=0.2, image_prob=0.9, fusion_prob=0.60, rep_days_to_event=200),
        # G: fusion hurt (true=1, a unimodal correct, fusion wrong)
        dict(patient_id="pG", y_true=1, cnv_prob=0.9, image_prob=0.9, fusion_prob=0.30, rep_days_to_event=200),
        # at-event TP (days==0) should be flagged
        dict(patient_id="pZ", y_true=1, cnv_prob=0.9, image_prob=0.9, fusion_prob=0.95, rep_days_to_event=0),
    ]
    w = pd.DataFrame(rows)
    w["analysis_set"] = "early_prediction_only"
    return w


def run(wide, at_event=None):
    if at_event is None:
        at_event = pd.Series({p: False for p in wide["patient_id"]})
    return pd.DataFrame(sel.select_cases(wide, at_event, clin_thr=None))


def cats(cases, cat):
    return set(cases[cases["case_category"].eq(cat)]["patient_id"])


def test_true_positive_early_selected():
    cases = run(toy_wide())
    assert "pA" in cats(cases, "A_true_positive_early")


def test_false_negative_selected():
    cases = run(toy_wide())
    assert "pB" in cats(cases, "B_false_negative")


def test_false_positive_selected():
    cases = run(toy_wide())
    assert "pC" in cats(cases, "C_false_positive")


def test_true_negative_selected():
    cases = run(toy_wide())
    assert "pD" in cats(cases, "D_true_negative")


def test_cnv_rescue_classification():
    cases = run(toy_wide())
    assert "pE" in cats(cases, "E_cnv_rescue")
    assert "pE" not in cats(cases, "F_histology_rescue")


def test_histology_rescue_classification():
    cases = run(toy_wide())
    assert "pF" in cats(cases, "F_histology_rescue")


def test_fusion_hurt_classification():
    cases = run(toy_wide())
    assert "pG" in cats(cases, "G_fusion_hurt")


def test_modality_disagreement_classification():
    cases = run(toy_wide())
    # pE and pF have |cnv-image| = 0.7 >= 0.4
    disagree = cats(cases, "I_modality_disagreement")
    assert "pE" in disagree and "pF" in disagree
    # pA (0.8 vs 0.8) does not disagree
    assert "pA" not in disagree


def test_at_event_flag():
    w = toy_wide()
    at_event = pd.Series({p: (p == "pZ") for p in w["patient_id"]})
    cases = run(w, at_event)
    z = cases[cases["patient_id"].eq("pZ")]
    # pZ has rep_days_to_event == 0 -> per-case timing is at_event
    assert (z["case_timing"] == "at_event").all()
    assert bool(z["patient_has_at_event_biopsy"].iloc[0]) is True


def test_early_prediction_prioritised_in_table():
    # A-category selection requires not-at-event; the at-event TP pZ must not be an A case
    cases = run(toy_wide())
    assert "pZ" not in cats(cases, "A_true_positive_early")


def test_pred_class_default_threshold():
    assert sel.pred_class(0.9) == 1
    assert sel.pred_class(0.2) == 0
