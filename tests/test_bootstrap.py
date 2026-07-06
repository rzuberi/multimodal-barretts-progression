import pandas as pd

from barrett.evaluation.bootstrap import bootstrap_cis


def test_bootstrap_runs_on_toy_data():
    df = pd.DataFrame({"y_true": [0, 0, 1, 1], "y_prob": [0.1, 0.4, 0.6, 0.9]})
    out = bootstrap_cis(df, n_boot=20, seed=1)
    assert "roc_auc_ci_low" in out
    assert "npv_ci_high" in out

