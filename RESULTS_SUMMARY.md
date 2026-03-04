# Results Summary

## Setup
- Snapshot source: `data_snapshots/coverage_status.csv`, `data_snapshots/model_leaderboard_binary_auc.csv`, `data_snapshots/task_leaders.csv`.
- Stable aggregate snapshot includes `315` rows (`304` complete, `11` incomplete).
- Full-coverage campaign plan in snapshot metadata: `864` total runlist rows, `402` trainable rows, `462` derived late-fusion rows, `0` blocked rows.
- Canonical progression definition: LGD3plus (`NextBiopsyProgression_LGD3plus`).
- Evaluation policy: `rep=1`, `folds=1..5`.

## Tasks
- Binary, multiclass, and regression task families are present.
- Binary leaderboard snapshot covers `16` tasks (top-50 rows only).
- Canonical progression task is explicitly included as `NextBiopsyProgression_LGD3plus`; legacy `NextBiopsyProgression` is deprecated.

## Models
- Discovered models: `23` (trainable + derived) across image, CNV, and multimodal families.
- Snapshot top-50 binary leaderboard modality composition: `47` multimodal, `3` image, `0` CNV.
- Task-leader modalities (all task types in `task_leaders.csv`): `20` multimodal, `1` image.

## Metrics
- Binary: AUC (primary in leaderboard), with sensitivity/specificity available.
- Multiclass: macro AUC OVR, macro F1, accuracy (in `task_leaders.csv` for multiclass tasks).
- Regression: MAE (leader metric in `task_leaders.csv`), with RMSE/R2 in broader internal summaries.

## Results highlights
- `NextBiopsyProgression_LGD3plus`: best observed multimodal AUC in this snapshot is `0.854` (`exclude_lgd_hgd_imc`), vs best image AUC `0.834`.
- `Progressor_label` (`all_samples`): best multimodal AUC `0.843` vs best image AUC `0.823`.
- Highest binary AUCs in this snapshot are dominated by multimodal `early_mean_mlp_timev1` across multiple tasks and exclusion conditions.
- Several top risk/progression rows occur under exclusion conditions (`exclude_hgd_imc`, `exclude_lgd_hgd_imc`), indicating condition dependence.
- CNV-only rows are not present in the top-50 binary leaderboard snapshot; this should be treated as a snapshot-table limitation, not a universal statement about all campaign runs.

## Headline task table (binary AUC, snapshot-derived)

| task | best multimodal AUC | best image AUC | best CNV AUC | notes |
|---|---:|---:|---:|---|
| NextBiopsyProgression_LGD3plus | 0.854 | 0.834 | NA | Best rows from `exclude_lgd_hgd_imc`; canonical progression endpoint |
| Progressor_label | 0.843 | 0.823 | NA | `all_samples` rows visible for multimodal and image |
| HasNextBiopsy | 0.873 | NA | NA | Only multimodal rows appear in top-50 snapshot |
| NextBiopsyExistsInDataset | 0.881 | NA | NA | Only multimodal rows appear in top-50 snapshot |
| AtRisk_1y | 0.995 | NA | NA | Only multimodal rows appear in top-50 snapshot |

`NA` means no row for that modality is present in the current top-50 binary leaderboard snapshot file.

## Observed tradeoffs
- Multimodal models lead most headline rows in this snapshot, but modality-level evidence is uneven because leaderboard storage is top-50 filtered.
- Exclusion-condition gains may reflect cleaner label regimes, but can also reduce representativeness for broader deployment populations.
- Strong AUC does not directly establish calibrated decision quality; operating-point safety still needs dedicated calibration and decision-curve analysis.
- Current snapshot supports comparative modeling claims at aggregate level, not clinical deployment claims.
