# LGD2+ Histology Dry-Run Command Check

External dry-run directory: `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run`

## Selected Cases

| case_id | case_category | patient_id | sample_id | slide_id | slide_basename | fold | true_label | image_probability | fusion_probability | ABMIL checkpoint ref | early-fusion checkpoint ref | reason selected | external output ref | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | SLX-12455.D701_D504 | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | 2 | 1 | 0.9635841250419616 | 0.9931897521018982 | foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/image/all_samples/core_gpu/cv/all_samples_abmil_NextBiopsyProgression_LGD2plus_rep01_fold2_best.pt | foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/multimodal/all_samples/core_gpu/cv/all_samples_early_mean_mlp_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_rep01_fold2_best.pt | highest-confidence A true-positive with complete inputs | analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/A_true_positive_early_02/ |  |
| B_false_negative_07 | B_false_negative | AHM1146 | SLX-13692.D703_D508 | S09 26616 2 1 G3497.ndpi | S09 26616 2 1 G3497.ndpi | 3 | 1 | 0.1040728092193603 | 0.2848115861415863 | foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/image/all_samples/core_gpu/cv/all_samples_abmil_NextBiopsyProgression_LGD2plus_rep01_fold3_best.pt | foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/multimodal/all_samples/core_gpu/cv/all_samples_early_mean_mlp_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_rep01_fold3_best.pt | clear B false-negative/missed progressor with complete inputs | analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/B_false_negative_07/ |  |

## Input Checks

- A_true_positive_early_02 abmil: slide_exists=False, feature_index_exists=True, feature_npz_exists=False, checkpoint_exists=True, prediction_exists=True, metrics_json_exists=True
- A_true_positive_early_02 early_mean_mlp: slide_exists=False, feature_index_exists=True, feature_npz_exists=False, checkpoint_exists=True, prediction_exists=True, metrics_json_exists=True
- B_false_negative_07 abmil: slide_exists=False, feature_index_exists=True, feature_npz_exists=False, checkpoint_exists=True, prediction_exists=True, metrics_json_exists=True
- B_false_negative_07 early_mean_mlp: slide_exists=False, feature_index_exists=True, feature_npz_exists=False, checkpoint_exists=True, prediction_exists=True, metrics_json_exists=True

## Command Template

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths.csv \
  --row_idx <ROW_INDEX> \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache \
  --top_tiles 25 --tissue_only --skip_if_exists
```

## Resolved Commands

### row_idx 0: `A_true_positive_early_02` `abmil`

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths.csv --row_idx 0 --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache --top_tiles 25 --tissue_only --skip_if_exists
```

### row_idx 1: `A_true_positive_early_02` `early_mean_mlp`

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths.csv --row_idx 1 --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache --top_tiles 25 --tissue_only --skip_if_exists
```

### row_idx 2: `B_false_negative_07` `abmil`

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths.csv --row_idx 2 --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache --top_tiles 25 --tissue_only --skip_if_exists
```

### row_idx 3: `B_false_negative_07` `early_mean_mlp`

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths.csv --row_idx 3 --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache --top_tiles 25 --tissue_only --skip_if_exists
```

## Safety Assessment

- All required external inputs exist: `False`
- Output root is external under `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/`.
- Command is case-level via `--row_idx`; it does not launch full-cohort training.
- Expected heavy outputs stay external: heatmap PNGs, top/bottom tile grids, `tile_scores.csv`, metadata, and cache files.

- Command run status before execution: `skipped_missing_inputs`
- Command actually run: `no`
- Blocker: raw slide paths from `ImageAbsPath` are not visible in this shell (`/scratchc/.../*.ndpi` does not exist); selected UNI2 feature refs also require path remapping from legacy `/scratchc` to the visible slow-scratch tree before the legacy runner can load them.
- No heavy WSI/tile/heatmap outputs were generated.

## Path remapping / mount validation

This section supersedes the earlier direct-path-only input check above.

Path-remap audit:

- `reports/thesis_ch1/lgd2_histology_path_remap_audit.csv`
- `reports/thesis_ch1/lgd2_histology_path_remap_audit.md`
- `reports/thesis_ch1/lgd2_histology_path_remap_warnings.md`

Validation result:

- Cases checked: `2`
- Fully resolvable cases: `2`
- Dry-run can proceed in this shell after remapping: `True`
- Config source: `configs/path_remap.template.yaml (template fallback)`

Remap rules attempted:

- `/scratchc/fmlab/datasets/imaging/` -> `/mnt/scratchc/fmlab/datasets/imaging/`
- `/scratchc/fmlab/zuberi01/phd/barretts_retraining/` -> `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/`
- `/scratchc/fmlab/` -> `/mnt/scratche/slow/fmlab/`

Remaining missing required references:

- None in the path audit.

The histology dry run was still **not run** in this stage, by design. The next safe
action is a case-level external dry run for `row_idx 0` only, writing to:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/`

## Dry-run execution attempt 2026-07-07

The external full-path manifest was rebuilt with remapped paths:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv`

The remapped UNI2 feature index was written externally:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/index/uni2_index_remapped_dry_run.csv`

Attempted first command only:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv \
  --row_idx 0 \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache \
  --top_tiles 25 \
  --tissue_only \
  --skip_if_exists
```

Result:

- Case/model: `A_true_positive_early_02` / `abmil`
- Command run: `yes`
- Command success: `no`
- Failure point: Python import before WSI/feature/checkpoint loading
- Error summary: `ModuleNotFoundError: No module named 'torch'`
- Second case attempted: `no`

No WSI files were opened, no feature tensors were loaded, no checkpoints were loaded,
and no heatmaps/tile outputs were generated.
