"""Toy tests for late-fusion migration and the script-02 fused_prob alias."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.late_fusion import (  # noqa: E402
    compute_late_fusion,
    merge_oof,
    run_late_fusion,
)
from barrett.evaluation.io import load_predictions, MODEL_GROUP_COLS  # noqa: E402


def _side(y_prob, y_true, model="m", n_folds=2):
    rows = []
    for i, (p, t) in enumerate(zip(y_prob, y_true)):
        rows.append({
            "condition": "all_samples", "rep": 1, "fold": (i % n_folds) + 1,
            "patient_id": f"P{i}", "sample_id": f"S{i}",
            "y_true": t, "y_prob": p, "model_name": model,
        })
    return pd.DataFrame(rows)


def _paired(n=12):
    rng = np.random.default_rng(0)
    y = [i % 2 for i in range(n)]
    cnv = _side(rng.random(n), y, "cnv")
    img = _side(rng.random(n), y, "abmil")
    return cnv, img


def test_merge_and_methods():
    cnv, img = _paired()
    merged = merge_oof(cnv, img)
    assert len(merged) == 12
    preds = compute_late_fusion(merged, seed=0)
    methods = set(preds["fusion_method"])
    assert {"cnv_only", "img_only", "mean", "stack_logit"} == methods
    # mean is exactly the average of the two probs
    m = preds[preds.fusion_method == "mean"].set_index("sample_id")["y_prob"]
    c = merge_oof(cnv, img).set_index("sample_id")["cnv_prob"]
    i = merge_oof(cnv, img).set_index("sample_id")["img_prob"]
    assert np.allclose(m.sort_index(), (0.5 * (c + i)).sort_index())


def test_label_disagreement_rejected():
    cnv, img = _paired()
    img.loc[0, "y_true"] = 1 - img.loc[0, "y_true"]
    with pytest.raises(ValueError, match="label disagreement"):
        merge_oof(cnv, img)


def test_patient_crossing_folds_rejected():
    cnv, img = _paired()
    # force patient P0 into a second fold via a duplicate row with a different fold
    dup = cnv[cnv.patient_id == "P0"].copy()
    dup["fold"] = 99
    cnv2 = pd.concat([cnv, dup], ignore_index=True)
    img2 = pd.concat([img, img[img.patient_id == "P0"].assign(fold=99)], ignore_index=True)
    with pytest.raises(ValueError, match="cross held-out folds"):
        merge_oof(cnv2, img2)


def test_fold_pure_stack_excludes_test_fold():
    # single-class training fold triggers the documented mean fallback
    cnv = _side([0.9, 0.8, 0.1, 0.2], [1, 1, 0, 0], "cnv", n_folds=2)
    img = _side([0.7, 0.6, 0.3, 0.4], [1, 1, 0, 0], "abmil", n_folds=2)
    # fold1 has P0(y=1),P2(y=0); fold2 has P1(y=1),P3(y=0) -> both folds two-class
    preds = compute_late_fusion(merge_oof(cnv, img), seed=0)
    stack = preds[preds.fusion_method == "stack_logit"]
    assert len(stack) == 4
    assert set(stack["stack_note"]) <= {"ok", "fallback_mean_single_class_train"}


def test_fused_prob_alias_normalizes(tmp_path):
    # a late-fusion-style file with fused_prob and no y_prob
    df = pd.DataFrame({
        "condition": ["all_samples"] * 2, "rep": [1, 1], "fold": [1, 2],
        "patient_id": ["P0", "P1"], "sample_id": ["S0", "S1"],
        "y_true": [1, 0], "image_model": ["abmil", "abmil"],
        "fusion_method": ["mean", "mean"], "fused_prob": [0.8, 0.2],
        "stack_note": ["ok", "ok"],
    })
    f = tmp_path / "cv_predictions_late_fusion.csv"
    df.to_csv(f, index=False)
    loaded = load_predictions([f])
    assert "y_prob" in loaded.columns
    assert np.allclose(loaded["y_prob"], [0.8, 0.2])
    assert "fusion_method" in MODEL_GROUP_COLS  # keeps mean/stack_logit separate


def test_canonical_y_prob_preserved(tmp_path):
    # a standard file with real y_prob and no fused_prob: unchanged
    df = pd.DataFrame({
        "sample_id": ["S0"], "patient_id": ["P0"], "fold": [1],
        "y_true": [1], "y_prob": [0.42], "model_name": ["abmil"],
    })
    f = tmp_path / "predictions_standard.csv"
    df.to_csv(f, index=False)
    loaded = load_predictions([f])
    assert np.allclose(loaded["y_prob"], [0.42])


def test_reject_output_inside_repo():
    with pytest.raises(ValueError, match="inside the clean repo"):
        run_late_fusion(["x"], ["y"], REPO_ROOT / "reports" / "thesis_ch1")
