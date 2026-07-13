# Final Analysis Training Completion Execution Report

## Outcome

`COMPLETE`. The strict pre-event five-fold rerun, leakage-safe late fusion, supplementary co-attention rerun, OOF validation, patient-level metrics, paired comparisons, and final case reselection all completed.

## Repository state

- Starting commit: `5954b5789202025631367ba713f6164a00d907d7`.
- Branch: `main`.
- Base-run commit: `98ba86820b3a3a33cd61f1f6724f20da38e9c8da`; pushed to `origin/main` under `rzuberi` before training.
- Late-alignment fix commit: `8d12c49`; pushed before corrected late-fusion regeneration.
- Final documentation/report state: validated on `main` and pushed to `origin/main` after this report update; use repository `HEAD` for the immutable commit ID.
- Co-attention implementation/training commit: `0e736d48`; pushed before co-attention training.
- No raw cohort data, feature tensors, prediction dumps, checkpoints, or Slurm logs are being written into Git.

## Frozen analysis

- Endpoint: `NextBiopsyProgression_LGD2plus`.
- Definition: HGD/IMC/OAC or two consecutive LGD biopsies.
- Analysis set: strict pre-event; at-event and post-event rows excluded before splitting.
- Cohort: 707 canonical modelling rows, 150 patients, 693 unique CNV profiles.
- Evaluation: frozen five-fold patient-disjoint outer CV; 30 patients per fold, with 10 positive and 20 negative patients per fold.
- Primary aggregation: patient maximum probability.
- Selection metric: pooled inner-validation patient-level AUPRC.
- Clinical threshold: selected on inner validation to target 90% specificity and applied unchanged to the matching outer fold.

## Feature mapping

- Frozen release: `analysis/chapter1_lgd2_final_pre_event_20260713_final/` outside Git.
- CNV source views:
  - `data/killcoyne_repro_strict_500kb_slurm_v2/features_5mb_armdiff.csv`
  - `data/killcoyne_repro_strict_500kb_slurm_v2/features_arms.csv`
  - `data/killcoyne_repro_strict_500kb_slurm_v2/cx.csv`
