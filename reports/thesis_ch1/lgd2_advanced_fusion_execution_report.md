# LGD2+ Advanced Fusion Execution Report

## Scope

Seven advanced architectures were implemented as supplementary post-hoc comparisons after the primary analysis was locked. No raw data, feature arrays, checkpoints, OOF prediction dumps, or Slurm logs are tracked in Git.

## Analysis contract

- Endpoint: `NextBiopsyProgression_LGD2plus`.
- Cohort: 707 strict pre-event rows; 150 patients; 50 positive and 100 negative patients.
- Evaluation: frozen five-fold patient-disjoint outer CV with three-fold patient-disjoint inner CV.
- Selection: patient-max inner-validation AUPRC only.
- Clinical threshold: inner-validation target of 90% specificity.
- Reporting: patient-max over complete OOF predictions.
- Role: `SUPPLEMENTARY_POST_HOC_ARCHITECTURE_SEARCH`.

## Architectures

| Family | Main mechanism | AUPRC | AUC | Brier |
|---|---|---:|---:|---:|
| Foundation ensemble | GigaPath/UNI2/Virchow2/CNV mixture | 0.636 | 0.728 | 0.208 |
| Hierarchical patient fusion | Slide-biopsy-patient hierarchy | 0.631 | 0.798 | 0.180 |
| Optimal transport | Sinkhorn chromosome-histology matching | 0.565 | 0.728 | 0.201 |
| Multitask temporal | Progression plus auxiliary time target | 0.534 | 0.700 | 0.231 |
| Low-rank bilinear | Factorized image-CNV interactions | 0.514 | 0.666 | 0.244 |
| CNV-token cross-attention | Bidirectional chromosome/tile attention | 0.507 | 0.690 | 0.244 |
| Reliability gated | Convex gate with bounded residual | 0.502 | 0.682 | 0.226 |

Locked late mean reference: AUPRC 0.630, AUC 0.774, Brier 0.184.

## Paired comparisons

- Foundation ensemble minus late mean AUPRC: +0.006 (95% CI -0.098 to 0.096).
- Hierarchical patient fusion minus late mean AUPRC: +0.001 (95% CI -0.108 to 0.132).
- Hierarchical patient fusion minus CNV-only AUC: +0.135 (95% CI 0.033 to 0.234).
- Hierarchical patient fusion minus image-only Brier: -0.065 (95% CI -0.114 to -0.017; lower is better).

No advanced architecture showed a conclusive AUPRC gain over late mean. Foundation ensemble has the highest AUPRC point estimate; hierarchical fusion has the strongest combined discrimination and calibration point estimates.

## Execution

- Training source commit: `6c22ddf`.
- External output: `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/`.
- GPU environment: `/home/zuberi01/miniforge3/envs/virchow2/bin/python`.
- Compute: L40S CUDA shards; CPU used for collection, metrics, and 5,000-replicate paired bootstrap.
- Completeness: 35/35 folds PASS; every OOF family has 707 rows and 150 patients.
- Infrastructure deviation: 16 first attempts hit an uncorrectable ECC error on `clust1-cuda-4` before training. They were preserved under external `failed_attempts/ecc_cuda4_20260713/` and rerun successfully with the node excluded.

## Outputs

- `lgd2_advanced_fusion_oof_completeness.csv/.md`
- `lgd2_advanced_fusion_model_comparison.csv/.md`
- `lgd2_advanced_fusion_paired_differences.csv/.md`
- `lgd2_advanced_fusion_interpretation.md`
- `lgd2_advanced_fusion_warnings.md`

All lightweight outputs are under `reports/thesis_ch1/`; model artifacts remain external.
