# Final Analysis Training Completion Execution Report

## Outcome

`PARTIAL` while required fold-1 smoke runs and final five-fold jobs are executing.

## Repository state

- Starting commit: `5954b5789202025631367ba713f6164a00d907d7`.
- Branch: `main`.
- Final commit/push state: pending completion and review.
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
| `55144153` | Early fusion fold 1 | RUNNING/PENDING | pending | H200-compatible environment. |
| `55144154` | Intermediate fusion fold 1 | RUNNING/PENDING | pending | H200-compatible environment; both candidates selected on inner validation. |

Full folds 2-5 remain blocked until `scripts/29_audit_lgd2_final_smoke.py` reports 4/4 PASS.

## Fold completion matrix

| Family | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
|---|---|---|---|---|---|
| CNV-only | PASS smoke | not started | not started | not started | not started |
| Image-only | PASS smoke | not started | not started | not started | not started |
| Early fusion | running | not started | not started | not started | not started |
| Intermediate fusion | running | not started | not started | not started | not started |
| Late mean | pending base models | pending | pending | pending | pending |
| Late stack-logit | pending base models | pending | pending | pending | pending |

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
- Targeted and full toy suite: 137 tests passing in the `erin` environment.
- Migrated ABMIL, early-fusion, and intermediate-fusion modules produce identical outputs to legacy definitions after loading identical state dictionaries.
- Data guard: to be rerun after final report generation.

## Current scientific status

The strict rerun is not yet complete, so no new superiority claim is made. Developmental results remain suggestive only. The endpoint must be described as future next-biopsy LGD2+ neoplastic progression, not OAC-only cancer progression.

## Exact continuation commands

Audit the smoke gate:

```bash
/home/zuberi01/miniforge3/envs/erin/bin/python scripts/29_audit_lgd2_final_smoke.py \
  --release-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_smoke
```

After and only after 4/4 smoke PASS, generate the full launch manifest before submission:

```bash
/home/zuberi01/miniforge3/envs/erin/bin/python scripts/25_launch_lgd2_final_rerun.py \
  --release-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1 \
  --mode full
```
