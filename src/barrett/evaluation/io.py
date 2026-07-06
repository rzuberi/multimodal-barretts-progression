"""Manifest, cohort, and prediction IO helpers for external result files."""

from __future__ import annotations

import glob
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from barrett.labels.endpoints import LGD2_ENDPOINT

MASTER_COLS = [
    "SampleID",
    "PatientID",
    "BiopsyID_int",
    "BiopsyID_real",
    "PatientID_real",
    "CNVAbsPath",
    "ImageAbsPath",
    "DaysFromCurrentToEvent",
    LGD2_ENDPOINT,
]

MODEL_GROUP_COLS = [
    "model_name",
    "cnv_variant",
    "cnv_mask_name",
    "instance_k",
    "subsample_mode",
    "embed_pca_dim",
    "method_name",
    "n_experts",
    "experts",
]


@dataclass
class WarningRow:
    result_id: str
    severity: str
    message: str


def expand_braces(pattern: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]
    body = match.group(1)
    if re.fullmatch(r"-?\d+\.\.-?\d+", body):
        start, end = [int(x) for x in body.split("..")]
        step = 1 if end >= start else -1
        values = [str(i) for i in range(start, end + step, step)]
    else:
        values = body.split(",")
    out = []
    for value in values:
        out.extend(expand_braces(pattern[: match.start()] + value + pattern[match.end() :]))
    return out


def resolve_files(root: Path, pattern: str) -> list[Path]:
    if not pattern or pattern in {"NA", "MISSING", "REVIEW_MANUALLY", "nan"}:
        return []
    raw = Path(pattern)
    full = raw if raw.is_absolute() else root / raw
    files: list[Path] = []
    for expanded in expand_braces(str(full)):
        if any(ch in expanded for ch in "*?[]"):
            files.extend(Path(p) for p in glob.glob(expanded))
        else:
            path = Path(expanded)
            if path.exists():
                files.append(path)
    return sorted(set(files))


def normalize_key(series: pd.Series) -> pd.Series:
    return series.astype("string").str.replace(r"\.0$", "", regex=True).str.strip()


def load_manifest(path: Path, endpoint: str, statuses: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path).fillna("")
    keep = (
        df["status"].isin(statuses)
        & df["endpoint"].eq(endpoint)
        & df["task"].eq("binary progression")
        & ~df["prediction_file"].isin(["", "NA", "MISSING", "REVIEW_MANUALLY"])
    )
    return df.loc[keep].copy()


def load_master(root: Path, manifest_path: Path, endpoint: str) -> pd.DataFrame:
    cohort_rows = pd.read_csv(manifest_path).fillna("")
    cohort_path = cohort_rows.loc[cohort_rows["result_id"].eq("lgd2_primary_cohort"), "external_result_path"]
    if cohort_path.empty:
        raise RuntimeError("lgd2_primary_cohort not found in manifest")
    path = root / cohort_path.iloc[0]
    header = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [c for c in MASTER_COLS if c in header]
    if endpoint not in usecols:
        raise RuntimeError(f"{endpoint} not found in master cohort: {path}")
    master = pd.read_csv(path, usecols=usecols)
    master["sample_key"] = normalize_key(master["SampleID"])
    if "PatientID_real" in master:
        master["patient_id_master"] = normalize_key(master["PatientID_real"])
    else:
        master["patient_id_master"] = normalize_key(master["PatientID"])
    if "BiopsyID_int" in master:
        master["biopsy_id"] = normalize_key(master["BiopsyID_int"])
    elif "BiopsyID_real" in master:
        master["biopsy_id"] = normalize_key(master["BiopsyID_real"])
    else:
        master["biopsy_id"] = pd.NA
    master["label_master"] = pd.to_numeric(master[endpoint], errors="coerce")
    if "CNVAbsPath" in master:
        master["cnv_key"] = master["CNVAbsPath"].map(lambda x: Path(str(x)).name if pd.notna(x) else pd.NA)
        master["cnv_key"] = normalize_key(master["cnv_key"])
    else:
        master["cnv_key"] = pd.NA
    return master


