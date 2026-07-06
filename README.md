# Multimodal Barrett's Progression

## Missing / Not Yet Done

- No raw data, derived cohort tables, slide files, CNV matrices, embeddings, checkpoints, prediction CSVs, or result folders are stored in this repository.
- The primary endpoint is now locked as `NextBiopsyProgression_LGD2plus`: HGD/IMC/OAC or two consecutive LGD biopsies.
- The primary evaluation is now locked as 5-fold patient-disjoint CV, not LOPO.
- Existing LGD2+ 5-fold patient-level results are present, but the final clinical table is incomplete: patient-level AUPRC, Brier/calibration, fixed-sensitivity/specificity operating points, and full confusion matrices still need recomputation from saved predictions.
- A clean early-prediction-only supplementary analysis excluding `DaysFromCurrentToEvent == 0` has not yet been generated as a final result.
- LGD2+ biological interpretation outputs were not found in the audited experiment folder.
- A clean tile/magnification comparison table for the final LGD2+ endpoint was not found.
- This branch is a reset from the previous demo-oriented repository contents; it starts from the local experiment audits and defines the next reproducible project direction.

## Current Focus

This project is being rebuilt around a single thesis question:

> Can multimodal histopathology plus CNV improve prediction of future Barrett's oesophagus progression, evaluated at patient level without patient leakage?

The immediate working plan is:

1. Use `NextBiopsyProgression_LGD2plus` as the primary endpoint.
2. Use 5-fold patient-disjoint CV as the primary evaluation.
3. Use patient-level results as primary; biopsy/sample-level results are supplementary.
4. Keep LGD3+ as supplementary / legacy / interpretability-supporting.
5. Recompute the missing patient-level clinical metrics from saved LGD2+ prediction files.
6. Decide whether early-prediction-only analysis is supplementary or required for the main table.
7. Add LGD2+ biological interpretation outputs for histology, CNV, and multimodal disagreement/rescue cases.

## Repository Scope

This repository should contain:

- project direction and decisions;
- audit-derived evidence summaries;
- data contracts and cohort definitions;
- reproducible scripts that operate on external data paths;
- small configuration files;
- documentation for how to regenerate results.

This repository should not contain:

- raw histology slides;
- CNV profiles or matrices;
- patient-level raw clinical metadata;
- derived master CSVs;
- fold assignment CSVs;
- prediction CSVs;
- model checkpoints;
- generated figures from private cases;
- large logs or Slurm outputs.

See `docs/no_data_policy.md` for the guardrails.

## Audited Starting Point

The local experiment folder audit identified this primary LGD2+ master table, stored outside Git:

`data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`

Key audited facts:

- 959 slide/sample rows.
- 160 patients.
- 470 biopsy IDs.
- `NextBiopsyProgression_LGD2plus`: 231 positive rows, 690 negative rows, 38 missing labels.
- Patient-level LGD2+ labels: 55 positive patients, 100 negative patients among 155 labelled patients.
- Patient-disjoint CV split code was found.
- Primary LGD2+ logic is HGD/IMC/OAC or two consecutive LGD biopsies.
- At-event rows where `DaysFromCurrentToEvent == 0` are present and must be handled explicitly.
- Existing result families are mixed, but the primary candidate is the LGD2+ 5-fold campaign under `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`.

The two source audit reports are in `docs/audits/`.
The current completion audit is in `docs/lgd2_completion_audit.md`.

## What To Run Next

After cloning this branch on the cluster, set external paths in your shell or job config:

```bash
export BARRETTS_EXPERIMENT_ROOT=/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
export BARRETTS_MASTER_CSV="$BARRETTS_EXPERIMENT_ROOT/data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv"
```

Then follow:

- `docs/data_contract.md` for required table columns.
- `docs/experiment_plan.md` for the minimum final result set.
- `scripts/assert_no_data_tracked.sh` before any commit.

## Current Status

This repository is documentation-first. Endpoint and primary evaluation are now locked; the remaining work is final metric recomputation, early-prediction sensitivity analysis, and LGD2+ interpretation packaging.
