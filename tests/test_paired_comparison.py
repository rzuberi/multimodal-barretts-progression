"""Toy tests for patient-level paired model comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.paired_comparison import align_pair, compare  # noqa: E402


def _scores(probs, y):
    return pd.DataFrame({"patient_id": [f"P{i}" for i in range(len(y))], "y_true": y, "y_prob": probs})


def _sep(n=40):
    # model a well-separated, model b near-random; alternating labels
    y = [i % 2 for i in range(n)]
    pa = [0.9 if t else 0.1 for t in y]
    pb = [0.5 + 0.001 * i for i in range(n)]
    return _scores(pa, y), _scores(pb, y)


def test_align_pair_success():
    a, b = _sep()
    m = align_pair(a, b)
    assert len(m) == 40 and {"y_prob_a", "y_prob_b", "y_true"} <= set(m.columns)


def test_align_pair_mismatched_patients_rejected():
    a, b = _sep()
    b.loc[0, "patient_id"] = "PX"
    with pytest.raises(ValueError, match="patient sets differ"):
        align_pair(a, b)


def test_align_pair_label_disagreement_rejected():
    a, b = _sep()
    b.loc[0, "y_true"] = 1 - b.loc[0, "y_true"]
    with pytest.raises(ValueError, match="labels disagree"):
        align_pair(a, b)


def test_align_pair_duplicate_patient_rejected():
    a, b = _sep()
    a = pd.concat([a, a.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate patient_id"):
        align_pair(a, b)


def test_paired_delta_favours_better_model():
    a, b = _sep()
    res = compare(a, b, n_boot=500, seed=1)
    assert res["delta_auprc"] > 0 and res["delta_roc_auc"] > 0  # a beats b
    assert res["delta_brier"] < 0  # a is better calibrated (lower Brier)
    assert res["n_patients"] == 40 and res["valid_fraction"] > 0.9
    for k in ("delta_auprc_ci_low", "delta_auprc_ci_high", "delta_auprc_sign_prob"):
        assert k in res


def test_paired_bootstrap_ci_orders():
    a, b = _sep()
    res = compare(a, b, n_boot=500, seed=1)
    assert res["delta_auprc_ci_low"] <= res["delta_auprc"] <= res["delta_auprc_ci_high"]
