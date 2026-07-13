# LGD2+ Modality Ablation (feature-shuffle) - patient_max

Endpoint: `NextBiopsyProgression_LGD2plus`. Aggregation: patient_max. Evaluation: 5-fold patient-disjoint out-of-fold predictions.
Source campaign: `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/patchselect/uni2_signal`.

Feature shuffling permutes a modality across patients while the sample set is held fixed. A metric drop under shuffle is **supporting** evidence that the model relies on that modality, not causal proof. **shuffle_image is the direct test of the histology contribution.**

## Patient-max metrics by model and condition

| model | condition | n_patients | n_pos | AUPRC | ROC AUC | Brier |
|---|---|---:|---:|---:|---:|---:|
| coattn_abmil_cnv | baseline | 155 | 55 | 0.790 | 0.889 | 0.159 |
| coattn_abmil_cnv | shuffle_image | 155 | 55 | 0.685 | 0.749 | 0.232 |
| coattn_abmil_cnv | shuffle_cnv | 155 | 55 | 0.837 | 0.884 | 0.185 |
| coattn_abmil_cnv | shuffle_both | 155 | 55 | 0.453 | 0.565 | 0.269 |
| early_mean_mlp | baseline | 155 | 55 | 0.845 | 0.906 | 0.140 |
| early_mean_mlp | shuffle_image | 155 | 55 | 0.791 | 0.861 | 0.195 |
| early_mean_mlp | shuffle_cnv | 155 | 55 | 0.825 | 0.875 | 0.186 |
| early_mean_mlp | shuffle_both | 155 | 55 | 0.449 | 0.576 | 0.269 |
| early_mean_mlp_timev1 | baseline | 155 | 55 | 0.768 | 0.845 | 0.162 |
| early_mean_mlp_timev1 | shuffle_image | 155 | 55 | 0.714 | 0.806 | 0.193 |
| early_mean_mlp_timev1 | shuffle_cnv | 155 | 55 | 0.595 | 0.751 | 0.208 |
| early_mean_mlp_timev1 | shuffle_both | 155 | 55 | 0.557 | 0.722 | 0.217 |

## Deltas (baseline minus shuffle)

Positive AUPRC/AUC delta = shuffle performed worse than baseline (modality helped). For Brier (lower is better) a NEGATIVE delta = shuffle worse.

| model | comparison | dAUPRC | dROC_AUC | dBrier | matched_set |
|---|---|---:|---:|---:|:--:|
| coattn_abmil_cnv | baseline_minus_shuffle_image | +0.105 | +0.139 | -0.073 | yes |
| coattn_abmil_cnv | baseline_minus_shuffle_cnv | -0.047 | +0.005 | -0.026 | yes |
| coattn_abmil_cnv | baseline_minus_shuffle_both | +0.337 | +0.324 | -0.110 | yes |
| early_mean_mlp | baseline_minus_shuffle_image | +0.055 | +0.045 | -0.055 | yes |
| early_mean_mlp | baseline_minus_shuffle_cnv | +0.020 | +0.031 | -0.046 | yes |
| early_mean_mlp | baseline_minus_shuffle_both | +0.396 | +0.330 | -0.129 | yes |
| early_mean_mlp_timev1 | baseline_minus_shuffle_image | +0.053 | +0.039 | -0.032 | yes |
| early_mean_mlp_timev1 | baseline_minus_shuffle_cnv | +0.173 | +0.094 | -0.046 | yes |
| early_mean_mlp_timev1 | baseline_minus_shuffle_both | +0.210 | +0.123 | -0.055 | yes |

## Notes

- Metrics recomputed with `barrett.evaluation.metrics.compute_metrics` and `barrett.evaluation.aggregation.aggregate_predictions` (patient_max).
- Sample sets verified identical across conditions per model; see warnings file.
- No model was retrained; predictions are the saved out-of-fold campaign outputs.
