import math

import numpy as np

from barrett.evaluation.metrics import compute_metrics, confusion_counts


def test_confusion_and_clinical_metrics():
    y_true = np.array([1, 1, 0, 0])
    y_prob = np.array([0.9, 0.4, 0.8, 0.1])
    y_pred = (y_prob >= 0.5).astype(int)

    assert confusion_counts(y_true, y_pred) == (1, 1, 1, 1)

    metrics = compute_metrics(y_true, y_prob)
    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["tn"] == 1
    assert metrics["fn"] == 1
    assert metrics["sensitivity"] == 0.5
    assert metrics["specificity"] == 0.5
    assert metrics["ppv"] == 0.5
    assert metrics["npv"] == 0.5
    assert metrics["false_positives_per_detected_progressor"] == 1.0
    assert not math.isnan(metrics["roc_auc"])
    assert not math.isnan(metrics["auprc"])


def test_metrics_handle_single_class():
    metrics = compute_metrics([1, 1], [0.2, 0.8])
    assert math.isnan(metrics["roc_auc"])
    assert metrics["n_units"] == 2

