"""Hardening tests for late-fusion migration, IO fail-closed helpers, and the
fused_prob alias. Synthetic DataFrames / system temp files only."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation import late_fusion as lf  # noqa: E402
from barrett.evaluation.late_fusion import compute_late_fusion, merge_oof, run_late_fusion  # noqa: E402
from barrett.evaluation.io import (  # noqa: E402
    MODEL_GROUP_COLS, fold_integrity_reason, late_fusion_method_reason,
    load_predictions, master_agreement_reason,
)


def _side(n=12, model="abmil", n_folds=5, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        rows.append({
            "condition": "all_samples", "rep": 1, "fold": (i % n_folds) + 1,
            "patient_id": f"P{i}", "sample_id": f"S{i}",
            "y_true": i % 2, "y_prob": float(rng.random()), "model_name": model,
        })
    return pd.DataFrame(rows)


def _pair(n=12):
    return _side(n, "cnv", seed=1), _side(n, "abmil", seed=2)


# ---- merge_oof exact pairing / validation ----

def test_merge_success_and_image_model():
    cnv, img = _pair()
    m = merge_oof(cnv, img)
    assert len(m) == 12 and set(m["image_model"]) == {"abmil"}


def test_duplicate_cnv_keys_rejected():
    cnv, img = _pair()
    cnv = pd.concat([cnv, cnv.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        merge_oof(cnv, img)


def test_duplicate_image_keys_rejected():
    cnv, img = _pair()
    img = pd.concat([img, img.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        merge_oof(cnv, img)


def test_unmatched_cnv_keys_rejected():
    cnv, img = _pair()
    cnv.loc[0, "sample_id"] = "S_extra"
    with pytest.raises(ValueError, match="key sets differ|unmatched"):
        merge_oof(cnv, img)


def test_unmatched_image_keys_rejected():
    cnv, img = _pair()
    img.loc[0, "sample_id"] = "S_extra"
    with pytest.raises(ValueError, match="key sets differ|unmatched"):
        merge_oof(cnv, img)


def test_null_ids_rejected():
    cnv, img = _pair()
    cnv.loc[0, "patient_id"] = None
    with pytest.raises(ValueError, match="null/blank"):
        merge_oof(cnv, img)


def test_invalid_label_rejected():
    cnv, img = _pair()
    cnv.loc[0, "y_true"] = 2
    with pytest.raises(ValueError, match="labels must be 0/1"):
        merge_oof(cnv, img)


def test_invalid_probability_rejected():
    cnv, img = _pair()
    img.loc[0, "y_prob"] = 1.5
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        merge_oof(cnv, img)


def test_label_disagreement_rejected():
    cnv, img = _pair()
    img.loc[0, "y_true"] = 1 - img.loc[0, "y_true"]
    with pytest.raises(ValueError, match="label disagreement"):
        merge_oof(cnv, img)


def test_patient_crossing_folds_rejected():
    cnv, img = _pair()
    cnv.loc[cnv.patient_id == "P0", "fold"] = 1
    cnv2 = pd.concat([cnv, cnv[cnv.patient_id == "P0"].assign(fold=2, sample_id="S0b")], ignore_index=True)
    img2 = pd.concat([img, img[img.patient_id == "P0"].assign(fold=2, sample_id="S0b")], ignore_index=True)
    with pytest.raises(ValueError, match="cross held-out folds"):
        merge_oof(cnv2, img2)


# ---- multiple image models ----

def test_multiple_image_models_processed_independently():
    cnv, _ = _pair()
    img_a = _side(12, "abmil", seed=2)
    img_b = _side(12, "set_transformer_lite", seed=3)
    img = pd.concat([img_a, img_b], ignore_index=True)
    merged = merge_oof(cnv, img)
    assert set(merged["image_model"]) == {"abmil", "set_transformer_lite"}
    preds, diag = compute_late_fusion(merged, seed=0)
    # every fold/model diagnostic keeps its own image_model
    assert {d["image_model"] for d in diag} == {"abmil", "set_transformer_lite"}


def test_no_image_model_mixing_in_meta_training(monkeypatch):
    cnv, _ = _pair()
    img = pd.concat([_side(12, "abmil", seed=2), _side(12, "set_transformer_lite", seed=3)], ignore_index=True)
    merged = merge_oof(cnv, img)
    seen = []
    real = lf._fold_pure_stack

    def spy(train, test, seed, fitter=None):
        seen.append((set(train["image_model"]), set(test["image_model"])))
        return real(train, test, seed, fitter=fitter)

    monkeypatch.setattr(lf, "_fold_pure_stack", spy)
    compute_late_fusion(merged, seed=0)
    for train_models, test_models in seen:
        assert len(test_models) == 1
        assert train_models <= test_models  # only the same single model in training


def test_fold_purity_holds_out_test_fold(monkeypatch):
    cnv, img = _pair()
    merged = merge_oof(cnv, img)
    calls = []
    real = lf._fold_pure_stack

    def spy(train, test, seed, fitter=None):
        calls.append((set(train["fold"]), set(test["fold"])))
        return real(train, test, seed, fitter=fitter)

    monkeypatch.setattr(lf, "_fold_pure_stack", spy)
    compute_late_fusion(merged, seed=0)
    assert calls
    for train_folds, test_folds in calls:
        assert test_folds and not (test_folds & train_folds)  # held-out fold absent from training


# ---- external write safety ----

def test_output_inside_repo_rejected():
    with pytest.raises(ValueError, match="inside the clean repo"):
        run_late_fusion(["x"], ["y"], REPO_ROOT / "reports" / "thesis_ch1")


def test_output_inside_repo_tmp_also_rejected():
    with pytest.raises(ValueError, match="inside the clean repo"):
        run_late_fusion(["x"], ["y"], REPO_ROOT / "tmp" / "run")


def _write_pair(dirpath):
    cnv, img = _pair()
    cp = Path(dirpath) / "cnv.csv"
    ip = Path(dirpath) / "img.csv"
    cnv.to_csv(cp, index=False)
    img.to_csv(ip, index=False)
    return str(cp), str(ip)


def test_atomic_write_in_system_temp_and_overwrite_guard():
    with tempfile.TemporaryDirectory() as td:  # system temp, outside repo
        cp, ip = _write_pair(td)
        out = Path(td) / "run1"
        dest = run_late_fusion([cp], [ip], out, seed=0)
        assert dest.exists() and (out / "run_metadata.json").exists()
        # second call without overwrite fails
        with pytest.raises(FileExistsError):
            run_late_fusion([cp], [ip], out, seed=0)
        # overwrite succeeds
        run_late_fusion([cp], [ip], out, seed=0, overwrite=True)


# ---- io fail-closed helpers (used by script 02) ----

def _lf_frame():
    rows = []
    for m in ("mean", "stack_logit"):
        for i in range(4):
            rows.append({"condition": "all_samples", "rep": 1, "fold": (i % 2) + 1,
                         "fusion_method": m, "sample_id": f"S{i}", "patient_id": f"P{i}"})
    return pd.DataFrame(rows)


def test_late_fusion_method_reason_duplicate():
    df = pd.concat([_lf_frame(), _lf_frame().iloc[[0]]], ignore_index=True)
    assert "duplicate" in late_fusion_method_reason(df, {"mean", "stack_logit"})


def test_late_fusion_method_reason_missing_method():
    df = _lf_frame()
    df = df[df.fusion_method == "mean"]
    assert "!= present" in late_fusion_method_reason(df, {"mean", "stack_logit"})


def test_late_fusion_method_reason_different_sample_sets():
    df = _lf_frame()
    df.loc[(df.fusion_method == "mean") & (df.sample_id == "S0"), "sample_id"] = "SX"
    assert "different sample sets" in late_fusion_method_reason(df, {"mean", "stack_logit"})


def test_late_fusion_method_reason_ok():
    assert late_fusion_method_reason(_lf_frame(), {"mean", "stack_logit"}) is None


def test_master_agreement_label_disagreement():
    df = pd.DataFrame({"patient_id": ["P0"], "y_true": [1], "label_master": [0]})
    assert "disagrees with master label" in master_agreement_reason(df)


def test_master_agreement_patient_disagreement():
    df = pd.DataFrame({"patient_id": ["P0"], "y_true": [1], "label_master": [1],
                       "patient_id_master": ["PX"]})
    assert "patient_id disagrees" in master_agreement_reason(df)


def test_fold_integrity_multi_fold_and_count():
    good = pd.DataFrame({"patient_id": [f"P{i}" for i in range(5)], "fold": [1, 2, 3, 4, 5]})
    assert fold_integrity_reason(good) is None
    leak = pd.DataFrame({"patient_id": ["P0", "P0"], "fold": [1, 2]})
    assert "multiple folds" in fold_integrity_reason(leak)
    fewer = pd.DataFrame({"patient_id": [f"P{i}" for i in range(3)], "fold": [1, 2, 3]})
    assert "expected 5 folds" in fold_integrity_reason(fewer)


# ---- io fused_prob alias ----

def test_fused_prob_alias_normalizes(tmp_path):
    df = pd.DataFrame({
        "condition": ["all_samples"] * 2, "rep": [1, 1], "fold": [1, 2],
        "patient_id": ["P0", "P1"], "sample_id": ["S0", "S1"],
        "y_true": [1, 0], "image_model": ["abmil", "abmil"],
        "fusion_method": ["mean", "mean"], "fused_prob": [0.8, 0.2], "stack_note": ["ok", "ok"],
    })
    f = tmp_path / "cv_predictions_late_fusion.csv"
    df.to_csv(f, index=False)
    loaded = load_predictions([f])
    assert np.allclose(loaded["y_prob"], [0.8, 0.2])
    assert "fusion_method" in MODEL_GROUP_COLS


def test_canonical_y_prob_preserved(tmp_path):
    df = pd.DataFrame({"sample_id": ["S0"], "patient_id": ["P0"], "fold": [1],
                       "y_true": [1], "y_prob": [0.42], "model_name": ["abmil"]})
    f = tmp_path / "predictions_standard.csv"
    df.to_csv(f, index=False)
    assert np.allclose(load_predictions([f])["y_prob"], [0.42])
