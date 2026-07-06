import numpy as np

from barrett.evaluation.thresholds import fixed_operating_points


def test_fixed_operating_points_return_requested_metrics():
    y_true = np.array([1, 1, 1, 0, 0, 0])
    y_prob = np.array([0.95, 0.8, 0.2, 0.7, 0.3, 0.1])
    out = fixed_operating_points(y_true, y_prob)

    assert "sensitivity_at_90_specificity" in out
    assert "sensitivity_at_95_specificity" in out
    assert "specificity_at_90_sensitivity" in out
    assert "specificity_at_95_sensitivity" in out
    assert 0 <= out["sensitivity_at_90_specificity"] <= 1
    assert 0 <= out["specificity_at_90_sensitivity"] <= 1

