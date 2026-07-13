"""Feature loading for canonical-keyed final-rerun data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


CNV_METADATA = {"sample_id", "source_cnv_feature_id", "patient_id", "cnv_id", "slide_ref"}


def load_cnv_matrix(directory: str | Path) -> tuple[pd.DataFrame, list[str]]:
    directory = Path(directory)
    frames = []
    feature_names: list[str] = []
    for name in ("features_5mb_armdiff.csv", "features_arms.csv", "cx.csv"):
        frame = pd.read_csv(directory / name, low_memory=False)
        features = [column for column in frame.columns if column not in CNV_METADATA]
        if not features:
            raise ValueError(f"{name} has no feature columns")
        part = frame[["sample_id"] + features].copy()
        part["sample_id"] = part["sample_id"].astype(str)
        if part["sample_id"].duplicated().any():
            raise ValueError(f"{name} has duplicate canonical sample_id")
        frames.append(part)
        feature_names.extend(features)
    if len(set(feature_names)) != len(feature_names):
        raise ValueError("CNV feature names overlap across source views")
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="sample_id", how="inner", validate="one_to_one")
    for column in feature_names:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    return merged, feature_names


class CanonicalFeatureStore:
    def __init__(self, uni2_index: pd.DataFrame, cnv: pd.DataFrame, cnv_features: list[str]) -> None:
        index = uni2_index.copy()
        index["sample_id"] = index["sample_id"].astype(str)
        if index["sample_id"].duplicated().any():
            raise ValueError("UNI2 canonical sample_id must be unique")
        self.image_paths = dict(zip(index["sample_id"], index["npz_path"].astype(str)))
        # A final fold revisits each fixed UNI2 bag across inner candidates and
        # epochs. The full 707-row view fits comfortably in job memory, so a
        # process-local cache avoids repeatedly decompressing the same NPZ.
        self._bag_cache: dict[str, np.ndarray] = {}
        cnv = cnv.copy()
        cnv["sample_id"] = cnv["sample_id"].astype(str)
        self.cnv = cnv.set_index("sample_id")[cnv_features]
        self.cnv_features = list(cnv_features)

    def bag(self, sample_id: str) -> np.ndarray:
        sample_id = str(sample_id)
        if sample_id in self._bag_cache:
            return self._bag_cache[sample_id]
        path = self.image_paths[sample_id]
        with np.load(path, allow_pickle=False) as archive:
            bag = np.asarray(archive["embeddings"], dtype=np.float32)
        if bag.ndim != 2 or not np.isfinite(bag).all():
            raise ValueError(f"invalid UNI2 bag for {sample_id}: shape={bag.shape}")
        self._bag_cache[sample_id] = bag
        return bag

    def cnv_array(self, sample_ids: list[str]) -> np.ndarray:
        return self.cnv.loc[[str(value) for value in sample_ids]].to_numpy(dtype=np.float32)


class FinalDataset(Dataset):
    def __init__(
        self,
        frame: pd.DataFrame,
        store: CanonicalFeatureStore,
        family: str,
        cnv_median: np.ndarray | None = None,
        cnv_mean: np.ndarray | None = None,
        cnv_std: np.ndarray | None = None,
    ) -> None:
        self.frame = frame.reset_index(drop=True).copy()
        self.store = store
        self.family = family
        self.cnv_median = cnv_median
        self.cnv_mean = cnv_mean
        self.cnv_std = cnv_std

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> dict:
        row = self.frame.iloc[index]
        sample_id = str(row["sample_id"])
        item = {
            "sample_id": sample_id,
            "patient_id": str(row["patient_id"]),
            "y": torch.tensor(float(row["y_progressor"]), dtype=torch.float32),
        }
        if self.family != "cnv_only":
            item["bag"] = torch.from_numpy(self.store.bag(sample_id)).float()
        if self.family in {"early_fusion", "intermediate_fusion", "coattention_fusion"}:
            cnv = self.store.cnv_array([sample_id])[0]
            if self.cnv_median is not None:
                cnv = np.where(np.isfinite(cnv), cnv, self.cnv_median)
            if self.cnv_mean is not None and self.cnv_std is not None:
                cnv = (cnv - self.cnv_mean) / self.cnv_std
            if not np.isfinite(cnv).all():
                raise ValueError(f"non-finite standardized CNV features for {sample_id}")
            item["cnv"] = torch.from_numpy(cnv.astype(np.float32)).float()
        return item


def collate_final(batch: list[dict]) -> dict:
    out = {
        "sample_ids": [item["sample_id"] for item in batch],
        "patient_ids": [item["patient_id"] for item in batch],
        "y": torch.stack([item["y"] for item in batch]),
    }
    if "bag" in batch[0]:
        out["bags"] = [item["bag"] for item in batch]
    if "cnv" in batch[0]:
        out["cnv"] = torch.stack([item["cnv"] for item in batch])
    return out
