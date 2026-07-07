# LGD2+ Histology Dry-Run Execution Log

Date: 2026-07-07

## Environment

- Clean Git repo: `multimodal-barretts-progression`
- External execution root: `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`
- Python attempted: `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python`
- Legacy runner: `scripts/run_wsi_explainability_case.py`

## Path Remapping

Preflight was rerun immediately before the dry-run attempt:

```bash
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/10_validate_lgd2_histology_paths.py
```

Result:

- Dry-run cases checked: `2`
- Fully resolvable after remapping: `2`
- Missing required paths: none

External files created outside Git:

- `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv`
- `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/index/uni2_index_remapped_dry_run.csv`
- `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/preflight_resolved_inputs.csv`

## Cases Attempted

| case_id | model | row_idx | attempted | success | notes |
| --- | --- | --- | --- | --- | --- |
| `A_true_positive_early_02` | `abmil` | 0 | yes | no | failed at `import torch` before loading WSI/features/checkpoint |
| `A_true_positive_early_02` | `early_mean_mlp` | 1 | no | no | skipped because row 0 failed |
| `B_false_negative_07` | `abmil` | 2 | no | no | skipped because first case failed |
| `B_false_negative_07` | `early_mean_mlp` | 3 | no | no | skipped because first case failed |

## Command Run

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

Failure summary:

```text
ModuleNotFoundError: No module named 'torch'
```

## Runtime Preflight

Runtime preflight was added after the failed dry run:

```bash
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/11_validate_histology_runtime_env.py
```

Result:

- pass: `False`
- Python executable: `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python`
- Python version: `3.12.13`
- missing imports: `torch`, `PIL`, `openslide`

Latest blocker is runtime dependency resolution, not path resolution. No data/model
execution occurred before the import failure.

## Outputs

No WSI-derived heavy outputs were generated. The expected external output directory
`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/` was not
created by the failed command.

Expected heavy outputs, if a correct environment is used later, must stay external:

- heatmap PNGs;
- top/bottom tile-grid PNGs;
- `tile_scores.csv`;
- `metadata.json`;
- cache files under `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache/`.

Lightweight summaries updated in Git:

- `lgd2_histology_dry_run_summary.csv`
- `lgd2_histology_dry_run_summary.md`
- `lgd2_histology_dry_run_warnings.md`

## Recommendation

Do not run all 8 cases yet. First identify a Python environment for the legacy WSI
runner with `torch`, `openslide`, `pandas`, `numpy`, and `PIL` importing quickly. Run
`scripts/11_validate_histology_runtime_env.py` in that environment, then rerun only
`row_idx 0` using the remapped external manifest.

## Candidate Environment Discovery

Candidate runtime environments were tested with `scripts/11_validate_histology_runtime_env.py`.

Selected environment:

`/home/zuberi01/miniforge3/envs/pathology/bin/python`

Reason:

- imports `torch`, `numpy`, `pandas`, `PIL`, and `openslide`;
- most pathology/WSI-aligned passing environment name;
- external `.conda_mil` Python timed out during runtime preflight.

## Successful Row 0 Rerun

After path and runtime preflights passed, row 0 was rerun only:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/pathology/bin/python scripts/run_wsi_explainability_case.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv \
  --row_idx 0 \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache \
  --top_tiles 25 \
  --tissue_only \
  --skip_if_exists
```

Result:

- case/model: `A_true_positive_early_02` / `abmil`
- success: `yes`
- second case attempted: `no`

External output directory:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/A_true_positive_early/PR1_BED_060__SLX-12455.D701_D504__fold2`

External files generated and kept out of Git:

- `top_tiles_grid.png`
- `bottom_tiles_grid.png`
- `heatmap_overlay.png`
- `heatmap_overlay_shuffle.png`
- `tile_scores.csv`
- `metadata.json`

Next recommendation: inspect row 0 outputs first. If they are acceptable, run only the
next planned row/case on request; do not automatically run all 8.

## Row 0 Output Validation

Row 0 output audit:

- case/model: `A_true_positive_early_02` / `abmil`
- structurally valid: `True`
- metadata JSON parsed: `True`
- tile-score CSV parsed: `True`
- tiles scored: `256`
- top patch grid, bottom patch grid, heatmap overlay, and shuffled heatmap overlay all exist and are non-empty.

## Row 1 Dry Run

After row 0 passed structural validation, only the second dry-run case was run:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/pathology/bin/python scripts/run_wsi_explainability_case.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv \
  --row_idx 2 \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/cache \
  --top_tiles 25 \
  --tissue_only \
  --skip_if_exists
```

Result:

- case/model: `B_false_negative_07` / `abmil`
- success: `yes`
- all 8 cases run: `no`

External row 1 output directory:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/B_false_negative/AHM1146__SLX-13692.D703_D508__fold3`

External files generated and kept out of Git:

- `top_tiles_grid.png`
- `bottom_tiles_grid.png`
- `heatmap_overlay.png`
- `heatmap_overlay_shuffle.png`
- `tile_scores.csv`
- `metadata.json`

## Row 1 Output Validation

- structurally valid: `True`
- metadata JSON parsed: `True`
- tile-score CSV parsed: `True`
- tiles scored: `256`
- top patch grid, bottom patch grid, heatmap overlay, and shuffled heatmap overlay all exist and are non-empty.

Next recommendation: manually inspect both external visual outputs. If they look
correct, run the remaining 6 selected cases with the same environment and output root.
