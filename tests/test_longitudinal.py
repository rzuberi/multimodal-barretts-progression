"""Tests for the landmarking longitudinal model and its history assembly.

Fully synthetic tensors and DataFrames — no real data, no cluster access.
Covers: model forward shapes, the single-timepoint degenerate case, temporal
sensitivity, history-assembly correctness, and fail-closed leakage guards.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.models.longitudinal import BiopsyEncoder, LongitudinalABMILCNV  # noqa: E402
from barrett.training.longitudinal import (  # noqa: E402
    LandmarkHistory,
    build_landmark_histories,
    fit_longitudinal,
    predict_longitudinal,
)

IMAGE_DIM = 32
CNV_DIM = 12


def _bag(n_tiles: int, seed: int) -> torch.Tensor:
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tiles, IMAGE_DIM, generator=g)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #


def test_biopsy_encoder_output_dim():
    enc = BiopsyEncoder(IMAGE_DIM, CNV_DIM, img_hidden=64, cnv_hidden=32)
    out = enc(_bag(10, 0), torch.randn(CNV_DIM))
    assert out.shape == (64 + 32,)
    assert enc.out_dim == 64 + 32


@pytest.mark.parametrize("aggregator", ["gru", "attn"])
def test_forward_one_returns_scalar_logit(aggregator):
    model = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator=aggregator)
    bags = [_bag(8, 1), _bag(12, 2), _bag(5, 3)]
    cnv = torch.randn(3, CNV_DIM)
    time_feat = torch.tensor([0.0, 6.2, 5.9])
    out = model.forward_one(bags, cnv, time_feat)
    assert out.shape == (1,)
    assert torch.isfinite(out).all()


@pytest.mark.parametrize("aggregator", ["gru", "attn"])
def test_batch_forward_shape(aggregator):
    model = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator=aggregator)
    batch_bags = [[_bag(6, 10)], [_bag(6, 11), _bag(7, 12)]]  # len-1 and len-2 histories
    batch_cnv = [torch.randn(1, CNV_DIM), torch.randn(2, CNV_DIM)]
    batch_time = [torch.tensor([0.0]), torch.tensor([0.0, 5.1])]
    out = model(batch_bags, batch_cnv, batch_time)
    assert out.shape == (2, 1)


def test_single_timepoint_degenerate_case():
    """A history of length one must run and produce a finite logit."""
    model = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator="gru")
    out = model.forward_one([_bag(9, 5)], torch.randn(1, CNV_DIM), torch.tensor([0.0]))
    assert out.shape == (1,) and torch.isfinite(out).all()


def test_temporal_order_changes_gru_output():
    """The GRU aggregator must be sensitive to biopsy order (it is temporal)."""
    torch.manual_seed(0)
    model = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator="gru")
    model.eval()
    b1, b2 = _bag(8, 21), _bag(8, 22)
    cnv = torch.randn(2, CNV_DIM)
    time_feat = torch.tensor([0.0, 5.0])
    with torch.no_grad():
        forward = model.forward_one([b1, b2], cnv, time_feat)
        reverse = model.forward_one([b2, b1], cnv.flip(0), time_feat)
    assert not torch.allclose(forward, reverse, atol=1e-4)


def test_sequence_attention_only_for_attn():
    gru = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator="gru")
    with pytest.raises(ValueError, match="attn"):
        gru.sequence_attention([_bag(4, 0)], torch.randn(1, CNV_DIM), torch.tensor([0.0]))
    attn = LongitudinalABMILCNV(IMAGE_DIM, CNV_DIM, aggregator="attn")
    weights = attn.sequence_attention(
        [_bag(4, 0), _bag(4, 1)], torch.randn(2, CNV_DIM), torch.tensor([0.0, 5.0])
    )
    assert weights.shape == (2,)
    assert torch.isclose(weights.sum(), torch.tensor(1.0), atol=1e-5)


# --------------------------------------------------------------------------- #
# Landmark history assembly
# --------------------------------------------------------------------------- #


def _timeline() -> pd.DataFrame:
    """Two patients, 3 and 2 biopsies; deliberately shuffled row order."""
    rows = [
        {"sample_id": "P1_b3", "patient_id": "P1", "Date": "2015-06-01", "y_progressor": 1},
        {"sample_id": "P1_b1", "patient_id": "P1", "Date": "2013-01-01", "y_progressor": 0},
        {"sample_id": "P2_b1", "patient_id": "P2", "Date": "2014-03-01", "y_progressor": 0},
        {"sample_id": "P1_b2", "patient_id": "P1", "Date": "2014-01-01", "y_progressor": 0},
        {"sample_id": "P2_b2", "patient_id": "P2", "Date": "2015-03-01", "y_progressor": 1},
    ]
    return pd.DataFrame(rows)


def test_build_histories_counts_and_order():
    histories = build_landmark_histories(_timeline())
    # one landmark per biopsy row
    assert len(histories) == 5
    by_id = {h.sample_id: h for h in histories}
    # P1's third biopsy sees all three, in chronological order, itself last
    assert by_id["P1_b3"].history_ids == ["P1_b1", "P1_b2", "P1_b3"]
    # first biopsy of each patient has a length-1 history
    assert by_id["P1_b1"].history_ids == ["P1_b1"]
    assert by_id["P2_b1"].history_ids == ["P2_b1"]
    # landmark is always the last element of its own history
    for h in histories:
        assert h.history_ids[-1] == h.sample_id


def test_history_never_contains_future_biopsy():
    histories = build_landmark_histories(_timeline())
    dates = {r["sample_id"]: pd.Timestamp(r["Date"]) for _, r in _timeline().iterrows()}
    for h in histories:
        landmark_date = dates[h.sample_id]
        for sid in h.history_ids:
            assert dates[sid] <= landmark_date, f"future biopsy {sid} in history of {h.sample_id}"


def test_gaps_first_is_zero_and_lengths_match():
    histories = build_landmark_histories(_timeline())
    for h in histories:
        assert len(h.gaps_days) == len(h.history_ids)
        assert h.gaps_days[0] == 0.0
    by_id = {h.sample_id: h for h in histories}
    # P1_b2 is 2014-01-01, previous 2013-01-01 -> 365 days
    assert by_id["P1_b2"].gaps_days[-1] == 365.0


def test_missing_column_rejected():
    df = _timeline().drop(columns=["Date"])
    with pytest.raises(ValueError, match="missing columns"):
        build_landmark_histories(df)


def test_unparseable_date_rejected():
    df = _timeline()
    df.loc[0, "Date"] = "not-a-date"
    with pytest.raises(ValueError, match="unparseable Date"):
        build_landmark_histories(df)


def test_duplicate_sample_id_rejected():
    df = pd.concat([_timeline(), _timeline().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate sample_id"):
        build_landmark_histories(df)


# --------------------------------------------------------------------------- #
# End-to-end training on a synthetic feature store
# --------------------------------------------------------------------------- #


class _FakeStore:
    """Minimal CanonicalFeatureStore stand-in: random bags + CNV per sample_id."""

    def __init__(self, sample_ids, cnv_dim=CNV_DIM, seed=0):
        g = np.random.default_rng(seed)
        self._bags = {sid: g.standard_normal((g.integers(4, 12), IMAGE_DIM)).astype(np.float32)
                      for sid in sample_ids}
        self._cnv = {sid: g.standard_normal(cnv_dim).astype(np.float32) for sid in sample_ids}
        self.cnv_features = [f"f{i}" for i in range(cnv_dim)]

    def bag(self, sid):
        return self._bags[str(sid)]

    def cnv_array(self, sample_ids):
        return np.stack([self._cnv[str(s)] for s in sample_ids], axis=0)


def _synth_cohort(n_patients=16, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_patients):
        pid = f"SP{p:03d}"
        n = int(rng.integers(1, 5))
        start = np.datetime64("2012-01-01") + int(rng.integers(0, 500))
        dates = start + np.cumsum(rng.integers(120, 700, size=n)).astype("timedelta64[D]")
        prog = int(p % 3 == 0)
        for b in range(n):
            rows.append({
                "sample_id": f"{pid}_b{b}",
                "patient_id": pid,
                "Date": np.datetime_as_string(dates[b], unit="D"),
                "y_progressor": prog if b == n - 1 else int(rng.random() < 0.2),
            })
    return pd.DataFrame(rows)


def test_end_to_end_fit_and_predict():
    cohort = _synth_cohort()
    histories = build_landmark_histories(cohort)
    store = _FakeStore(cohort["sample_id"].tolist())
    # patient-disjoint split
    patients = sorted(cohort["patient_id"].unique())
    val_patients = set(patients[:4])
    train = [h for h in histories if h.patient_id not in val_patients]
    val = [h for h in histories if h.patient_id in val_patients]
    config = {"max_epochs": 2, "patience": 5, "batch_size": 4, "aggregator": "gru",
              "img_hidden": 32, "cnv_hidden": 16, "temporal_hidden": 32, "fusion_hidden": 32}
    fit = fit_longitudinal(train, val, store, config, torch.device("cpu"), seed=0)
    preds = predict_longitudinal(
        fit.model, val, store, torch.device("cpu"),
        fit.cnv_median, fit.cnv_mean, fit.cnv_std,
    )
    # one prediction per validation landmark, probabilities in range
    assert len(preds) == len(val)
    assert preds["y_prob"].between(0, 1).all()
    assert (preds["history_len"] >= 1).all()
    # no patient leakage between train and val
    assert not (set(h.patient_id for h in train) & val_patients)


def test_fit_rejects_single_class_training():
    cohort = _synth_cohort()
    histories = build_landmark_histories(cohort)
    store = _FakeStore(cohort["sample_id"].tolist())
    for h in histories:
        h.y_progressor = 0  # force single class
    config = {"max_epochs": 1, "batch_size": 4}
    with pytest.raises(ValueError, match="one class"):
        fit_longitudinal(histories, None, store, config, torch.device("cpu"), seed=0)
