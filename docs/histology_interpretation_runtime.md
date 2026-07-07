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

## Candidate Environment Discovery

The candidate sweep tested local project/user Python executables and found:

- selected: `/home/zuberi01/miniforge3/envs/pathology/bin/python`
- pass: `/home/zuberi01/miniforge3/envs/pathology/bin/python`
- pass: `/home/zuberi01/miniforge3/envs/virchow2/bin/python`
- pass: `/home/zuberi01/miniforge3/envs/erin/bin/python`
- fail: `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python` because it lacks `torch`, `PIL`, and `openslide`
- fail/timeout: external `.conda_mil/bin/python` and `.conda_mil/bin/python3`

Use the selected environment for the current dry run:

```bash
/home/zuberi01/miniforge3/envs/pathology/bin/python \
  scripts/11_validate_histology_runtime_env.py
```

Do not use `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python` for WSI
interpretation; it lacks required runtime dependencies.

## Minimal Dry-Run Rule

After both preflights pass, run only `row_idx 0` first. Do not attempt
`B_false_negative_07` or all 8 interpretation cases until row 0 succeeds and the
lightweight summary confirms expected external outputs.

Current row 0 status: `A_true_positive_early_02` / `abmil` succeeded with the
`pathology` environment and wrote heavy outputs externally.
