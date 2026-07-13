"""Analysis-ready artifact contract for LGD2+ outer-test predictions (Phase 5).

Pure Python. Importing this module must never require real data. All validators
fail closed: they return a list of human-readable problem strings, empty == OK.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Set

import math

# Columns every outer-test prediction row must carry. Order is the documented
# schema order (see docs/schemas/lgd2_oof_prediction_schema.md).
REQUIRED_PREDICTION_COLUMNS: List[str] = [
    "run_id",
    "cohort_release_id",
    "cohort_hash",
    "split_release_id",
    "split_hash",
    "model_family",
    "model_name",
    "configuration_id",
    "feature_model",
    "fusion_type",
    "cnv_representation",
    "outer_fold",
    "row_key",
    "patient_id",
    "biopsy_id",
    "sample_id",
    "slide_id",
    "cnv_id",
    "y_true",
    "y_prob",
    "strict_pre_event_eligible",
    "checkpoint_ref",
    "config_ref",
    "seed",
    "env_ref",
]

# Nullable/optional columns that may be absent or contain nulls.
OPTIONAL_PREDICTION_COLUMNS: List[str] = [
    "y_logit",
    "y_prob_calibrated",
]

# External artifact keys a completed run manifest must resolve (Phase 5).
REQUIRED_RUN_ARTIFACT_KEYS: List[str] = [
    "resolved_config",
    "git_commit",
    "git_dirty",
    "env_export",
    "input_manifests",
    "input_hashes",
    "inner_fold_assignments",
    "outer_fold_assignments",
    "inner_validation_predictions",
    "inner_validation_leaderboard",
    "outer_test_predictions",
    "fold_checkpoints",
    "fitted_preprocessing",
    "per_fold_metadata",
    "completeness_manifest",
]


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def validate_predictions(df, expected_folds: int = 5) -> List[str]:
    """Validate an outer-test prediction table. Empty list means it passed."""
    problems: List[str] = []

    missing_cols = [c for c in REQUIRED_PREDICTION_COLUMNS if c not in df.columns]
    if missing_cols:
        # Fail closed: without the key columns no further check is meaningful.
        return [f"missing required columns: {sorted(missing_cols)}"]

    if len(df) == 0:
        return ["prediction table is empty"]

    # Duplicate prediction keys.
    key_cols = ["model_name", "outer_fold", "row_key"]
    dup_mask = df.duplicated(subset=key_cols, keep=False)
    if dup_mask.any():
        dups = (
            df.loc[dup_mask, key_cols]
            .drop_duplicates()
            .to_dict(orient="records")
        )
        problems.append(f"duplicate (model_name, outer_fold, row_key) keys: {dups}")

    # Missing patient IDs.
    if df["patient_id"].map(_is_missing).any() or (df["patient_id"].astype(str).str.strip() == "").any():
        problems.append("missing patient_id in one or more rows")

    # Label domain.
    bad_labels = sorted(
        {v for v in df["y_true"].tolist() if v not in (0, 1)}
    )
    if bad_labels:
        problems.append(f"y_true values not in {{0,1}}: {bad_labels}")

    # Probability range.
    probs = df["y_prob"]
    if probs.map(_is_missing).any():
        problems.append("y_prob has missing values")
    out_of_range = [p for p in probs.tolist() if not _is_missing(p) and not (0.0 <= p <= 1.0)]
    if out_of_range:
        problems.append(f"y_prob outside [0,1]: {out_of_range}")

    # Outer-fold coverage: every expected fold must be present, per model_name.
    expected = set(range(expected_folds))
    for model_name, sub in df.groupby("model_name"):
        present = set(int(f) for f in sub["outer_fold"].tolist())
        missing_folds = expected - present
        if missing_folds:
            problems.append(
                f"model '{model_name}' missing outer folds {sorted(missing_folds)} "
                f"(expected {sorted(expected)})"
            )

    return problems


def validate_model_input_equality(frames_by_model: Mapping[str, Set]) -> List[str]:
    """Given {model_name: set_of_row_keys}, require all models share identical rows."""
    if len(frames_by_model) < 2:
        return []
    items = list(frames_by_model.items())
    ref_name, ref_keys = items[0]
    ref_keys = set(ref_keys)
    problems: List[str] = []
    for name, keys in items[1:]:
        keys = set(keys)
        if keys != ref_keys:
            problems.append(
                f"model '{name}' row keys differ from '{ref_name}': "
                f"missing={sorted(ref_keys - keys)} extra={sorted(keys - ref_keys)}"
            )
    return problems


def validate_run_completeness(manifest_dict: Mapping[str, object]) -> List[str]:
    """Return required artifact keys absent (or null) from a run manifest."""
    missing = [
        k
        for k in REQUIRED_RUN_ARTIFACT_KEYS
        if k not in manifest_dict or manifest_dict[k] in (None, "", [], {})
    ]
    if missing:
        return [f"missing required run artifacts: {missing}"]
    return []
