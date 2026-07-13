"""Toy checks for the leakage-safe final training foundation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from barrett.models import AttentionMIL, EarlyFusionMLP, IntermediateABMILCNV
from barrett.training.inner_cv import make_inner_assignments, split_inner
from barrett.training.loops import fit_neural


class MemoryStore:
    def __init__(self) -> None:
        self.cnv_features = ["c1", "c2"]
        self._bags = {str(i): np.full((3, 4), i / 10, dtype=np.float32) for i in range(1, 9)}
        self._cnv = {
            "1": np.array([0.0, np.nan], dtype=np.float32),
            "2": np.array([2.0, 4.0], dtype=np.float32),
            "3": np.array([1.0, 2.0], dtype=np.float32),
            "4": np.array([3.0, 6.0], dtype=np.float32),
            "5": np.array([1000.0, 1000.0], dtype=np.float32),
            "6": np.array([1000.0, 1000.0], dtype=np.float32),
            "7": np.array([0.0, 0.0], dtype=np.float32),
            "8": np.array([0.0, 0.0], dtype=np.float32),
        }

    def bag(self, sample_id: str) -> np.ndarray:
        return self._bags[str(sample_id)]

    def cnv_array(self, sample_ids: list[str]) -> np.ndarray:
        return np.stack([self._cnv[str(value)] for value in sample_ids])


def _frame(sample_ids: list[int], patient_prefix: str = "P") -> pd.DataFrame:
    return pd.DataFrame({
        "sample_id": [str(value) for value in sample_ids],
        "patient_id": [f"{patient_prefix}{value}" for value in sample_ids],
        "y_progressor": [value % 2 for value in sample_ids],
    })


def test_inner_folds_are_patient_disjoint() -> None:
    rows = []
    for patient in range(12):
        for sample in range(2):
            rows.append({
                "sample_id": f"S{patient}_{sample}",
                "patient_id": f"P{patient}",
                "y_progressor": patient % 2,
            })
    frame = pd.DataFrame(rows)
    assignments = make_inner_assignments(frame, n_folds=3, seed=7)
    assert assignments["patient_id"].is_unique
    for fold in (1, 2, 3):
        train, validation = split_inner(frame, assignments, fold)
        assert set(train["patient_id"]).isdisjoint(validation["patient_id"])


def test_neural_cnv_preprocessing_uses_training_rows_only() -> None:
    store = MemoryStore()
    fit = fit_neural(
        "early_fusion",
        _frame([1, 2, 3, 4]),
        _frame([5, 6], "V"),
        store,
        {"hidden_dim": 8, "dropout": 0.0, "batch_size": 2, "max_epochs": 1, "patience": 1},
        torch.device("cpu"),
        seed=3,
    )
    np.testing.assert_allclose(fit.cnv_median, np.array([1.5, 4.0], dtype=np.float32))
    np.testing.assert_allclose(fit.cnv_mean, np.array([1.5, 4.0], dtype=np.float32))
    assert fit.validation_predictions is not None
    assert set(fit.validation_predictions["patient_id"]) == {"V5", "V6"}


@pytest.mark.parametrize(
    "new_class,old_module,old_class,kwargs,needs_cnv",
    [
        (AttentionMIL, "image_mil.models", "AttentionMIL", {"in_dim": 4, "hidden_dim": 6, "attn_dim": 3, "dropout": 0.0}, False),
        (EarlyFusionMLP, "image_mil.multimodal", "EarlyFusionMLP", {"image_dim": 4, "cnv_dim": 2, "hidden_dim": 8, "dropout": 0.0}, True),
        (IntermediateABMILCNV, "image_mil.multimodal", "IntermediateABMILCNV", {"image_dim": 4, "cnv_dim": 2, "img_hidden": 6, "cnv_hidden": 3, "attn_dim": 3, "fusion_hidden": 5, "dropout": 0.0}, True),
    ],
)
def test_migrated_models_match_legacy_weights(
    new_class, old_module: str, old_class: str, kwargs: dict, needs_cnv: bool
) -> None:
    legacy_root = Path(__file__).resolve().parents[2]
    if not (legacy_root / "image_mil").exists():
        pytest.skip("legacy image_mil package is not available")
    sys.path.insert(0, str(legacy_root))
    try:
        module = importlib.import_module(old_module)
    except ImportError as exc:
        pytest.skip(f"legacy dependency unavailable: {exc}")
    finally:
        sys.path.pop(0)
    torch.manual_seed(11)
    new = new_class(**kwargs).eval()
    old = getattr(module, old_class)(**kwargs).eval()
    old.load_state_dict(new.state_dict(), strict=True)
    bags = [torch.randn(5, 4), torch.randn(3, 4)]
    with torch.no_grad():
        if needs_cnv:
            cnv = torch.randn(2, 2)
            expected = old(bags, cnv)
            actual = new(bags, cnv)
        else:
            expected = old(bags)
            actual = new(bags)
    torch.testing.assert_close(actual, expected)
