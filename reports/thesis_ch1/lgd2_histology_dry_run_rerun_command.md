# LGD2+ Histology Dry-Run Rerun Command

Do not run this until both path and runtime preflights pass.

Selected Python executable:

`/home/zuberi01/miniforge3/envs/pathology/bin/python`

## 1. Validate Paths

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression
/home/zuberi01/miniforge3/envs/pathology/bin/python scripts/10_validate_lgd2_histology_paths.py \
  --dry-run-only
```

Expected before proceeding:

- dry-run cases checked: `2`
- fully resolvable: `2`
- missing required paths: none

## 2. Validate Runtime

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression
/home/zuberi01/miniforge3/envs/pathology/bin/python scripts/11_validate_histology_runtime_env.py
```

Expected before proceeding:

- `torch`: pass
- `numpy`: pass
- `pandas`: pass
- `PIL`: pass
- `openslide`: pass

## 3. Rerun Row 0 Only

Use the external Barrett training folder and the remapped manifest:

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

Row 0 is:

- case: `A_true_positive_early_02`
- model: `abmil`

Current status: row 0 has succeeded with the selected Python executable. Do not
attempt row 1 or `B_false_negative_07` until the row 0 outputs are inspected.

Do not attempt `B_false_negative_07` or all 8 cases until row 0 succeeds and the
lightweight summary confirms top patches, tile scores, and heatmap/overlay outputs
were generated externally.
