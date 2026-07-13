# LGD2+ Final Co-attention Retraining

## Status

Complete. Five patient-disjoint outer folds were trained on the frozen strict pre-event cohort. Co-attention is supplementary post-hoc evidence because it was requested after review of the prespecified primary model results.

## Design

- Cohort: 707 modelling rows and 150 patients; 50 positive and 100 negative patients.
- Endpoint: `NextBiopsyProgression_LGD2plus`.
- Model: CNV-conditioned attention over UNI2 tile embeddings plus a CNV branch.
- Selection: pooled inner-validation patient-level AUPRC only.
- Candidates: learning rates `1e-4` and `3e-4`; all other architecture settings fixed.
- Reporting: outer-OOF patient maximum probability.
- Thresholds and Platt calibration: fitted on inner-validation predictions only.

## Execution

| Fold | Slurm job | Selected configuration | Status |
|---:|---:|---|---|
| 1 | `55147064` | `coattention_lr1e4` | PASS |
| 2 | `55147145` | `coattention_lr3e4` | PASS |
| 3 | `55147146` | `coattention_lr3e4` | PASS |
| 4 | `55147147` | `coattention_lr3e4` | PASS |
| 5 | `55147149` | `coattention_lr3e4` | PASS |

External outputs: `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/coattention_fusion/`.

## Results

| AUPRC | ROC AUC | Brier | Sensitivity | Specificity | TP | FP |
|---:|---:|---:|---:|---:|---:|---:|
| 0.548 | 0.739 | 0.230 | 0.52 | 0.80 | 26 | 20 |

- Co-attention minus CNV AUPRC: +0.010 (95% paired bootstrap CI -0.103 to 0.136).
- Co-attention minus image-only AUPRC: -0.009 (95% CI -0.131 to 0.099).
- Co-attention ranks below late mean, early fusion, and intermediate fusion by the primary AUPRC metric.

## Validation

- Five of five folds passed the external artifact contract.
- OOF coverage: 707/707 rows and 150/150 patients.
- No threshold fallback occurred.
- OOF SHA-256: `19d954331ae53d656676281b8d677816e3b678deaabcd11d7dfe33944817fbd5`.
- Heavy checkpoints, inner predictions, OOF predictions, and logs remain external.
