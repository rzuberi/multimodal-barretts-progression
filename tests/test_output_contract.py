"""Toy tests for the Phase 5 analysis-ready artifact contract."""

import pandas as pd

from barrett.evaluation.output_contract import (
    REQUIRED_PREDICTION_COLUMNS,
    REQUIRED_RUN_ARTIFACT_KEYS,
    validate_model_input_equality,
    validate_predictions,
    validate_run_completeness,
)


def _row(**over):
    row = {c: "x" for c in REQUIRED_PREDICTION_COLUMNS}
    row.update(
        model_name="cnv",
        patient_id="P1",
        row_key="rk1",
        outer_fold=1,
        y_true=0,
        y_prob=0.1,
        seed=1,
    )
    row.update(over)
    return row


def _valid_frame(folds=5):
    rows = []
    for f in range(1, folds + 1):
        rows.append(_row(outer_fold=f, row_key=f"rk{f}", patient_id=f"P{f}", y_true=f % 2, y_prob=0.3))
    return pd.DataFrame(rows)


def _manifest():
    return {k: "present" for k in REQUIRED_RUN_ARTIFACT_KEYS}


def test_valid_frame_passes():
    assert validate_predictions(_valid_frame(), expected_folds=5) == []


def test_duplicate_keys_fail():
    df = _valid_frame()
    dup = df.iloc[[0]].copy()
    df = pd.concat([df, dup], ignore_index=True)
    problems = validate_predictions(df, expected_folds=5)
    assert any("duplicate" in p for p in problems)


def test_incomplete_folds_fail():
    df = _valid_frame(folds=3)
    problems = validate_predictions(df, expected_folds=5)
    assert any("missing outer folds" in p for p in problems)


def test_single_fold_can_be_validated_explicitly():
    df = _valid_frame(folds=1)
    assert validate_predictions(df, expected_fold_values=[1]) == []


def test_missing_patient_id_fails():
    df = _valid_frame()
    df.loc[0, "patient_id"] = None
    problems = validate_predictions(df, expected_folds=5)
    assert any("patient_id" in p for p in problems)


def test_missing_required_column_fails():
    df = _valid_frame().drop(columns=["y_prob"])
    problems = validate_predictions(df, expected_folds=5)
    assert any("missing required columns" in p for p in problems)


def test_label_out_of_range_fails():
    df = _valid_frame()
    df.loc[0, "y_true"] = 2
    problems = validate_predictions(df, expected_folds=5)
    assert any("y_true" in p for p in problems)


def test_prob_out_of_range_fails():
    df = _valid_frame()
    df.loc[0, "y_prob"] = 1.5
    problems = validate_predictions(df, expected_folds=5)
    assert any("y_prob outside" in p for p in problems)


def test_model_input_equality_passes():
    frames = {"a": {"r1", "r2"}, "b": {"r2", "r1"}}
    assert validate_model_input_equality(frames) == []


def test_model_input_inequality_fails():
    frames = {"a": {"r1", "r2"}, "b": {"r1", "r3"}}
    assert validate_model_input_equality(frames)


def test_run_completeness_passes():
    assert validate_run_completeness(_manifest()) == []


def test_run_completeness_missing_artifact_fails():
    m = _manifest()
    del m["fold_checkpoints"]
    problems = validate_run_completeness(m)
    assert problems and "fold_checkpoints" in problems[0]
