"""Landmark sequence assembly and training for the longitudinal LGD2+ model.

A *landmark* is one biopsy row ``t``; its history is that patient's biopsies with
``Date`` <= the landmark's ``Date``, ordered chronologically. We predict the
Chapter 1 endpoint for the landmark row using only its history-to-date, so the
evaluation rows and target match the frozen single-timepoint baseline exactly.

Leakage controls (all fail-closed):
- a landmark's history never contains a biopsy dated after the landmark;
- the landmark itself is always the last element of its own history;
- patient-disjoint folds are inherited unchanged from the frozen release, so no
  patient contributes rows to both train and test.

This module reuses ``CanonicalFeatureStore`` for feature access and mirrors the
``fit_neural`` protocol in ``barrett.training.loops`` (AdamW, class-weighted BCE,
early stopping on patient-level validation AUPRC).
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from torch import nn

from barrett.models.longitudinal import LongitudinalABMILCNV
from barrett.training.data import CanonicalFeatureStore


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# --------------------------------------------------------------------------- #
# Landmark history assembly
# --------------------------------------------------------------------------- #

REQUIRED_LANDMARK_COLUMNS = {"sample_id", "patient_id", "Date", "y_progressor"}


@dataclass
class LandmarkHistory:
    """One landmark and the ordered sample_ids of its history (last == landmark)."""

    sample_id: str
    patient_id: str
    y_progressor: int
    history_ids: list[str]  # chronological; history_ids[-1] == sample_id
    gaps_days: list[float]  # days since previous biopsy; gaps_days[0] == 0.0


def build_landmark_histories(frame: pd.DataFrame) -> list[LandmarkHistory]:
    """Build a history-to-date for every landmark row.

    ``frame`` must have one row per biopsy with columns
    {sample_id, patient_id, Date, y_progressor}. ``Date`` is parsed to datetime;
    rows are ordered within patient by (Date, sample_id) for a deterministic tie
    break. Each landmark's history is every earlier-or-equal biopsy of that
    patient.
    """
    missing = sorted(REQUIRED_LANDMARK_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"landmark frame missing columns: {missing}")

    work = frame.copy()
    work["sample_id"] = work["sample_id"].astype(str)
    work["patient_id"] = work["patient_id"].astype(str)
    work["_date"] = pd.to_datetime(work["Date"], errors="coerce")
    if work["_date"].isna().any():
        n = int(work["_date"].isna().sum())
        raise ValueError(f"{n} landmark rows have an unparseable Date")
    if work["sample_id"].duplicated().any():
        raise ValueError("landmark frame has duplicate sample_id")

    histories: list[LandmarkHistory] = []
    for patient_id, group in work.groupby("patient_id", sort=True):
        ordered = group.sort_values(["_date", "sample_id"]).reset_index(drop=True)
        dates = ordered["_date"].tolist()
        ids = ordered["sample_id"].tolist()
        for i in range(len(ordered)):
            history_ids = ids[: i + 1]
            history_dates = dates[: i + 1]
            # fail-closed: no future biopsy leaked into this landmark's history
            landmark_date = history_dates[-1]
            if any(d > landmark_date for d in history_dates):
                raise ValueError(f"future biopsy leaked into history for {ids[i]}")
            gaps = [0.0]
            for j in range(1, len(history_dates)):
                gaps.append(float((history_dates[j] - history_dates[j - 1]).days))
            histories.append(
                LandmarkHistory(
                    sample_id=ids[i],
                    patient_id=str(patient_id),
                    y_progressor=int(ordered.iloc[i]["y_progressor"]),
                    history_ids=history_ids,
                    gaps_days=gaps,
                )
            )
    return histories


def _log_gap(days: float) -> float:
    """Log-scale an inter-biopsy gap in days (0 -> 0, else log1p(days))."""
    return math.log1p(max(0.0, float(days)))


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #


def _materialise(
    history: LandmarkHistory,
    store: CanonicalFeatureStore,
    cnv_median: np.ndarray,
    cnv_mean: np.ndarray,
    cnv_std: np.ndarray,
    device: torch.device,
) -> tuple[list[torch.Tensor], torch.Tensor, torch.Tensor]:
    """Turn a landmark history into (bags, cnv[seq,dim], time_feat[seq]) tensors."""
    bags = [
        torch.from_numpy(store.bag(sid)).float().to(device)
        for sid in history.history_ids
    ]
    cnv_raw = store.cnv_array(list(history.history_ids))  # [seq, cnv_dim]
    cnv_raw = np.where(np.isfinite(cnv_raw), cnv_raw, cnv_median)
    cnv_std_safe = np.where(cnv_std < 1e-6, 1.0, cnv_std)
    cnv_norm = (cnv_raw - cnv_mean) / cnv_std_safe
    if not np.isfinite(cnv_norm).all():
        raise ValueError(f"non-finite standardized CNV in history for {history.sample_id}")
    cnv = torch.from_numpy(cnv_norm.astype(np.float32)).to(device)
    time_feat = torch.tensor(
        [_log_gap(g) for g in history.gaps_days], dtype=torch.float32, device=device
    )
    return bags, cnv, time_feat


def _cnv_stats(
    histories: list[LandmarkHistory], store: CanonicalFeatureStore
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Median/mean/std over the training landmarks' own biopsy rows (no leakage)."""
    train_ids = sorted({sid for h in histories for sid in h.history_ids})
    x = store.cnv_array(train_ids)
    cnv_median = np.nanmedian(x, axis=0).astype(np.float32)
    cnv_median[~np.isfinite(cnv_median)] = 0.0
    x = np.where(np.isfinite(x), x, cnv_median)
    cnv_mean = np.mean(x, axis=0).astype(np.float32)
    cnv_std = np.std(x, axis=0).astype(np.float32)
    cnv_std[~np.isfinite(cnv_std) | (cnv_std < 1e-6)] = 1.0
    cnv_mean[~np.isfinite(cnv_mean)] = 0.0
    return cnv_median, cnv_mean, cnv_std


