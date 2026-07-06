import pandas as pd

from barrett.evaluation.aggregation import aggregate_predictions


def toy_predictions():
    return pd.DataFrame(
        {
            "sample_key": ["s1", "s2", "s3", "s4"],
            "patient_id": ["p1", "p1", "p2", "p2"],
            "biopsy_id": ["b1", "b1", "b2", "b3"],
            "fold": ["1", "1", "2", "2"],
            "y_true": [1, 1, 0, 0],
            "y_prob": [0.2, 0.8, 0.4, 0.9],
        }
    )


def test_patient_max_aggregation():
    out = aggregate_predictions(toy_predictions(), "patient_max")
    assert len(out) == 2
    assert out.loc[out["unit_id"].eq("p1"), "y_prob"].iloc[0] == 0.8
    assert out.loc[out["unit_id"].eq("p2"), "y_prob"].iloc[0] == 0.9


def test_patient_mean_aggregation():
    out = aggregate_predictions(toy_predictions(), "patient_mean")
    assert out.loc[out["unit_id"].eq("p1"), "y_prob"].iloc[0] == 0.5
    assert out.loc[out["unit_id"].eq("p2"), "y_prob"].iloc[0] == 0.65


def test_biopsy_max_aggregation():
    out = aggregate_predictions(toy_predictions(), "biopsy_max")
    assert len(out) == 3
    assert out.loc[out["unit_id"].eq("b1"), "y_prob"].iloc[0] == 0.8

