"""CNV preprocessing and random-forest baseline."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_cnv_pipeline(params: dict, seed: int, n_jobs: int = 8) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("pca", PCA(n_components=int(params.get("pca_dim", 64)), random_state=seed)),
        ("model", RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 500)),
            max_depth=params.get("max_depth", 10),
            min_samples_leaf=int(params.get("min_samples_leaf", 2)),
            max_features=params.get("max_features", 0.5),
            class_weight="balanced",
            random_state=seed,
            n_jobs=n_jobs,
        )),
    ])


def genomic_feature_importance(pipeline: Pipeline, feature_names: list[str]) -> np.ndarray:
    """Project RF component importances back to original CNV features."""
    pca = pipeline.named_steps["pca"]
    model = pipeline.named_steps["model"]
    projected = np.abs(pca.components_).T @ np.asarray(model.feature_importances_, dtype=float)
    total = float(projected.sum())
    return projected / total if total > 0 else projected
