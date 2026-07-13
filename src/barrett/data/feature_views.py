"""Canonical-keyed feature views for the frozen LGD2+ cohort."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import pandas as pd

from barrett.utils.path_remap import resolve_existing_path


MAPPING_COLUMNS = [
    "canonical_row_key",
    "patient_id",
    "cnv_id",
    "slide_ref",
]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_matched_mapping(matched: pd.DataFrame) -> None:
    missing = sorted(set(MAPPING_COLUMNS) - set(matched.columns))
    if missing:
        raise ValueError(f"matched manifest missing columns: {missing}")
    if matched["canonical_row_key"].isna().any():
        raise ValueError("canonical_row_key contains missing values")
    if matched["canonical_row_key"].astype(str).duplicated().any():
        raise ValueError("canonical_row_key must be unique")
    for column in ("cnv_id", "slide_ref"):
        if matched[column].isna().any() or matched[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} contains missing values")


def canonical_cnv_view(matched: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    """Re-key one CNV matrix from source CNV IDs to canonical modelling rows."""
    validate_matched_mapping(matched)
    if "sample_id" not in source.columns:
        raise ValueError("CNV source missing sample_id")
    src = source.copy()
    src["sample_id"] = src["sample_id"].astype(str)
    if src["sample_id"].duplicated().any():
        examples = src.loc[src["sample_id"].duplicated(False), "sample_id"].head(5).tolist()
        raise ValueError(f"CNV source sample_id is not unique: {examples}")

    mapping = matched[MAPPING_COLUMNS].copy()
    mapping["cnv_id"] = mapping["cnv_id"].astype(str)
    mapping["canonical_row_key"] = mapping["canonical_row_key"].astype(str)
    out = mapping.merge(
        src,
        left_on="cnv_id",
        right_on="sample_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    missing = out["_merge"].ne("both")
    if missing.any():
        examples = out.loc[missing, ["canonical_row_key", "cnv_id"]].head(10).to_dict("records")
        raise ValueError(f"CNV source missing {int(missing.sum())} canonical rows: {examples}")
    out = out.drop(columns=["_merge", "sample_id"])
    out.insert(0, "sample_id", out.pop("canonical_row_key"))
    out.insert(1, "source_cnv_feature_id", out["cnv_id"].astype(str))
    metadata = ["sample_id", "source_cnv_feature_id", "patient_id", "cnv_id", "slide_ref"]
    features = [column for column in out.columns if column not in metadata]
    if not features:
        raise ValueError("CNV source has no feature columns")
    if out[features].isna().all(axis=1).any():
        raise ValueError("CNV source has canonical rows with all feature values missing")
    return out[metadata + features]


def canonical_uni2_index(
    matched: pd.DataFrame,
    source_index: pd.DataFrame,
    remap_rules: list[dict[str, str]] | None = None,
    candidate_roots: Iterable[str | Path] | None = None,
) -> pd.DataFrame:
    """Build a one-row-per-canonical-sample UNI2 index without loading tensors."""
    validate_matched_mapping(matched)
    required = {"sample_id", "image_basename", "npz_path"}
    missing_cols = sorted(required - set(source_index.columns))
    if missing_cols:
        raise ValueError(f"UNI2 source index missing columns: {missing_cols}")
    idx = source_index.copy()
    idx["sample_id"] = idx["sample_id"].astype(str)
    idx["image_basename"] = idx["image_basename"].astype(str)
    pair_cols = ["sample_id", "image_basename"]
    if idx.duplicated(pair_cols).any():
        examples = idx.loc[idx.duplicated(pair_cols, False), pair_cols].head(5).to_dict("records")
        raise ValueError(f"UNI2 index key is ambiguous: {examples}")

    mapping = matched[MAPPING_COLUMNS].copy()
    mapping["cnv_id"] = mapping["cnv_id"].astype(str)
    mapping["slide_ref"] = mapping["slide_ref"].astype(str)
    mapping["canonical_row_key"] = mapping["canonical_row_key"].astype(str)
    out = mapping.merge(
        idx,
        left_on=["cnv_id", "slide_ref"],
        right_on=["sample_id", "image_basename"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    missing = out["_merge"].ne("both")
    if missing.any():
        examples = out.loc[missing, ["canonical_row_key", "cnv_id", "slide_ref"]].head(10).to_dict("records")
        raise ValueError(f"UNI2 index missing {int(missing.sum())} canonical rows: {examples}")

    resolved = out["npz_path"].map(
        lambda value: resolve_existing_path(value, remap_rules, list(candidate_roots or []))
    )
    out["source_npz_path"] = out["npz_path"].astype(str)
    out["npz_path"] = resolved.map(lambda value: value[0])
    out["path_exists"] = resolved.map(lambda value: bool(value[1]))
    out["path_remap_rule"] = resolved.map(lambda value: value[2])
    if not out["path_exists"].all():
        examples = out.loc[~out["path_exists"], ["canonical_row_key", "source_npz_path"]].head(10).to_dict("records")
        raise ValueError(f"UNI2 NPZ path missing for {int((~out['path_exists']).sum())} rows: {examples}")

    out["source_feature_sample_id"] = out["sample_id"].astype(str)
    out["sample_id"] = out["canonical_row_key"].astype(str)
    out = out.drop(columns=["canonical_row_key", "_merge"])
    preferred = [
        "sample_id",
        "patient_id",
        "source_feature_sample_id",
        "cnv_id",
        "image_basename",
        "npz_path",
        "source_npz_path",
        "n_instances",
        "feat_dim",
        "status",
        "path_exists",
        "path_remap_rule",
    ]
    return out[[column for column in preferred if column in out.columns] + [
        column for column in out.columns if column not in preferred
    ]]


def feature_view_audit(
    matched: pd.DataFrame,
    cnv_views: dict[str, pd.DataFrame],
    uni2_index: pd.DataFrame,
) -> pd.DataFrame:
    expected = set(matched["canonical_row_key"].astype(str))
    rows = []
    for name, frame in cnv_views.items():
        observed = set(frame["sample_id"].astype(str))
        rows.append({
            "feature_view": name,
            "modality": "cnv",
            "expected_rows": len(expected),
            "observed_rows": len(frame),
            "unique_sample_ids": frame["sample_id"].astype(str).nunique(),
            "missing_rows": len(expected - observed),
            "unexpected_rows": len(observed - expected),
            "duplicate_rows": int(frame["sample_id"].astype(str).duplicated().sum()),
            "paths_missing": 0,
            "status": "PASS" if observed == expected and len(frame) == len(expected) else "FAIL",
        })
    observed = set(uni2_index["sample_id"].astype(str))
    missing_paths = int((~uni2_index["path_exists"].astype(bool)).sum()) if "path_exists" in uni2_index else -1
    rows.append({
        "feature_view": "uni2_index",
        "modality": "image",
        "expected_rows": len(expected),
        "observed_rows": len(uni2_index),
        "unique_sample_ids": uni2_index["sample_id"].astype(str).nunique(),
        "missing_rows": len(expected - observed),
        "unexpected_rows": len(observed - expected),
        "duplicate_rows": int(uni2_index["sample_id"].astype(str).duplicated().sum()),
        "paths_missing": missing_paths,
        "status": "PASS" if observed == expected and len(uni2_index) == len(expected) and missing_paths == 0 else "FAIL",
    })
    return pd.DataFrame(rows)
