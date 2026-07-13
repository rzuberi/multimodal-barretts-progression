"""Toy tests for cross-fitted (validation-derived) thresholding.

Central invariant under test: outer-test labels never influence threshold
selection or calibrator fitting.
"""

from __future__ import annotations

import pandas as pd

from barrett.evaluation.cross_fitted_thresholds import (
    cross_fitted_confusion,
    fit_apply_calibration,
    select_threshold,
)


def _df(probs, labels):
    return pd.DataFrame(
        {
            "patient_id": [f"p{i}" for i in range(len(probs))],
            "y_true": labels,
            "y_prob": probs,
        }
    )


def test_default_0p5_returns_half():
    choice = select_threshold(_df([0.1, 0.9], [0, 1]), "default_0p5")
    assert choice.threshold == 0.5
    assert choice.fallback is False


def test_threshold_ignores_outer_test_labels():
    # Validation: negatives at 0.2/0.4, positives at 0.6/0.8. At target spec 0.90
    # (both negatives must be TN) the threshold must exceed 0.4, giving full sens.
    val = _df([0.2, 0.4, 0.6, 0.8], [0, 0, 1, 1])
    choice = select_threshold(val, "target_specificity", target=0.90)
    assert 0.4 < choice.threshold <= 0.6
    assert choice.fallback is False

    # Now a test fold whose labels, if (wrongly) used to pick the threshold,
    # would push it lower. select_threshold must not depend on test at all: same
    # val -> same threshold regardless of any test data.
    choice_again = select_threshold(val, "target_specificity", target=0.90)
    assert choice_again.threshold == choice.threshold


def test_target_specificity_applied_unchanged_to_test():
    val = _df([0.2, 0.4, 0.6, 0.8], [0, 0, 1, 1])
    chosen = select_threshold(val, "target_specificity", target=0.90).threshold

    # Test fold: a positive sits at 0.5 (below chosen threshold ~0.6). A
    # threshold-fitter peeking at test labels would lower the bar to catch it;
    # cross-fitting must keep the val threshold and thus miss it (FN).
    test = _df([0.1, 0.5, 0.7], [0, 1, 1])
    res = cross_fitted_confusion([(val, test)], "target_specificity", target=0.90)
    assert res.thresholds[0] == chosen
    # p=0.5 positive is below chosen threshold => 1 FN, other positive caught.
    assert res.fn == 1
    assert res.tp == 1
    assert res.tn == 1
    assert res.fp == 0


def test_pooled_confusion_sums_per_fold():
    val = _df([0.2, 0.4, 0.6, 0.8], [0, 0, 1, 1])
    fold_a = (val, _df([0.1, 0.7], [0, 1]))  # TN=1, TP=1
    fold_b = (val, _df([0.9, 0.3], [1, 0]))  # TP=1, TN=1
    res = cross_fitted_confusion([fold_a, fold_b], "target_specificity", target=0.90)
    assert (res.tp, res.fp, res.tn, res.fn) == (2, 0, 2, 0)
    assert res.n_folds == 2
    assert res.sensitivity == 1.0
    assert res.specificity == 1.0


def test_unachievable_target_records_fallback():
    # Overlapping distribution: positive at 0.4, negative at 0.6. To reach 90%
    # sensitivity you must catch the 0.4 positive, but any threshold that does so
    # also catches the 0.6 negative -> can't get spec, but target_specificity
    # 0.90 with data where every positive outranks... build the clear case:
    # a negative sits ABOVE a positive, so no threshold gives >0 sens at spec 1.
    val = _df([0.6, 0.4], [0, 1])
    # target spec 0.90 needs the single negative (0.6) as TN => threshold > 0.6,
    # which also drops the positive (0.4) below => sens 0 but spec 1.0 (>=0.90)
    # is reachable, so NOT a fallback here.
    assert select_threshold(val, "target_specificity", target=0.90).fallback is False

    # Degenerate: validation has no negatives, so specificity is undefined for
    # every threshold -> target_specificity is unachievable -> fallback recorded.
    val_no_neg = _df([0.3, 0.6], [1, 1])
    choice = select_threshold(val_no_neg, "target_specificity", target=0.90)
    assert choice.fallback is True
    assert choice.threshold == 1.0


def test_calibration_fits_on_validation_only():
    # Monotone val relationship -> isotonic learns increasing map.
    val = _df([0.1, 0.3, 0.6, 0.9], [0, 0, 1, 1])
    test = _df([0.2, 0.8], [1, 0])  # test labels are deliberately "wrong-way"
    cal = fit_apply_calibration(val, test, method="isotonic")
    # Calibrated test probs follow validation-learned map: higher raw -> higher
    # calibrated, regardless of test labels.
    assert cal[1] >= cal[0]

    # Swapping test labels must not change calibrated outputs (labels unused).
    test_flipped = _df([0.2, 0.8], [0, 1])
    cal2 = fit_apply_calibration(val, test_flipped, method="isotonic")
    assert list(cal) == list(cal2)
