"""Fail-closed validation and collection of external outer-fold artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from barrett.evaluation.output_contract import validate_predictions


REQUIRED_FOLD_FILES = (
    "fold_completion.json",
    "fold_metadata.json",
    "inner_fold_assignments.csv",
    "inner_validation_predictions.csv",
    "inner_validation_leaderboard.csv",
    "outer_test_predictions.csv",
    "resolved_config.yaml",
    "training_history.json",
    "artifact_validation.json",
    "environment.txt",
)


def reject_repo_output(path: str | Path, repo_root: str | Path) -> None:
    target = Path(path).resolve()
    repo = Path(repo_root).resolve()
    if target == repo or repo in target.parents:
        raise ValueError(f"output must remain outside Git: {target}")


def validate_fold_directory(
    fold_dir: str | Path,
    expected_rows: pd.DataFrame,
    family: str,
    fold: int,
) -> tuple[list[str], pd.DataFrame | None]:
    fold_dir = Path(fold_dir)
    problems: list[str] = []
    for name in REQUIRED_FOLD_FILES:
        path = fold_dir / name
        if not path.exists() or path.stat().st_size == 0:
            problems.append(f"missing or empty artifact: {path}")
    if problems:
        return problems, None

    try:
        completion = json.loads((fold_dir / "fold_completion.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid fold completion JSON: {exc}"], None
    if completion.get("status") != "PASS":
        problems.append(f"completion status is {completion.get('status')!r}, expected PASS")
    if completion.get("family") != family or int(completion.get("outer_fold", -1)) != int(fold):
        problems.append("completion family/fold does not match requested fold")

    try:
        predictions = pd.read_csv(fold_dir / "outer_test_predictions.csv", dtype={"row_key": str, "sample_id": str})
    except Exception as exc:
        return problems + [f"cannot read predictions: {exc}"], None
    problems.extend(validate_predictions(predictions, expected_fold_values=[fold]))
    if set(predictions["model_family"].astype(str)) != {family}:
        problems.append(f"prediction model_family does not equal {family}")

    expected = expected_rows.copy()
    expected["sample_id"] = expected["sample_id"].astype(str)
    expected_map = expected.set_index("sample_id")
    actual_keys = set(predictions["row_key"].astype(str))
    expected_keys = set(expected_map.index)
    if actual_keys != expected_keys:
        problems.append(
            f"row-key mismatch: missing={len(expected_keys - actual_keys)} "
            f"extra={len(actual_keys - expected_keys)}"
        )
    common = sorted(actual_keys & expected_keys)
    if common:
        actual = predictions.set_index("row_key").loc[common]
        expected_common = expected_map.loc[common]
        if not actual["patient_id"].astype(str).equals(expected_common["patient_id"].astype(str)):
            problems.append("patient IDs disagree with frozen manifest")
        if not actual["y_true"].astype(int).equals(expected_common["y_progressor"].astype(int)):
            problems.append("labels disagree with frozen manifest")
    return problems, predictions


def collect_family(
    output_root: str | Path,
    manifest: pd.DataFrame,
    family: str,
    folds: tuple[int, ...] = (1, 2, 3, 4, 5),
) -> tuple[pd.DataFrame | None, list[dict]]:
    output_root = Path(output_root)
    reports: list[dict] = []
    frames = []
    for fold in folds:
        expected = manifest[manifest["fold_id_rep01"].eq(fold)].copy()
        problems, predictions = validate_fold_directory(
            output_root / family / f"fold{fold}", expected, family, fold
        )
        reports.append({
            "model_family": family,
            "outer_fold": fold,
            "status": "PASS" if not problems else "FAIL",
            "expected_rows": int(len(expected)),
            "prediction_rows": int(len(predictions)) if predictions is not None else 0,
            "expected_patients": int(expected["patient_id"].nunique()),
            "prediction_patients": int(predictions["patient_id"].nunique()) if predictions is not None else 0,
            "problems": "; ".join(problems),
        })
        if predictions is not None:
            frames.append(predictions)
    if any(row["status"] != "PASS" for row in reports):
        return None, reports
    combined = pd.concat(frames, ignore_index=True)
    problems = validate_predictions(combined, expected_fold_values=folds)
    if combined["row_key"].duplicated().any():
        problems.append("duplicate row_key across collected outer folds")
    if set(combined["row_key"].astype(str)) != set(manifest["sample_id"].astype(str)):
        problems.append("collected row keys do not equal frozen manifest")
    patient_folds = combined.groupby("patient_id")["outer_fold"].nunique()
    if patient_folds.gt(1).any():
        problems.append("one or more patients occur in multiple outer folds")
    if problems:
        reports.append({
            "model_family": family,
            "outer_fold": "ALL",
            "status": "FAIL",
            "expected_rows": int(len(manifest)),
            "prediction_rows": int(len(combined)),
            "expected_patients": int(manifest["patient_id"].nunique()),
            "prediction_patients": int(combined["patient_id"].nunique()),
            "problems": "; ".join(problems),
        })
        return None, reports
    return combined, reports
