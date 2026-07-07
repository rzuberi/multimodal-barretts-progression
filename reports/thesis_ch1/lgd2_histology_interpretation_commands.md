# LGD2+ Histology Interpretation Command Plan

External output target:

`analysis/lgd2_interpretation_regeneration_20260707/histology/`

Do not write WSI-derived images, tile crops, feature caches, checkpoints, or raw attention arrays into Git.

## Clean-Repo Lightweight Manifest

Already safe to run from the clean Git repo:

```bash
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python \
  scripts/08_build_lgd2_wsi_case_manifest.py \
  --external-root .. \
  --external-output-root analysis/lgd2_interpretation_regeneration_20260707/histology
```

Outputs committed as lightweight summaries:

- `reports/thesis_ch1/lgd2_wsi_case_manifest.csv`
- `reports/thesis_ch1/lgd2_wsi_case_manifest.md`
- `reports/thesis_ch1/lgd2_wsi_case_manifest_warnings.md`

## `build_wsi_case_manifest.py`

Appears to build a legacy WSI explainability manifest from campaign summaries, prediction files, metrics JSON, checkpoints, and feature indexes.

Reuse status: **manual review** for LGD2+. The default is LGD3+ and it selects top TP/FP/FN/TN cases automatically, not the fixed 8 thesis cases.

Arguments that must change:

- `--summary_csv` to LGD2+ UNI2 campaign summary.
- `--campaign_root` to LGD2+ UNI2 campaign root.
- `--derived_master` to LGD2+ master cohort.
- `--task` to `NextBiopsyProgression_LGD2plus`.
- `--conditions` to `all_samples`.
- model selection must be constrained to `abmil` and `early_mean_mlp`, or post-filtered to the fixed 8 cases.

Command template:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/build_wsi_case_manifest.py \
  --repo_root . \
  --summary_csv data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/global_results_summary.csv \
  --campaign_root data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2 \
  --derived_master data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv \
  --task NextBiopsyProgression_LGD2plus \
  --conditions all_samples \
  --baseline_image_models abmil \
  --top_mm 1 \
  --top_img_per_encoder 1 \
  --top_k 0
```

Warning: this template may not produce exactly the fixed 8 selected cases. Prefer building a full-path external manifest from `reports/thesis_ch1/lgd2_wsi_case_manifest.csv` plus the external lookup tables, then run the case renderer on that manifest.

## `run_wsi_explainability_case.py`

Appears to render one WSI explainability case. It loads feature NPZs/checkpoints, opens slides with OpenSlide, computes tile scores, writes heatmap PNGs, top/bottom tile grids, `tile_scores.csv`, and `metadata.json`.

Reuse status: **not safe to run in Git**. Safe only when `--out_root` and `--cache_root` point to external folders.

Required external manifest columns include:

- `sample_id`
- `patient_id`
- `wsi_path`
- `checkpoint_path`
- `index_csv`
- `metrics_json`
- `dataset_master_expected`
- `task`
- `condition`
- `fold`
- `model`
- `encoder`
- `modality`

Command template for one row:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/run_wsi_explainability_case.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/wsi_case_manifest_fullpaths.csv \
  --row_idx <ROW_INDEX> \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/cache \
  --top_tiles 25 \
  --tissue_only \
  --skip_if_exists
```

Outputs too heavy for Git:

- heatmap overlay PNGs
- top/bottom tile-grid PNGs
- tile crops
- cached feature/CNV arrays
- checkpoint-derived files

Lightweight outputs that can be summarized in Git:

- per-case `metadata.json` fields, if converted to a small CSV/MD summary
- `tile_scores.csv` top rows, if reduced to top patch references and attention-spread statistics

## `launch_wsi_explainability_array.py`

Appears to launch `run_wsi_explainability_case.py` over a manifest locally or via Slurm.

Reuse status: **manual review**. Use only after a full-path external LGD2+ manifest exists.

Command template:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/launch_wsi_explainability_array.py \
  --manifest_csv analysis/lgd2_interpretation_regeneration_20260707/histology/wsi_case_manifest_fullpaths.csv \
  --out_root analysis/lgd2_interpretation_regeneration_20260707/histology/wsi \
  --cache_root analysis/lgd2_interpretation_regeneration_20260707/histology/cache \
  --max_rows 16 \
  --partition epyc \
  --cpus 4 \
  --mem 24G \
  --time 03:00:00 \
  --skip_if_exists
```

## `plot_attention_spread_curves.py`

Appears to summarize existing `tile_scores.csv` outputs into attention-spread curves and tables.

Reuse status: **ready only after tile scores exist**.

Command template:

```bash
cd /mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python scripts/plot_attention_spread_curves.py \
  --batch_roots analysis/lgd2_interpretation_regeneration_20260707/histology
```

## Clean-Repo Summary Loader

Run after external WSI outputs exist, or now in missing-output mode:

```bash
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python \
  scripts/09_summarise_lgd2_histology_interpretation.py \
  --external-output-dir analysis/lgd2_interpretation_regeneration_20260707/histology
```

Current status: missing-output mode only. No WSI explainability command was run.
