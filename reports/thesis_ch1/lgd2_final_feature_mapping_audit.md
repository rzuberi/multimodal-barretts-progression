# LGD2+ Final Feature Mapping Audit

- Canonical rows: 707
- Unique CNV profiles: 693
- CNV profiles shared across rows: 26
- Unique slides: 707
- External feature-view root: `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/chapter1_lgd2_final_pre_event_20260713_final/feature_views`

| feature_view | modality | expected_rows | observed_rows | unique_sample_ids | missing_rows | unexpected_rows | duplicate_rows | paths_missing | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| features_5mb_armdiff.csv | cnv | 707 | 707 | 707 | 0 | 0 | 0 | 0 | PASS |
| features_arms.csv | cnv | 707 | 707 | 707 | 0 | 0 | 0 | 0 | PASS |
| cx.csv | cnv | 707 | 707 | 707 | 0 | 0 | 0 | 0 | PASS |
| uni2_index | image | 707 | 707 | 707 | 0 | 0 | 0 | 0 | PASS |

All feature matrices and NPZ references remain external to Git.