def master_lookup(master: pd.DataFrame, key_col: str) -> pd.DataFrame:
    rows = master.dropna(subset=[key_col]).copy()
    if rows.empty:
        return pd.DataFrame()

    def first_nonmissing(values: pd.Series) -> object:
        values = values.dropna()
        return values.iloc[0] if len(values) else pd.NA

    def event_or_min(values: pd.Series) -> float:
        vals = pd.to_numeric(values, errors="coerce")
        if (vals == 0).any():
            return 0.0
        vals = vals.dropna()
        return float(vals.min()) if len(vals) else math.nan

    return (
        rows.groupby(key_col, dropna=False)
        .agg(
            patient_id_master=("patient_id_master", first_nonmissing),
            biopsy_id=("biopsy_id", first_nonmissing),
            DaysFromCurrentToEvent=("DaysFromCurrentToEvent", event_or_min),
            label_master=("label_master", "max"),
        )
        .reset_index()
        .rename(columns={key_col: "sample_key"})
    )


def load_predictions(files: list[Path], usecols_extra: list[str] | None = None) -> pd.DataFrame:
    frames = []
    for path in files:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        base_cols = ["sample_id", "patient_id", "fold", "y_true", "y_prob", "y_pred", "condition", "task_name"]
        cols = [c for c in base_cols + MODEL_GROUP_COLS + (usecols_extra or []) if c in header]
        part = pd.read_csv(path, usecols=cols)
        part["prediction_file"] = str(path)
        frames.append(part)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def join_master(pred: pd.DataFrame, master: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if "sample_id" not in pred.columns:
        return pred, "failed:no_sample_id"
    pred = pred.copy()
    pred["sample_key"] = normalize_key(pred["sample_id"])
    candidates = [
        ("sample_id->SampleID", master_lookup(master, "sample_key")),
        ("sample_id->basename(CNVAbsPath)", master_lookup(master, "cnv_key")),
    ]
    scored = []
    pred_keys = set(pred["sample_key"].dropna().astype(str))
    for name, lookup in candidates:
        if lookup.empty:
            scored.append((0, name, lookup))
        else:
            keys = set(lookup["sample_key"].dropna().astype(str))
            scored.append((len(pred_keys & keys), name, lookup))
    _, key, lookup = max(scored, key=lambda item: item[0])
    if lookup.empty:
        return pred, "failed:no_master_lookup"
    joined = pred.merge(lookup, on="sample_key", how="left", validate="many_to_one")
    if "patient_id" not in joined.columns or joined["patient_id"].isna().all():
        joined["patient_id"] = joined["patient_id_master"]
        key = f"{key}; patient_id from master"
    else:
        joined["patient_id"] = normalize_key(joined["patient_id"])
        missing = joined["patient_id"].isna()
        joined.loc[missing, "patient_id"] = joined.loc[missing, "patient_id_master"]
        key = f"prediction.patient_id; {key} for timing/biopsy"
    if "y_true" not in joined.columns or joined["y_true"].isna().all():
        joined["y_true"] = joined["label_master"]
    joined["y_true"] = pd.to_numeric(joined["y_true"], errors="coerce")
    joined["y_prob"] = pd.to_numeric(joined["y_prob"], errors="coerce")
    if "fold" in joined.columns:
        joined["fold"] = normalize_key(joined["fold"])
    else:
        joined["fold"] = pd.NA
    return joined, key


def group_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in MODEL_GROUP_COLS if c in df.columns]


def model_label(row: pd.Series, fallback: str) -> str:
    pieces = []
    for col in MODEL_GROUP_COLS:
        if col in row and pd.notna(row[col]) and str(row[col]) not in {"", "nan"}:
            pieces.append(f"{col}={row[col]}")
    return "; ".join(pieces) if pieces else fallback

