# Histology Interpretation Runtime

This repo does not contain WSIs, tile images, feature tensors, checkpoints, or large
interpretability outputs. Histology interpretation must run from the external Barrett
training folder and write heavy outputs only under:

`analysis/lgd2_interpretation_regeneration_20260707/histology/`

## Required Runtime Packages

The legacy WSI runner `run_wsi_explainability_case.py` requires these imports:

- `torch`
- `numpy`
- `pandas`
- `PIL`
- `openslide`

The previous dry-run failed before any WSI/model/data access with:

`ModuleNotFoundError: No module named 'torch'`

## Required Checks Before Running

Run path preflight first:

```bash
/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python \
  scripts/10_validate_lgd2_histology_paths.py
```

Then run runtime preflight:

```bash
<candidate-python> scripts/11_validate_histology_runtime_env.py
```

Both preflights must pass before running `run_wsi_explainability_case.py`.

## Environment Notes

Do not use default `python3` blindly. In this shared environment it may resolve to an
old system Python, including Python 3.6.

Known candidates to check, not guaranteed:

- `.conda_mil/bin/python` from the external training folder;
- a project conda env with `torch` and `openslide`;
- an HPC/module env that can import `torch`, `openslide`, `pandas`, `numpy`, and `PIL`.

Do not install packages from this repo automation unless explicitly asked.

## Minimal Dry-Run Rule

After both preflights pass, run only `row_idx 0` first. Do not attempt
`B_false_negative_07` or all 8 interpretation cases until row 0 succeeds and the
lightweight summary confirms expected external outputs.
