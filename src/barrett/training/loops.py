"""Neural train/validation/test loops with explicit split separation."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from torch import nn
from torch.utils.data import DataLoader

from barrett.models import AttentionMIL, CoAttentionABMILCNV, EarlyFusionMLP, IntermediateABMILCNV
from barrett.training.data import CanonicalFeatureStore, FinalDataset, collate_final


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def patient_max_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("patient_id", as_index=False)
        .agg(y_true=("y_true", "max"), y_prob=("y_prob", "max"))
    )


def build_model(family: str, image_dim: int, cnv_dim: int, config: dict) -> nn.Module:
    if family == "image_only":
        return AttentionMIL(
            in_dim=image_dim,
            hidden_dim=int(config.get("hidden_dim", 256)),
            attn_dim=int(config.get("attn_dim", 128)),
            dropout=float(config.get("dropout", 0.1)),
        )
    if family == "early_fusion":
        return EarlyFusionMLP(
            image_dim=image_dim,
            cnv_dim=cnv_dim,
            hidden_dim=int(config.get("hidden_dim", 512)),
            dropout=float(config.get("dropout", 0.2)),
        )
    if family == "intermediate_fusion":
        return IntermediateABMILCNV(
            image_dim=image_dim,
            cnv_dim=cnv_dim,
            img_hidden=int(config.get("img_hidden", 256)),
            cnv_hidden=int(config.get("cnv_hidden", 128)),
            attn_dim=int(config.get("attn_dim", 128)),
            fusion_hidden=int(config.get("fusion_hidden", 256)),
            dropout=float(config.get("dropout", 0.2)),
        )
    if family == "coattention_fusion":
        return CoAttentionABMILCNV(
            image_dim=image_dim,
            cnv_dim=cnv_dim,
            img_hidden=int(config.get("img_hidden", 256)),
            cnv_hidden=int(config.get("cnv_hidden", 128)),
            attn_dim=int(config.get("attn_dim", 128)),
            fusion_hidden=int(config.get("fusion_hidden", 256)),
            dropout=float(config.get("dropout", 0.2)),
        )
    raise ValueError(f"unsupported neural family: {family}")


def _forward(model: nn.Module, family: str, batch: dict, device: torch.device) -> torch.Tensor:
    bags = [bag.to(device, non_blocking=True) for bag in batch["bags"]]
    if family == "image_only":
        return model(bags).view(-1)
    return model(bags, batch["cnv"].to(device, non_blocking=True)).view(-1)


def predict_neural(
    model: nn.Module,
    family: str,
    frame: pd.DataFrame,
    store: CanonicalFeatureStore,
    device: torch.device,
    batch_size: int,
    cnv_median: np.ndarray | None = None,
    cnv_mean: np.ndarray | None = None,
    cnv_std: np.ndarray | None = None,
) -> pd.DataFrame:
    dataset = FinalDataset(frame, store, family, cnv_median, cnv_mean, cnv_std)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=collate_final)
    rows = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            logits = _forward(model, family, batch, device)
            probabilities = torch.sigmoid(logits).cpu().numpy()
            labels = batch["y"].numpy().astype(int)
            for i, sample_id in enumerate(batch["sample_ids"]):
                rows.append({
                    "sample_id": sample_id,
                    "patient_id": batch["patient_ids"][i],
                    "y_true": int(labels[i]),
                    "y_logit": float(logits[i].detach().cpu()),
                    "y_prob": float(probabilities[i]),
                })
    return pd.DataFrame(rows)


@dataclass
class NeuralFit:
    model: nn.Module
    best_epoch: int
    history: list[dict]
    validation_predictions: pd.DataFrame | None
    cnv_median: np.ndarray | None
    cnv_mean: np.ndarray | None
    cnv_std: np.ndarray | None


def fit_neural(
    family: str,
    train: pd.DataFrame,
    validation: pd.DataFrame | None,
    store: CanonicalFeatureStore,
    config: dict,
    device: torch.device,
    seed: int,
    fixed_epochs: int | None = None,
) -> NeuralFit:
    """Fit using validation only for early stopping; test data is not accepted."""
    set_seed(seed)
    batch_size = int(config.get("batch_size", 8))
    cnv_median = cnv_mean = cnv_std = None
    if family in {"early_fusion", "intermediate_fusion", "coattention_fusion"}:
        x = store.cnv_array(train["sample_id"].astype(str).tolist())
        cnv_median = np.nanmedian(x, axis=0).astype(np.float32)
        cnv_median[~np.isfinite(cnv_median)] = 0.0
        x = np.where(np.isfinite(x), x, cnv_median)
        cnv_mean = np.mean(x, axis=0).astype(np.float32)
        cnv_std = np.std(x, axis=0).astype(np.float32)
        cnv_std[~np.isfinite(cnv_std) | (cnv_std < 1e-6)] = 1.0
        cnv_mean[~np.isfinite(cnv_mean)] = 0.0
    sample_bag = store.bag(str(train.iloc[0]["sample_id"]))
    model = build_model(family, sample_bag.shape[1], len(store.cnv_features), config).to(device)
    dataset = FinalDataset(train, store, family, cnv_median, cnv_mean, cnv_std)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, collate_fn=collate_final)
    y = train["y_progressor"].astype(int).to_numpy()
    positives = int((y == 1).sum())
    negatives = int((y == 0).sum())
    if positives == 0 or negatives == 0:
        raise ValueError("neural training split has one class")
    pos_weight = torch.tensor([negatives / positives], dtype=torch.float32, device=device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=float(config.get("lr", 1e-4)), weight_decay=float(config.get("weight_decay", 1e-2))
    )
    max_epochs = int(fixed_epochs or config.get("max_epochs", 20))
    patience = int(config.get("patience", 5))
    best_score = -np.inf
    best_state = None
    best_epoch = max_epochs
    bad_epochs = 0
    history = []
    for epoch in range(1, max_epochs + 1):
        model.train()
        losses = []
        for batch in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = _forward(model, family, batch, device)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, batch["y"].to(device), pos_weight=pos_weight
            )
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        row = {"epoch": epoch, "train_loss": float(np.mean(losses))}
        if validation is not None:
            predictions = predict_neural(
                model, family, validation, store, device, batch_size,
                cnv_median, cnv_mean, cnv_std,
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
                history.append(row)
                break
        history.append(row)
    if validation is not None and best_state is not None:
        model.load_state_dict(best_state)
    val_predictions = None
    if validation is not None:
        val_predictions = predict_neural(
            model, family, validation, store, device, batch_size,
            cnv_median, cnv_mean, cnv_std,
        )
    return NeuralFit(
        model, int(best_epoch), history, val_predictions,
        cnv_median, cnv_mean, cnv_std,
    )
