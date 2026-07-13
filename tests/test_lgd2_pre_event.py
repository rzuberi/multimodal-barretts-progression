"""Toy tests for LGD2+ label derivation and strict pre-event eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.labels.lgd2 import current_grade_is_event, derive_next_biopsy_lgd2plus  # noqa: E402
from barrett.data.pre_event import (  # noqa: E402
    add_derived_labels, build_pre_event_flags, cohort_flow, validate_event_dates,
)


# ---- label rules ----

def test_current_event_hgd_and_two_lgd():
    cgi = pd.Series([3, 2, 2, 1, None])
    streak = pd.Series([0, 2, 1, 5, 3])
    ev = current_grade_is_event(cgi, streak).tolist()
    assert ev == [True, True, False, False, False]  # HGD+, 2xLGD; single LGD & ND not event; NaN grade False


def test_next_biopsy_endpoint_rule():
    nbl = pd.Series([3, 2, 2, 1, None])
    streak = pd.Series([0, 1, 0, 9, 1])
    out = derive_next_biopsy_lgd2plus(nbl, streak)
    assert out.tolist()[:4] == [1.0, 1.0, 0.0, 0.0]  # HGD+; LGD completing 2; LGD w/o streak; ND
    assert pd.isna(out.iloc[4])  # unknown label -> NaN


def _master():
    # one non-progressor with missing event date, one HGD+ progressor, one at-event, one post-event
    return pd.DataFrame({
        "PatientID_real": ["A", "A", "B", "C", "C", "C"],
        "BiopsyID_int": [1, 2, 3, 4, 5, 6],
        "Date": ["2020-01-01", "2020-06-01", "2020-01-01", "2019-01-01", "2019-06-01", "2020-01-01"],
        "NextBiopsyDate": ["2020-06-01", "2021-01-01", "2020-06-01", "2019-06-01", "2020-01-01", "2020-06-01"],
        "DaysToNextBiopsy": [151, 214, 151, 151, 214, 151],
        "CurrentGradeInt": [1, 1, 1, 2, 2, 1],  # C: LGD, LGD(2x=event), then post
        "LGDStreakSoFar": [0, 0, 0, 1, 2, 0],
        "NextBiopsyLabel": [1, 3, 1, 2, 1, 1],
        "NextBiopsyProgression_LGD2plus": [0, 1, 0, 1, 0, 0],
        "EventDate": ["", "", "", "2019-06-01", "2019-06-01", "2019-06-01"],
        "EventType": ["", "", "", "LGDx2", "LGDx2", "LGDx2"],
        "ImageAbsPath": ["i"] * 6,
        "CNVAbsPath": ["c"] * 6,
    })


def test_endpoint_agreement_flag():
    a = add_derived_labels(_master())
    ev = a["endpoint_agrees"].dropna()
    assert (ev == 1).all()  # stored equals derived on all evaluable toy rows


def test_valid_non_progressor_missing_event_retained():
    f = build_pre_event_flags(_master())
    a = f[(f.PatientID_real == "A")]
    assert a["strict_pre_event_eligible"].all()  # missing EventDate is valid for non-progressors


def test_at_event_and_post_event_excluded():
    f = build_pre_event_flags(_master()).sort_values("BiopsyID_int").set_index("BiopsyID_int")
    # C: biopsy 4 = 1st LGD predicting the upcoming 2-LGD event -> eligible predictor row;
    # biopsy 5 = 2nd LGD (at-event) -> excluded; biopsy 6 = after event -> post_event excluded.
    assert f.loc[4, "strict_pre_event_eligible"]
    assert f.loc[5, "exclusion_reason"] == "at_event"
    assert f.loc[6, "exclusion_reason"] == "post_event"


def test_next_biopsy_not_future_excluded():
    m = _master()
    m.loc[0, "NextBiopsyDate"] = "2019-01-01"  # before Date
    m.loc[0, "DaysToNextBiopsy"] = -5
    f = build_pre_event_flags(m)
    assert f.loc[0, "exclusion_reason"] == "next_biopsy_not_future"


def test_missing_modality_excluded():
    m = _master()
    m.loc[1, "CNVAbsPath"] = ""
    f = build_pre_event_flags(m)
    assert f.loc[1, "exclusion_reason"] == "missing_cnv"


def test_stored_vs_derived_disagreement_detected():
    m = _master()
    m.loc[1, "NextBiopsyProgression_LGD2plus"] = 0  # was 1 (HGD+ next)
    a = add_derived_labels(m)
    assert (a["endpoint_agrees"].dropna() == 0).any()


def test_cohort_flow_columns():
    flow = cohort_flow(build_pre_event_flags(_master()))
    assert {"stage", "rows", "patients"} <= set(flow.columns)
    assert (flow["stage"] == "strict_pre_event_eligible").any()


def test_eventdate_validation_reports_disagreement():
    m = _master()
    m.loc[m.PatientID_real == "C", "EventDate"] = "2025-01-01"  # canonical far from derived
    res = validate_event_dates(build_pre_event_flags(m))
    assert res["disagree"] >= 1
