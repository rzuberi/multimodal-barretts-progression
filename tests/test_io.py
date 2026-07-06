import pandas as pd

from barrett.evaluation.io import join_master


def test_join_master_fills_missing_patient_id_from_cnv_basename():
    pred = pd.DataFrame({"sample_id": ["SLX1"], "y_true": [1], "y_prob": [0.8], "fold": [1]})
    master = pd.DataFrame(
        {
            "sample_key": ["1"],
            "cnv_key": ["SLX1"],
            "patient_id_master": ["P1"],
            "biopsy_id": ["B1"],
            "DaysFromCurrentToEvent": [5],
            "label_master": [1],
        }
    )
    joined, key = join_master(pred, master)
    assert joined["patient_id"].iloc[0] == "P1"
    assert "basename(CNVAbsPath)" in key

