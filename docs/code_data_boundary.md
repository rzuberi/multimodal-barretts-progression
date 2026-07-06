# Code/Data Boundary

This repository is the clean Chapter 1 code and documentation layer. It does not own the raw Barrett data or full experiment outputs.

## In Git

- Reusable evaluation code under `src/barrett/`.
- CLI scripts under `scripts/`.
- Small configs under `configs/`.
- Audit and manifest documentation under `docs/`.
- Lightweight thesis summary reports under `reports/thesis_ch1/`.

## External Only

- Raw WSIs and tile images.
- CNV profiles, matrices, and feature arrays.
- Derived master cohort CSVs.
- Full prediction files and result folders.
- Model checkpoints.
- Private clinical metadata.

External paths are referenced through `docs/final_results_manifest.csv`. Scripts should resolve these paths under `BARRETTS_EXPERIMENT_ROOT` or an explicit `--experiment-root` argument.

## Metric Recompute

Run:

```bash
export BARRETTS_EXPERIMENT_ROOT=/path/to/barretts_training
python scripts/02_recompute_patient_detection_metrics.py
```

The script reads external prediction files and the external LGD2+ master cohort, joins by validated sample keys, computes patient/biopsy/sample metrics, and writes small summary reports to `reports/thesis_ch1/`.

## Safety Check

Before committing:

```bash
./scripts/assert_no_data_tracked.sh
```

The guard blocks common raw data, image, checkpoint, feature, and large result extensions. Only explicitly allowlisted lightweight manifest/report CSVs are permitted.

