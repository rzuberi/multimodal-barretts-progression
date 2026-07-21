"""Train/predict loops for the end-to-end Mixture-of-Experts.

Mirrors ``barrett.training.loops.fit_neural`` exactly (validation-only early
stopping on patient-max AUPRC, CNV normalisation from the training split,
pos_weight BCE) so the MoE is selected/calibrated under the identical
nested-CV contract as the frozen baselines. The only additions are the
load-balancing auxiliary loss and gate-weight extraction for the routing report.

The dataset is built with ``family="intermediate_fusion"`` so each batch carries
both the image bag and the CNV vector, WITHOUT modifying shared ``data.py``.
"""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from torch.utils.data import DataLoader

from barrett.training.data import CanonicalFeatureStore, FinalDataset, collate_final
from barrett.training.loops import NeuralFit, patient_max_predictions, set_seed

from moe import MixtureOfExperts, load_balance_loss

# Feed the shared dataset a fusion family so it yields bag + cnv per item.
_DATASET_FAMILY = "intermediate_fusion"

_MODEL_KEYS = ("img_hidden", "cnv_hidden", "attn_dim", "fusion_hidden", "dropout",
               "gate_hidden", "gate_temperature")


def _cnv_stats(store: CanonicalFeatureStore, train: pd.DataFrame):
    x = store.cnv_array(train["sample_id"].astype(str).tolist())
    cnv_median = np.nanmedian(x, axis=0).astype(np.float32)
    cnv_median[~np.isfinite(cnv_median)] = 0.0
    x = np.where(np.isfinite(x), x, cnv_median)
    cnv_mean = np.mean(x, axis=0).astype(np.float32)
    cnv_std = np.std(x, axis=0).astype(np.float32)
    cnv_std[~np.isfinite(cnv_std) | (cnv_std < 1e-6)] = 1.0
    cnv_mean[~np.isfinite(cnv_mean)] = 0.0
    return cnv_median, cnv_mean, cnv_std


def _build_model(config: dict, image_dim: int, cnv_dim: int) -> MixtureOfExperts:
    kwargs = {k: config[k] for k in _MODEL_KEYS if k in config}
    return MixtureOfExperts(image_dim=image_dim, cnv_dim=cnv_dim, **kwargs)


def _loader(frame, store, cnv_median, cnv_mean, cnv_std, batch_size, shuffle):
    dataset = FinalDataset(frame, store, _DATASET_FAMILY, cnv_median, cnv_mean, cnv_std)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0, collate_fn=collate_final)


def predict_moe(
    model: MixtureOfExperts,
    frame: pd.DataFrame,
    store: CanonicalFeatureStore,
    device: torch.device,
    batch_size: int,
    cnv_median: np.ndarray | None,
    cnv_mean: np.ndarray | None,
    cnv_std: np.ndarray | None,
    with_gate: bool = False,
) -> pd.DataFrame:
    loader = _loader(frame, store, cnv_median, cnv_mean, cnv_std, batch_size, shuffle=False)
    rows = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            bags = [bag.to(device, non_blocking=True) for bag in batch["bags"]]
            cnv = batch["cnv"].to(device, non_blocking=True)
            logits, gate_weights, _ = model.forward_full(bags, cnv)
            probabilities = torch.sigmoid(logits).cpu().numpy()
            gate = gate_weights.cpu().numpy()
            labels = batch["y"].numpy().astype(int)
            for i, sample_id in enumerate(batch["sample_ids"]):
                row = {
                    "sample_id": sample_id,
                    "patient_id": batch["patient_ids"][i],
                    "y_true": int(labels[i]),
                    "y_logit": float(logits[i].detach().cpu()),
                    "y_prob": float(probabilities[i]),
                }
                if with_gate:
                    row["w_image"] = float(gate[i, 0])
                    row["w_cnv"] = float(gate[i, 1])
                    row["w_multimodal"] = float(gate[i, 2])
                    row["routed_expert"] = ("image", "cnv", "multimodal")[int(gate[i].argmax())]
                rows.append(row)
    return pd.DataFrame(rows)


def fit_moe(
    train: pd.DataFrame,
    validation: pd.DataFrame | None,
    store: CanonicalFeatureStore,
    config: dict,
    device: torch.device,
    seed: int,
    fixed_epochs: int | None = None,
) -> NeuralFit:
    set_seed(seed)
    batch_size = int(config.get("batch_size", 8))
    cnv_median, cnv_mean, cnv_std = _cnv_stats(store, train)

    sample_bag = store.bag(str(train.iloc[0]["sample_id"]))
    model = _build_model(config, sample_bag.shape[1], len(store.cnv_features)).to(device)
    loader = _loader(train, store, cnv_median, cnv_mean, cnv_std, batch_size, shuffle=True)

    y = train["y_progressor"].astype(int).to_numpy()
    positives, negatives = int((y == 1).sum()), int((y == 0).sum())
    if positives == 0 or negatives == 0:
        raise ValueError("MoE training split has one class")
    pos_weight = torch.tensor([negatives / positives], dtype=torch.float32, device=device)
    lb_lambda = float(config.get("load_balance_lambda", 0.05))
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=float(config.get("lr", 1e-4)), weight_decay=float(config.get("weight_decay", 1e-2))
    )
    max_epochs = int(fixed_epochs or config.get("max_epochs", 20))
    patience = int(config.get("patience", 5))

    best_score, best_state, best_epoch, bad_epochs = -np.inf, None, max_epochs, 0
    history = []
    for epoch in range(1, max_epochs + 1):
        model.train()
        losses, lb_losses = [], []
        for batch in loader:
            optimizer.zero_grad(set_to_none=True)
            bags = [bag.to(device, non_blocking=True) for bag in batch["bags"]]
            cnv = batch["cnv"].to(device, non_blocking=True)
            logits, gate_weights, _ = model.forward_full(bags, cnv)
            bce = torch.nn.functional.binary_cross_entropy_with_logits(
                logits, batch["y"].to(device), pos_weight=pos_weight
            )
            lb = load_balance_loss(gate_weights)
            loss = bce + lb_lambda * lb
            loss.backward()
            optimizer.step()
            losses.append(float(bce.detach().cpu()))
            lb_losses.append(float(lb.detach().cpu()))
        row = {"epoch": epoch, "train_loss": float(np.mean(losses)), "load_balance": float(np.mean(lb_losses))}
        if validation is not None:
            predictions = predict_moe(model, validation, store, device, batch_size, cnv_median, cnv_mean, cnv_std)
            patient = patient_max_predictions(predictions)
            score = float(average_precision_score(patient["y_true"], patient["y_prob"]))
            row["validation_patient_auprc"] = score
            if score > best_score + 1e-12:
                best_score, best_state, best_epoch, bad_epochs = score, copy.deepcopy(model.state_dict()), epoch, 0
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
        val_predictions = predict_moe(model, validation, store, device, batch_size, cnv_median, cnv_mean, cnv_std)
    return NeuralFit(model, int(best_epoch), history, val_predictions, cnv_median, cnv_mean, cnv_std)
