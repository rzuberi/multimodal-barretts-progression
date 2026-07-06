# Multimodal Barrett's Progression

## Missing / Not Yet Done

- No raw data, derived cohort tables, slide files, CNV matrices, embeddings, checkpoints, prediction CSVs, or result folders are stored in this repository.
- Full leave-one-patient-out (LOPO) results for the canonical multimodal cohort are missing.
- The final primary endpoint is not yet locked: LGD2+ versus LGD3+ future progression remains an explicit decision.
- A clean early-prediction-only cohort excluding `DaysFromCurrentToEvent == 0` has not yet been generated as a final dataset.
- Patient-level clinical detection metrics need recomputation for the final endpoint: PPV, NPV, confusion matrices, detected/missed progressors, and false positives per detected progressor.
- LGD2+ biological interpretation outputs were not found in the audited experiment folder.
- This branch is a reset from the previous demo-oriented repository contents; it starts from the local experiment audits and defines the next reproducible project direction.

## Current Focus

This project is being rebuilt around a single thesis question:

> Can multimodal histopathology plus CNV improve prediction of future Barrett's oesophagus progression, evaluated at patient level without patient leakage?

The immediate working plan is:

1. Choose the final endpoint: LGD2+ or LGD3+ future progression.
2. Define a final early-prediction cohort that excludes current/at-event samples.
3. Regenerate or select a master cohort table outside Git.
4. Run patient-level LOPO or justify patient-disjoint 5-fold CV if LOPO is not feasible.
5. Report clinically interpretable patient-level detection metrics, not only AUC.
6. Add biological interpretation outputs for histology, CNV, and multimodal disagreement/rescue cases.

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

The local experiment folder audit identified this likely canonical master table, stored outside Git:

`data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`

Key audited facts:

- 959 slide/sample rows.
- 160 patients.
- 470 biopsy IDs.
- 941 unique CNV paths.
- Patient-disjoint CV split code was found.
- Canonical LGD3+ logic uses HGD/IMC/OAC plus an LGD streak rule.
- At-event rows where `DaysFromCurrentToEvent == 0` are present and must be handled explicitly.
- Existing result families are mixed: older 50-fold, newer canonical 5-fold, Killcoyne/CNV LOPO-style outputs.

The two source audit reports are in `docs/audits/`.

## What To Run Next

After cloning this branch on the cluster, set external paths in your shell or job config:

```bash
export BARRETTS_EXPERIMENT_ROOT=/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
export BARRETTS_MASTER_CSV="$BARRETTS_EXPERIMENT_ROOT/data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv"
```

Then follow:

- `docs/data_contract.md` for required table columns.
- `docs/experiment_plan.md` for the minimum final result set.
- `scripts/assert_no_data_tracked.sh` before any commit.

## Current Status

This repository is documentation-first. It is intentionally small until the endpoint, cohort filter, and evaluation protocol are finalized.