- UNI2 source index: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/image/all_samples/core_gpu/index/virchow2_index.csv`.
- Mapping strategy: canonical row ID joined through validated source CNV ID plus slide basename; shared CNV profiles remain separate canonical modelling rows.
- Coverage: CNV 707/707; UNI2 707/707; ambiguous or missing mappings 0.
- CNV dimensions: 632 total features. UNI2 dimension: 1536 with 256 instances per indexed bag.
- Audit: `reports/thesis_ch1/lgd2_final_feature_mapping_audit.md`.

## Manifest identity

- External training manifest: `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_manifest_v2.csv`.
- `sample_id` and `canonical_row_key` are unique canonical modelling-row identifiers.
- Source CNV and image identifiers are retained separately; repeated source CNV profiles do not collapse rows.
- Manifest SHA-256: `393cf2c02723f8d30ded4162bc9fd6437046b7eea07a4a42839fccff691b5968`.

## Model registry

Registry: `configs/chapter1_lgd2_final_models.yaml`.

- CNV-only random forest: three finite candidates (`cnv_rf_devbest`, `cnv_rf_conservative`, `cnv_rf_unrestricted`), with train-only median imputation, scaling, PCA-64, and patient-disjoint inner selection.
- Image-only: fixed UNI2 ABMIL (`uni2_abmil_fixed`).
- Early fusion: fixed UNI2 mean-pooling plus CNV MLP (`early_mean_mlp_fixed`).
- Intermediate fusion: ABMIL plus CNV branch, with two frozen learning-rate candidates (`intermediate_lr1e4`, `intermediate_lr3e4`).
- Late mean: prespecified arithmetic mean of matching CNV/image probabilities.
- Late stack-logit: logistic meta-model trained from patient-disjoint inner-OOF base predictions with equal patient weighting; meta-predictions used for threshold selection are themselves inner-cross-fitted.

Supplementary co-attention registry: `configs/chapter1_lgd2_final_coattention.yaml`.

- Co-attention: CNV-conditioned query attention over UNI2 tiles plus a CNV branch (`coattn_abmil_cnv`). Learning rates `1e-4` and `3e-4` were selected independently within each outer fold using pooled inner-validation patient predictions.
- Co-attention was requested after the primary model results were reviewed. It uses the same leakage controls and cohort but is labelled supplementary post-hoc rather than prespecified primary evidence.

## Leakage controls implemented

- The migrated neural fit API accepts train and optional validation inputs only; no outer-test loader is accepted.
- Early stopping and final epoch selection use inner validation only. The final outer-training fit uses the median selected inner best epoch.
- CNV tuning uses patient-stratified inner folds rather than row-level `StratifiedKFold` over samples.
- CNV imputation, scaling, PCA, and neural CNV standardisation are fitted from outer/inner training rows only.
- Candidate ranking aggregates held-out inner predictions to one score per patient with independent maximum label and maximum probability.
- Thresholds and Platt calibration are fitted from selected inner-validation patient predictions only.
- Late stacking does not select a variant from pooled outer-test results.
- Every fold is checked against the frozen row, patient, label, and fold assignments before a completion marker is written.

## Runtime validation

- CPU/test environment: `/home/zuberi01/miniforge3/envs/erin/bin/python`.
- H200-compatible neural environment: `/home/zuberi01/miniforge3/envs/virchow2/bin/python` with PyTorch `2.9.1+cu128`.
- GPU probe job `55144069`: passed on NVIDIA H200.
- `/home/zuberi01/miniforge3/envs/erin/bin/python` has PyTorch `2.0.1+cu117` and cannot execute on H200 (`no kernel image is available`).
- `/home/zuberi01/miniforge3/envs/pathology/bin/python` has CPU-only PyTorch and is unsuitable for neural training.

## Smoke jobs

| Job | Family | Result | Runtime | Note |
|---|---|---|---:|---|
| `55143462` | CNV-only fold 1 | PASS | 00:00:14 | 174 rows, 30 patients; selected `cnv_rf_conservative`. |
| `55143478` | Image fold 1 | FAILED | 00:06:15 | Wrong CUDA build; failed at first CUDA kernel. Preserved externally. |
| `55144080` | Image fold 1 | CANCELLED | 00:03:xx | Compatible environment but pre-cache I/O was inefficient; preserved externally. |
| `55144148` | Image fold 1 | PASS | 00:00:47 | Cached fixed UNI2 bags; 174 rows and 30 patients. |
| `55144153` | Early fusion fold 1 | PASS | 00:00:47 | 174 rows, 30 patients. |
| `55144154` | Intermediate fusion fold 1 | PASS | 00:01:23 | Selected `intermediate_lr1e4` on inner validation. |

The smoke gate reported 4/4 PASS before full submission.

Supplementary co-attention fold-1 smoke job `55147064` passed in 63 seconds. The expanded artifact smoke gate then reported 5/5 PASS.

## Final Slurm jobs

- CNV-only: jobs `55144170`-`55144174`; all PASS; 20-31 seconds per fold.
- Image-only: jobs `55144175`-`55144179`; all PASS; 32-41 seconds per fold.
- Early fusion: jobs `55144180`-`55144184`; all PASS; 34-44 seconds per fold.
- Intermediate fusion: jobs `55144185`-`55144189`; all PASS; 54-86 seconds per fold.
- Co-attention fusion: jobs `55147064`, `55147145`, `55147146`, `55147147`, and `55147149`; all PASS; 56-68 seconds per fold.
- Launch manifest: `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/launch_manifest_full_20260713_161453.json`.

## Fold completion matrix

| Family | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
|---|---|---|---|---|---|
| CNV-only | PASS | PASS | PASS | PASS | PASS |
| Image-only | PASS | PASS | PASS | PASS | PASS |
| Early fusion | PASS | PASS | PASS | PASS | PASS |
| Intermediate fusion | PASS | PASS | PASS | PASS | PASS |
| Co-attention fusion | PASS | PASS | PASS | PASS | PASS |
| Late mean | PASS | PASS | PASS | PASS | PASS |
| Late stack-logit | PASS | PASS | PASS | PASS | PASS |

## Fold selections and thresholds

- CNV selected `cnv_rf_conservative` in all five folds. Validation-derived thresholds: 0.334, 0.345, 0.314, 0.323, 0.295.
- Image used fixed `uni2_abmil_fixed`. Thresholds: 0.610, 0.609, 0.622, 0.691, 0.772.
- Early fusion used fixed `early_mean_mlp_fixed`. Thresholds: 0.781, 0.516, 0.771, 0.785, 0.681.
- Intermediate selected `intermediate_lr1e4` independently in all five folds. Thresholds: 0.808, 0.862, 0.529, 0.621, 0.676.
- Co-attention selected `coattention_lr1e4` in fold 1 and `coattention_lr3e4` in folds 2-5. Thresholds: 0.706, 0.692, 0.829, 0.864, 0.674.
- Late mean thresholds: 0.450, 0.424, 0.432, 0.444, 0.477.
- Late stack-logit thresholds: 0.336, 0.281, 0.311, 0.264, 0.297.
- No threshold selection used its matching outer-test labels; no fold required a threshold fallback.

## Artifacts retained externally per trained fold

- Raw outer-test logits and probabilities.
- Calibrated probabilities kept separately from raw probabilities.
- Inner fold assignments, inner held-out predictions, and validation leaderboard.
- Selected configuration and fixed final epoch count.
- Model checkpoint or fitted CNV pipeline.
- Platt calibrator and validation-derived threshold.
- CNV feature importances projected to ordered original features.
- UNI2 index/config needed to regenerate attention.
- Environment, input hashes, fold metadata, artifact-validation result, and completion marker.

## Validation

- Feature-view gate: PASS at 707/707 for both modalities.
- Targeted and full toy suite: 140 tests passing in the `erin` environment.
- Migrated ABMIL, early-fusion, intermediate-fusion, and co-attention modules produce identical outputs to legacy definitions after loading identical state dictionaries.
- All seven OOF files pass the final artifact collection contract.
- OOF completeness: 707 unique rows, 150 patients, five folds for every family; one patient occurs in exactly one outer fold.
- OOF hashes: CNV `9e1c9a9f5ef6...`; image `1ee345ea6e89...`; early `707c6e603080...`; intermediate `058d6914c221...`; co-attention `19d954331ae5...`; corrected late mean `964d624f7efe...`; corrected late stack-logit `6ecd41b7853e...`.
- Data guard: PASS after staging final lightweight reports.

## Failures and deviations

- Image smoke job `55143478` used an incompatible CUDA build and failed before a valid fold artifact. It was preserved externally and not reused.
- Image smoke job `55144080` was cancelled after detecting repeated NPZ decompression. A process-local immutable feature cache removed redundant I/O without changing model inputs.
- The first late-fusion derivation assigned merged probabilities without explicit `row_key` reindexing. A direct value-equality check detected the mismatch before final reporting. Invalid late outputs were moved to `failed_attempts/late_alignment_bug_20260713/`, keyed alignment and a regression test were added, and all late outputs/metrics were regenerated.
- Co-attention folds 2-5 record a dirty worktree because the fold-1 smoke audit updated tracked lightweight report files after the training commit. Their executable code and configuration remained exactly at commit `0e736d48`; no source/config changes occurred between folds.

## Final patient-level results

| Model | AUPRC | ROC AUC | Brier | Sensitivity | Specificity | TP | FP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Late mean | 0.630 | 0.774 | 0.184 | 0.58 | 0.80 | 29 | 20 |
| Early fusion | 0.590 | 0.738 | 0.213 | 0.58 | 0.85 | 29 | 15 |
| Intermediate fusion | 0.567 | 0.741 | 0.224 | 0.48 | 0.84 | 24 | 16 |
| Image-only | 0.557 | 0.731 | 0.245 | 0.60 | 0.72 | 30 | 28 |
| Co-attention | 0.548 | 0.739 | 0.230 | 0.52 | 0.80 | 26 | 20 |
| CNV-only | 0.538 | 0.663 | 0.216 | 0.28 | 0.90 | 14 | 10 |
| Late stack-logit | 0.530 | 0.737 | 0.202 | 0.60 | 0.75 | 30 | 25 |

Clinical sensitivity/specificity/counts use fold-specific validation-derived thresholds. Threshold 0.5 is reported separately.

Paired late mean minus CNV-only:

- AUPRC +0.091 (95% paired bootstrap CI -0.036 to 0.219).
- ROC AUC +0.111 (95% CI 0.002 to 0.219).
- Brier -0.032 (95% CI -0.062 to -0.004; lower is better).

Early fusion minus CNV-only AUPRC was +0.051 (95% CI -0.053 to 0.167). Intermediate fusion minus CNV-only AUPRC was +0.029 (95% CI -0.084 to 0.157).

Supplementary post-hoc co-attention minus CNV-only AUPRC was +0.010 (95% CI -0.103 to 0.136). Against image-only, its AUPRC difference was -0.009 (95% CI -0.131 to 0.099). Co-attention therefore did not improve the primary metric over the simpler fusion models.

## Scientific conclusion

Adding histopathology improved multimodal point estimates over CNV-only, with late mean strongest. Paired AUC and Brier intervals favor late mean, but the prespecified primary AUPRC interval includes zero. Supplementary co-attention did not outperform late mean, early fusion, or intermediate fusion by AUPRC. The defensible conclusion is a likely multimodal benefit that is not statistically conclusive on the primary metric in this internal cohort. The endpoint is future next-biopsy LGD2+ neoplastic progression, not OAC-only cancer progression.

Eight final interpretation cases were reselected from the strict OOF predictions. Final-checkpoint attention and CNV region/gene regeneration remains a subsequent interpretation task, not a missing model-comparison result.

## Exact next command

Regenerate final-model interpretation only for the new OOF-selected cases listed in `reports/thesis_ch1/lgd2_final_pre_event_interpretation_cases.csv`. Start by validating recorded feature/checkpoint references; do not reuse developmental case labels automatically.

The completed result tables can be reproduced with:

```bash
/home/zuberi01/miniforge3/envs/erin/bin/python scripts/27_collect_lgd2_final_oof.py \
  --release-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1

/home/zuberi01/miniforge3/envs/erin/bin/python scripts/28_make_lgd2_final_pre_event_results.py \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1 \
  --bootstrap 5000
```
