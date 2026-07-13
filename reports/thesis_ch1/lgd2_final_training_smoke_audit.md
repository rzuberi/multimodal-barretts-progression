# LGD2+ Final Training Smoke Audit

Gate status: **PASS** (4/4 families).

| model_family | outer_fold | status | expected_rows | prediction_rows | expected_patients | prediction_patients | selected_configuration_id | probability_min | probability_max | problems |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cnv_only | 1 | PASS | 174 | 174 | 30 | 30 | cnv_rf_conservative | 0.025 | 0.475 |  |
| image_only | 1 | PASS | 174 | 174 | 30 | 30 | uni2_abmil_fixed | 0.005 | 0.977 |  |
| early_fusion | 1 | PASS | 174 | 174 | 30 | 30 | early_mean_mlp_fixed | 0.000 | 0.999 |  |
| intermediate_fusion | 1 | PASS | 174 | 174 | 30 | 30 | intermediate_lr1e4 | 0.001 | 1.000 |  |

Folds 2-5 must not be launched until all four families pass.
