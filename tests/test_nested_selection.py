"""Leakage and correctness tests for nested_selection, synthetic data only."""
import numpy as np
import pandas as pd
import pytest

from barrett.evaluation.nested_selection import (
    make_inner_folds,
    patient_max,
    select_per_outer_fold,
)


def _frame(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "outer_fold",
            "inner_fold",
            "configuration_id",
            "patient_id",
            "y_true",
            "y_prob",
        ],
    )


def _two_candidate_fold():
    """One outer fold, two candidates. cfg_good separates classes, cfg_bad does not."""
    rows = []
    # patients p0..p3, y_true=1 for p2,p3
    truth = {"p0": 0, "p1": 0, "p2": 1, "p3": 1}
    good = {"p0": 0.1, "p1": 0.2, "p2": 0.9, "p3": 0.8}
    bad = {"p0": 0.8, "p1": 0.7, "p2": 0.2, "p3": 0.1}
    for i, p in enumerate(truth):
        fold = i % 2  # spread across 2 inner folds, disjoint per patient
        rows.append([0, fold, "cfg_good", p, truth[p], good[p]])
        rows.append([0, fold, "cfg_bad", p, truth[p], bad[p]])
    return _frame(rows)


def test_outer_test_rows_cannot_enter_selection():
    df = _two_candidate_fold()
    # p2 is an outer-test patient but appears in inner preds -> must fail closed.
    with pytest.raises(ValueError, match="outer-test"):
        select_per_outer_fold(df, outer_test_patients={0: {"p2"}})


def test_validation_selection_picks_higher_auprc():
    df = _two_candidate_fold()
    winners, board = select_per_outer_fold(df, outer_test_patients={0: set()})
    assert winners[0] == "cfg_good"
    good = board[board.configuration_id == "cfg_good"].iloc[0]
    bad = board[board.configuration_id == "cfg_bad"].iloc[0]
    assert good.auprc > bad.auprc


def test_leaderboard_complete_sorted_and_deterministic_tiebreak():
    # Two candidates with identical metrics -> tiebreak by configuration_id asc.
    rows = []
    truth = {"p0": 0, "p1": 1}
    prob = {"p0": 0.2, "p1": 0.8}
    for i, p in enumerate(truth):
        for cfg in ("cfg_b", "cfg_a"):  # deliberately not sorted
            rows.append([0, i % 2, cfg, p, truth[p], prob[p]])
    winners, board = select_per_outer_fold(_frame(rows), outer_test_patients={0: set()})
    assert set(board.configuration_id) == {"cfg_a", "cfg_b"}  # all candidates
    assert list(board.sort_values("rank").configuration_id) == ["cfg_a", "cfg_b"]
    assert winners[0] == "cfg_a"  # tie broken deterministically by name


def test_patient_in_two_inner_folds_fails_closed():
    rows = [
        [0, 0, "cfg", "p0", 0, 0.2],
        [0, 1, "cfg", "p0", 0, 0.3],  # same patient, two inner folds
        [0, 0, "cfg", "p1", 1, 0.8],
    ]
    with pytest.raises(ValueError, match=">1 inner fold"):
        select_per_outer_fold(_frame(rows), outer_test_patients={0: set()})


def test_inner_folds_patient_disjoint_and_deterministic():
    patients = [f"p{i}" for i in range(10)]
    a = make_inner_folds(patients, n_inner=3, seed=42)
    b = make_inner_folds(list(reversed(patients)), n_inner=3, seed=42)
    assert a == b  # deterministic, order-independent
    assert make_inner_folds(patients, 3, seed=7) != a  # seed matters
    # each patient in exactly one fold, folds cover everyone
    assert set(a.keys()) == set(patients)
    counts = np.bincount(list(a.values()))
    assert counts.sum() == len(patients)
    assert (counts >= len(patients) // 3).all()  # balanced


def test_patient_max_aggregation_used_before_ranking():
    # Two rows for p0 (label 1): a low and a high prob. patient_max must keep 0.9.
    rows = [
        [0, 0, "cfg", "p0", 1, 0.1],
        [0, 0, "cfg", "p0", 1, 0.9],
        [0, 1, "cfg", "p1", 0, 0.2],
    ]
    agg = patient_max(_frame(rows))
    assert set(agg.patient_id) == {"p0", "p1"}
    assert agg.loc[agg.patient_id == "p0", "y_prob"].item() == 0.9
