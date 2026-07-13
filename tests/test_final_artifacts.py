"""Toy artifact and late-stacker checks for the final rerun."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from barrett.evaluation.output_contract import REQUIRED_PREDICTION_COLUMNS
from barrett.training.artifacts import REQUIRED_FOLD_FILES, reject_repo_output, validate_fold_directory
from barrett.training.late_fusion import _align_outer_to_template, _cross_fitted_stack


def _prediction(sample_id: str, patient_id: str, fold: int, label: int, probability: float) -> dict:
    row = {column: "x" for column in REQUIRED_PREDICTION_COLUMNS}
    row.update({
        "model_family": "cnv_only", "model_name": "cnv_random_forest",
        "outer_fold": fold, "row_key": sample_id, "sample_id": sample_id,
        "patient_id": patient_id, "y_true": label, "y_prob": probability,
        "strict_pre_event_eligible": True, "seed": 1,
    })
    return row


def test_fold_directory_validation_passes_toy_contract(tmp_path) -> None:
    fold_dir = tmp_path / "cnv_only/fold1"
    fold_dir.mkdir(parents=True)
    predictions = pd.DataFrame([
        _prediction("S1", "P1", 1, 0, 0.2),
        _prediction("S2", "P2", 1, 1, 0.8),
    ])
    predictions.to_csv(fold_dir / "outer_test_predictions.csv", index=False)
    for name in REQUIRED_FOLD_FILES:
        path = fold_dir / name
        if path.exists():
            continue
        path.write_text("x\n", encoding="utf-8")
    (fold_dir / "fold_completion.json").write_text(json.dumps({
        "status": "PASS", "family": "cnv_only", "outer_fold": 1,
    }), encoding="utf-8")
    expected = pd.DataFrame({
        "sample_id": ["S1", "S2"], "patient_id": ["P1", "P2"],
        "y_progressor": [0, 1],
    })
    problems, loaded = validate_fold_directory(fold_dir, expected, "cnv_only", 1)
    assert problems == []
    assert loaded is not None and len(loaded) == 2


def test_fold_directory_rejects_wrong_rows(tmp_path) -> None:
    fold_dir = tmp_path / "cnv_only/fold1"
    fold_dir.mkdir(parents=True)
    pd.DataFrame([_prediction("S1", "P1", 1, 0, 0.2)]).to_csv(
        fold_dir / "outer_test_predictions.csv", index=False
    )
    for name in REQUIRED_FOLD_FILES:
        path = fold_dir / name
        if not path.exists():
            path.write_text("x\n", encoding="utf-8")
    (fold_dir / "fold_completion.json").write_text(json.dumps({
        "status": "PASS", "family": "cnv_only", "outer_fold": 1,
    }), encoding="utf-8")
    expected = pd.DataFrame({
        "sample_id": ["S1", "S2"], "patient_id": ["P1", "P2"],
        "y_progressor": [0, 1],
    })
    problems, _ = validate_fold_directory(fold_dir, expected, "cnv_only", 1)
    assert any("row-key mismatch" in problem for problem in problems)


def test_late_stacker_generates_cross_fitted_inner_predictions() -> None:
    rows = []
    for fold in (1, 2, 3):
        for index in range(8):
            label = index % 2
            rows.append({
                "outer_fold": 1, "inner_fold": fold,
                "sample_id": f"S{fold}_{index}", "patient_id": f"P{fold}_{index}",
                "y_true": label, "cnv_prob": 0.2 + 0.5 * label,
                "image_prob": 0.3 + 0.4 * label,
            })
    frame = pd.DataFrame(rows)
    cross_fitted, model = _cross_fitted_stack(frame, seed=5)
    assert len(cross_fitted) == len(frame)
    assert set(cross_fitted["sample_id"]) == set(frame["sample_id"])
    assert np.isfinite(cross_fitted["y_prob"]).all()
    assert model.coef_.shape == (1, 2)


def test_external_output_guard_rejects_repo_descendant(tmp_path) -> None:
    with pytest.raises(ValueError, match="outside Git"):
        reject_repo_output(tmp_path / "output", tmp_path)


def test_late_outer_probabilities_are_key_aligned_to_template() -> None:
    merged = pd.DataFrame({
        "row_key": ["S2", "S1"], "cnv_prob": [0.8, 0.2],
        "image_prob": [0.6, 0.4],
    })
    template = pd.DataFrame({"row_key": ["S1", "S2"]})
    aligned = _align_outer_to_template(merged, template)
    assert aligned["row_key"].tolist() == ["S1", "S2"]
    np.testing.assert_allclose(aligned["cnv_prob"], [0.2, 0.8])
