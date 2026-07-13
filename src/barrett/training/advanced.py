"""Training and feature loading for experimental strict pre-event fusion models."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from torch import nn
from torch.utils.data import DataLoader, Dataset

from barrett.models.advanced_fusion import (
    CNVTokenCrossAttentionFusion,
    FoundationEnsembleFusion,
    HierarchicalPatientFusion,
    LowRankBilinearFusion,
    MultiTaskTemporalFusion,
    OptimalTransportFusion,
    ReliabilityGatedResidualFusion,
)
from barrett.training.data import load_cnv_matrix
from barrett.training.loops import patient_max_predictions


ROW_FAMILIES = {
    "reliability_gated_fusion", "cnv_token_cross_attention", "low_rank_bilinear_fusion",
    "multitask_temporal_fusion", "optimal_transport_fusion", "foundation_ensemble_fusion",
}
ALL_FAMILIES = ROW_FAMILIES | {"hierarchical_patient_fusion"}


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def chromosome_group_ids(feature_names: list[str]) -> list[int]:
    groups: list[str] = []
    for name in feature_names:
        value = str(name).lower()
        if value == "cx":
            group = "cx"
        elif value.startswith("chr"):
            suffix = value[3:]
            group = suffix.split(":", 1)[0].rstrip("pq")
        else:
            group = "other"
        if group not in groups:
            groups.append(group)
    lookup = {name: index for index, name in enumerate(groups)}
    return [lookup[("cx" if str(name).lower() == "cx" else str(name).lower()[3:].split(":", 1)[0].rstrip("pq")) if str(name).lower().startswith("chr") or str(name).lower() == "cx" else "other"] for name in feature_names]


class AdvancedFeatureStore:
    def __init__(self, indexes: dict[str, pd.DataFrame], cnv: pd.DataFrame, cnv_features: list[str]) -> None:
        self.image_paths: dict[str, dict[str, str]] = {}
        for name, frame in indexes.items():
            index = frame.copy()
            index["sample_id"] = index["sample_id"].astype(str)
            if index["sample_id"].duplicated().any():
                raise ValueError(f"{name} index has duplicate sample_id")
            self.image_paths[name] = dict(zip(index["sample_id"], index["npz_path"].astype(str)))
        self.foundation_names = tuple(sorted(self.image_paths))
        if "uni2" not in self.foundation_names:
            raise ValueError("advanced store requires uni2")
        self._bag_cache: dict[tuple[str, str], np.ndarray] = {}
        cnv = cnv.copy()
        cnv["sample_id"] = cnv["sample_id"].astype(str)
        self.cnv = cnv.set_index("sample_id")[cnv_features]
        self.cnv_features = list(cnv_features)
        self.cnv_group_ids = chromosome_group_ids(cnv_features)

    @classmethod
    def from_release(cls, release: Path, feature_views: dict) -> "AdvancedFeatureStore":
        cnv, features = load_cnv_matrix(release / feature_views["cnv"])
        indexes = {
            name: pd.read_csv(release / path, dtype={"sample_id": str})
            for name, path in feature_views["foundation_indexes"].items()
        }
        return cls(indexes, cnv, features)

    def bag(self, sample_id: str, foundation: str = "uni2") -> np.ndarray:
        key = (foundation, str(sample_id))
        if key not in self._bag_cache:
            with np.load(self.image_paths[foundation][str(sample_id)], allow_pickle=False) as archive:
                bag = np.asarray(archive["embeddings"], dtype=np.float32)
            if bag.ndim != 2 or not np.isfinite(bag).all():
                raise ValueError(f"invalid {foundation} bag for {sample_id}: {bag.shape}")
            self._bag_cache[key] = bag
        return self._bag_cache[key]

    def cnv_array(self, sample_ids: list[str]) -> np.ndarray:
        return self.cnv.loc[[str(value) for value in sample_ids]].to_numpy(dtype=np.float32)


class AdvancedRowDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, store: AdvancedFeatureStore, family: str,
                 median: np.ndarray, mean: np.ndarray, std: np.ndarray) -> None:
        self.frame = frame.reset_index(drop=True)
        self.store, self.family = store, family
        self.median, self.mean, self.std = median, mean, std

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> dict:
        row = self.frame.iloc[index]
        sample_id = str(row["sample_id"])
        cnv = self.store.cnv_array([sample_id])[0]
        cnv = np.where(np.isfinite(cnv), cnv, self.median)
        cnv = ((cnv - self.mean) / self.std).astype(np.float32)
        item = {
            "sample_id": sample_id, "patient_id": str(row["patient_id"]),
            "y": torch.tensor(float(row["y_progressor"]), dtype=torch.float32),
            "bag": torch.from_numpy(self.store.bag(sample_id, "uni2")),
            "cnv": torch.from_numpy(cnv),
            "time_target": torch.tensor(float(row.get("DaysFromCurrentToEvent", np.nan)), dtype=torch.float32),
        }
        if self.family == "foundation_ensemble_fusion":
            item["foundation_bags"] = {
                name: torch.from_numpy(self.store.bag(sample_id, name)) for name in self.store.foundation_names
            }
        return item


def collate_rows(batch: list[dict]) -> dict:
    out = {
        "sample_ids": [item["sample_id"] for item in batch],
        "patient_ids": [item["patient_id"] for item in batch],
        "y": torch.stack([item["y"] for item in batch]),
        "bags": [item["bag"] for item in batch],
        "cnv": torch.stack([item["cnv"] for item in batch]),
        "time_target": torch.stack([item["time_target"] for item in batch]),
    }
    if "foundation_bags" in batch[0]:
        out["foundation_bags"] = {
            name: [item["foundation_bags"][name] for item in batch]
            for name in batch[0]["foundation_bags"]
        }
    return out


class PatientDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, store: AdvancedFeatureStore,
                 median: np.ndarray, mean: np.ndarray, std: np.ndarray) -> None:
        self.groups = [group.copy() for _, group in frame.groupby("patient_id", sort=False)]
        self.store = store
        self.median, self.mean, self.std = median, mean, std

    def __len__(self) -> int:
        return len(self.groups)

    def __getitem__(self, index: int) -> dict:
        group = self.groups[index].sort_values(["Date", "biopsy_id", "sample_id"], na_position="last")
        sample_ids = group["sample_id"].astype(str).tolist()
        cnv = self.store.cnv_array(sample_ids)
        cnv = np.where(np.isfinite(cnv), cnv, self.median)
        cnv = ((cnv - self.mean) / self.std).astype(np.float32)
        dates = pd.to_datetime(group["Date"], errors="coerce")
        if dates.notna().any():
            relative = (dates - dates.min()).dt.days.fillna(0).to_numpy(dtype=np.float32)
        else:
            relative = np.zeros(len(group), dtype=np.float32)
        return {
            "patient_id": str(group.iloc[0]["patient_id"]), "sample_ids": sample_ids,
            "labels": group["y_progressor"].astype(int).tolist(),
            "y": torch.tensor(float(group["y_progressor"].max()), dtype=torch.float32),
            "bags": [torch.from_numpy(self.store.bag(value, "uni2")) for value in sample_ids],
            "cnv": torch.from_numpy(cnv), "biopsy_ids": group["biopsy_id"].astype(str).tolist(),
            "relative_days": torch.from_numpy(relative),
        }


def collate_patients(batch: list[dict]) -> dict:
    return {"patients": batch, "y": torch.stack([item["y"] for item in batch])}


def _preprocessing(frame: pd.DataFrame, store: AdvancedFeatureStore) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = store.cnv_array(frame["sample_id"].astype(str).tolist())
    median = np.nanmedian(x, axis=0).astype(np.float32)
    median[~np.isfinite(median)] = 0.0
    x = np.where(np.isfinite(x), x, median)
    mean = x.mean(axis=0).astype(np.float32)
    std = x.std(axis=0).astype(np.float32)
    mean[~np.isfinite(mean)] = 0.0
    std[~np.isfinite(std) | (std < 1e-6)] = 1.0
    return median, mean, std


def build_advanced_model(family: str, store: AdvancedFeatureStore, config: dict) -> nn.Module:
    image_dim = int(store.bag(next(iter(store.image_paths["uni2"])), "uni2").shape[1])
    cnv_dim = len(store.cnv_features)
    hidden, dropout = int(config.get("hidden", 128)), float(config.get("dropout", 0.2))
    if family == "reliability_gated_fusion":
        return ReliabilityGatedResidualFusion(image_dim, cnv_dim, hidden, dropout, float(config.get("residual_scale", 0.1)))
    if family == "hierarchical_patient_fusion":
        return HierarchicalPatientFusion(image_dim, cnv_dim, hidden, dropout)
    if family == "cnv_token_cross_attention":
        return CNVTokenCrossAttentionFusion(image_dim, store.cnv_group_ids, int(config.get("token_dim", 64)), int(config.get("n_heads", 4)), dropout)
    if family == "low_rank_bilinear_fusion":
        return LowRankBilinearFusion(image_dim, cnv_dim, hidden, int(config.get("rank", 16)), dropout)
    if family == "multitask_temporal_fusion":
        return MultiTaskTemporalFusion(image_dim, cnv_dim, hidden, dropout)
    if family == "optimal_transport_fusion":
        return OptimalTransportFusion(image_dim, store.cnv_group_ids, int(config.get("token_dim", 64)), float(config.get("epsilon", 0.1)), int(config.get("sinkhorn_iters", 8)), dropout)
    if family == "foundation_ensemble_fusion":
        dims = {name: int(store.bag(next(iter(store.image_paths[name])), name).shape[1]) for name in store.foundation_names}
        return FoundationEnsembleFusion(dims, cnv_dim, hidden, dropout, bool(config.get("learned_gate", True)))
    raise ValueError(f"unsupported advanced family: {family}")


def _to_device_patient(patient: dict, device: torch.device) -> dict:
    return {
        **patient,
        "bags": [value.to(device, non_blocking=True) for value in patient["bags"]],
        "cnv": patient["cnv"].to(device, non_blocking=True),
        "relative_days": patient["relative_days"].to(device, non_blocking=True),
    }


def _forward(model: nn.Module, family: str, batch: dict, device: torch.device) -> dict[str, torch.Tensor]:
    if family == "hierarchical_patient_fusion":
        return model([_to_device_patient(value, device) for value in batch["patients"]])
    cnv = batch["cnv"].to(device, non_blocking=True)
    if family == "foundation_ensemble_fusion":
        bags = {name: [value.to(device, non_blocking=True) for value in values] for name, values in batch["foundation_bags"].items()}
        return model(bags, cnv)
    return model([value.to(device, non_blocking=True) for value in batch["bags"]], cnv)


def _loss(outputs: dict[str, torch.Tensor], batch: dict, device: torch.device,
          pos_weight: torch.Tensor, config: dict) -> torch.Tensor:
    labels = batch["y"].to(device)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(outputs["logits"], labels, pos_weight=pos_weight)
    if "aux_logits" in outputs:
        repeated = labels[:, None].expand_as(outputs["aux_logits"])
        aux = torch.nn.functional.binary_cross_entropy_with_logits(outputs["aux_logits"], repeated, pos_weight=pos_weight)
        loss = loss + float(config.get("aux_weight", 0.2)) * aux
    if "time_prediction" in outputs:
        target = batch["time_target"].to(device)
        mask = torch.isfinite(target) & (target >= 0)
        if mask.any():
            scaled = torch.log1p(target[mask]) / np.log(3651.0)
            loss = loss + float(config.get("time_weight", 0.2)) * torch.nn.functional.smooth_l1_loss(outputs["time_prediction"][mask], scaled)
    return loss


def predict_advanced(model: nn.Module, family: str, frame: pd.DataFrame, store: AdvancedFeatureStore,
                     device: torch.device, batch_size: int, median: np.ndarray,
                     mean: np.ndarray, std: np.ndarray) -> pd.DataFrame:
    if family == "hierarchical_patient_fusion":
        dataset, collate = PatientDataset(frame, store, median, mean, std), collate_patients
    else:
        dataset, collate = AdvancedRowDataset(frame, store, family, median, mean, std), collate_rows
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=collate)
    rows = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            outputs = _forward(model, family, batch, device)
            logits = outputs["logits"]
            probs = torch.sigmoid(logits).cpu().numpy()
            if family == "hierarchical_patient_fusion":
                for i, patient in enumerate(batch["patients"]):
                    for sample_id, label in zip(patient["sample_ids"], patient["labels"]):
                        rows.append({"sample_id": sample_id, "patient_id": patient["patient_id"], "y_true": int(label), "y_logit": float(logits[i].cpu()), "y_prob": float(probs[i])})
            else:
                labels = batch["y"].numpy().astype(int)
                for i, sample_id in enumerate(batch["sample_ids"]):
                    rows.append({"sample_id": sample_id, "patient_id": batch["patient_ids"][i], "y_true": int(labels[i]), "y_logit": float(logits[i].cpu()), "y_prob": float(probs[i])})
    return pd.DataFrame(rows)


@dataclass
class AdvancedFit:
    model: nn.Module
    best_epoch: int
    history: list[dict]
    validation_predictions: pd.DataFrame | None
    cnv_median: np.ndarray
    cnv_mean: np.ndarray
    cnv_std: np.ndarray


def fit_advanced(family: str, train: pd.DataFrame, validation: pd.DataFrame | None,
                 store: AdvancedFeatureStore, config: dict, device: torch.device,
                 seed: int, fixed_epochs: int | None = None) -> AdvancedFit:
    set_seed(seed)
    median, mean, std = _preprocessing(train, store)
    model = build_advanced_model(family, store, config).to(device)
    batch_size = int(config.get("batch_size", 8))
    if family == "hierarchical_patient_fusion":
        dataset, collate = PatientDataset(train, store, median, mean, std), collate_patients
        patient_labels = train.groupby("patient_id")["y_progressor"].max().to_numpy(dtype=int)
        positives, negatives = int(patient_labels.sum()), int((patient_labels == 0).sum())
    else:
        dataset, collate = AdvancedRowDataset(train, store, family, median, mean, std), collate_rows
        labels = train["y_progressor"].to_numpy(dtype=int)
        positives, negatives = int(labels.sum()), int((labels == 0).sum())
    if not positives or not negatives:
        raise ValueError("advanced training split has one class")
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, collate_fn=collate)
    pos_weight = torch.tensor([negatives / positives], dtype=torch.float32, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config.get("lr", 1e-4)), weight_decay=float(config.get("weight_decay", 1e-2)))
    max_epochs, patience = int(fixed_epochs or config.get("max_epochs", 20)), int(config.get("patience", 5))
    best_score, best_state, best_epoch, bad_epochs = -np.inf, None, max_epochs, 0
    history = []
    for epoch in range(1, max_epochs + 1):
        model.train()
        losses = []
        for batch in loader:
            optimizer.zero_grad(set_to_none=True)
            outputs = _forward(model, family, batch, device)
            loss = _loss(outputs, batch, device, pos_weight, config)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        row = {"epoch": epoch, "train_loss": float(np.mean(losses))}
        if validation is not None:
            prediction = predict_advanced(model, family, validation, store, device, batch_size, median, mean, std)
            patient = patient_max_predictions(prediction)
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
    validation_predictions = None if validation is None else predict_advanced(model, family, validation, store, device, batch_size, median, mean, std)
    return AdvancedFit(model, int(best_epoch), history, validation_predictions, median, mean, std)