def predict_longitudinal(
    model: LongitudinalABMILCNV,
    histories: list[LandmarkHistory],
    store: CanonicalFeatureStore,
    device: torch.device,
    cnv_median: np.ndarray,
    cnv_mean: np.ndarray,
    cnv_std: np.ndarray,
) -> pd.DataFrame:
    """Predict a probability per landmark. One landmark per output row."""
    rows = []
    model.eval()
    with torch.no_grad():
        for h in histories:
            bags, cnv, time_feat = _materialise(h, store, cnv_median, cnv_mean, cnv_std, device)
            logit = model.forward_one(bags, cnv, time_feat).view(-1)
            prob = torch.sigmoid(logit).item()
            rows.append({
                "sample_id": h.sample_id,
                "patient_id": h.patient_id,
                "y_true": int(h.y_progressor),
                "y_logit": float(logit.item()),
                "y_prob": float(prob),
                "history_len": len(h.history_ids),
            })
    return pd.DataFrame(rows)


def patient_max_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("patient_id", as_index=False)
        .agg(y_true=("y_true", "max"), y_prob=("y_prob", "max"))
    )


@dataclass
class LongitudinalFit:
    model: LongitudinalABMILCNV
    best_epoch: int
    history: list[dict] = field(default_factory=list)
    validation_predictions: pd.DataFrame | None = None
    cnv_median: np.ndarray | None = None
    cnv_mean: np.ndarray | None = None
    cnv_std: np.ndarray | None = None


def fit_longitudinal(
    train: list[LandmarkHistory],
    validation: list[LandmarkHistory] | None,
    store: CanonicalFeatureStore,
    config: dict,
    device: torch.device,
    seed: int,
    fixed_epochs: int | None = None,
) -> LongitudinalFit:
    """Train the landmarking model. Validation is used only for early stopping."""
    set_seed(seed)
    cnv_median, cnv_mean, cnv_std = _cnv_stats(train, store)

    sample_bag = store.bag(train[0].history_ids[0])
    model = LongitudinalABMILCNV(
        image_dim=sample_bag.shape[1],
        cnv_dim=len(store.cnv_features),
        img_hidden=int(config.get("img_hidden", 256)),
        cnv_hidden=int(config.get("cnv_hidden", 128)),
        attn_dim=int(config.get("attn_dim", 128)),
        temporal_hidden=int(config.get("temporal_hidden", 256)),
        fusion_hidden=int(config.get("fusion_hidden", 256)),
        dropout=float(config.get("dropout", 0.2)),
        aggregator=str(config.get("aggregator", "gru")),
    ).to(device)

    y = np.array([h.y_progressor for h in train], dtype=int)
    positives = int((y == 1).sum())
    negatives = int((y == 0).sum())
    if positives == 0 or negatives == 0:
        raise ValueError("longitudinal training split has one class")
    pos_weight = torch.tensor([negatives / positives], dtype=torch.float32, device=device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config.get("lr", 1e-4)),
        weight_decay=float(config.get("weight_decay", 1e-2)),
    )
    max_epochs = int(fixed_epochs or config.get("max_epochs", 20))
    patience = int(config.get("patience", 5))
    batch_size = int(config.get("batch_size", 8))

    best_score = -np.inf
    best_state = None
    best_epoch = max_epochs
    bad_epochs = 0
    history_log: list[dict] = []

    order = list(range(len(train)))
    for epoch in range(1, max_epochs + 1):
        model.train()
        random.shuffle(order)
        losses = []
        for start in range(0, len(order), batch_size):
            idx = order[start : start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            logits = []
            targets = []
            for j in idx:
                h = train[j]
                bags, cnv, time_feat = _materialise(h, store, cnv_median, cnv_mean, cnv_std, device)
                logits.append(model.forward_one(bags, cnv, time_feat).view(-1))
                targets.append(float(h.y_progressor))
            logit = torch.cat(logits, dim=0)
            target = torch.tensor(targets, dtype=torch.float32, device=device)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                logit, target, pos_weight=pos_weight
            )
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        row = {"epoch": epoch, "train_loss": float(np.mean(losses))}

        if validation is not None:
            predictions = predict_longitudinal(
                model, validation, store, device, cnv_median, cnv_mean, cnv_std
            )
            patient = patient_max_predictions(predictions)
            score = float(average_precision_score(patient["y_true"], patient["y_prob"]))
            row["validation_patient_auprc"] = score
            if score > best_score + 1e-12:
                best_score = score
                best_state = copy.deepcopy(model.state_dict())
                best_epoch = epoch
                bad_epochs = 0
            else:
                bad_epochs += 1
            if bad_epochs >= patience:
                history_log.append(row)
                break
        history_log.append(row)

    if validation is not None and best_state is not None:
        model.load_state_dict(best_state)

    val_predictions = None
    if validation is not None:
        val_predictions = predict_longitudinal(
            model, validation, store, device, cnv_median, cnv_mean, cnv_std
        )

    return LongitudinalFit(
        model=model,
        best_epoch=int(best_epoch),
        history=history_log,
        validation_predictions=val_predictions,
        cnv_median=cnv_median,
        cnv_mean=cnv_mean,
        cnv_std=cnv_std,
    )
