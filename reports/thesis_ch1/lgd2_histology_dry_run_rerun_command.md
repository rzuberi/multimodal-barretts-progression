# LGD2+ Histology Dry-Run Rerun Command

Do not run this until both path and runtime preflights pass.

## 1. Validate Paths

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression
<candidate-python> scripts/10_validate_lgd2_histology_paths.py \
  --dry-run-only
```

Expected before proceeding:

- dry-run cases checked: `2`
- fully resolvable: `2`
- missing required paths: none

## 2. Validate Runtime

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression
<candidate-python> scripts/11_validate_histology_runtime_env.py
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
<candidate-python> scripts/run_wsi_explainability_case.py \
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

Do not attempt `B_false_negative_07` or all 8 cases until row 0 succeeds and the
lightweight summary confirms top patches, tile scores, and heatmap/overlay outputs
were generated externally.
