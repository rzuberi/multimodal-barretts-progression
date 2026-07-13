# Multimodal Barrett's Progression

## Missing / Not Yet Done

- External cohort validation is missing; current evidence is internal five-fold patient-disjoint nested CV.
- Final-model LGD2+ CNV gene/window interpretation and final-model histology/co-attention regeneration are still needed. Existing eight-case histology figures came from the developmental models.
- Eight interpretation cases have been reselected from strict pre-event OOF predictions; their final-checkpoint outputs still need regeneration before thesis figures are frozen.
- A clean final tile/magnification sensitivity table remains missing.
- The primary paired AUPRC improvement for the best multimodal model is not conclusive: its 95% interval includes zero.
- The endpoint is next-biopsy LGD2+ neoplastic progression, not OAC-only cancer progression.
- No raw data, cohort tables, WSIs, feature tensors, checkpoints, OOF prediction dumps, or full result folders are stored in this repository.

## Final Candidate Result

The strict pre-event rerun is complete on 707 matched rows and 150 patients using identical folds for CNV-only, UNI2 ABMIL, early fusion, intermediate fusion, late mean, and late stack-logit. Co-attention was subsequently retrained under the same contract as a supplementary post-hoc architecture comparison.

- Best AUPRC: late mean `0.630`; CNV-only `0.538`.
- Best AUC: late mean `0.774`; CNV-only `0.663`.
- Late mean minus CNV AUPRC: `+0.091` (95% paired bootstrap CI `-0.036` to `0.219`).
- Late mean minus CNV AUC: `+0.111` (95% CI `0.002` to `0.219`).
- Late mean minus CNV Brier: `-0.032` (95% CI `-0.062` to `-0.004`; lower is better).
- Co-attention AUPRC: `0.548`; its paired difference from CNV was `+0.010` (95% CI `-0.103` to `0.136`).

Thus histopathology adds useful signal in point estimates and secondary metrics, but the prespecified primary AUPRC comparison remains uncertain.

## Supplementary Advanced Architectures

Seven post-hoc architectures were implemented and run under the same strict pre-event cohort and patient-disjoint nested-CV contract: reliability-gated residual fusion, hierarchical patient fusion, chromosome-token cross-attention, low-rank bilinear fusion, multitask temporal fusion, optimal-transport fusion, and a GigaPath/UNI2/Virchow2 foundation ensemble.

- Foundation ensemble had the highest AUPRC: `0.636` versus late mean `0.630`; paired difference `+0.006` (95% CI `-0.098` to `0.096`).
- Hierarchical patient fusion had AUPRC `0.631`, the highest AUC (`0.798`), and the lowest Brier score (`0.180`).
- Hierarchical minus late mean AUPRC was `+0.001` (95% CI `-0.108` to `0.132`).
- The other advanced architectures did not improve AUPRC over late mean.

These are supplementary post-hoc architecture comparisons. They do not replace late mean as the locked headline model or make the primary improvement statistically conclusive. See `reports/thesis_ch1/lgd2_advanced_fusion_execution_report.md`.

## Current Focus

This project is being rebuilt around a single thesis question:

> Can multimodal histopathology plus CNV improve prediction of future Barrett's oesophagus progression, evaluated at patient level without patient leakage?

The immediate working plan is:

1. Use `NextBiopsyProgression_LGD2plus` as the primary endpoint.
2. Use 5-fold patient-disjoint CV as the primary evaluation.
3. Use patient-level results as primary; biopsy/sample-level results are supplementary.
4. Keep LGD3+ as supplementary / legacy / interpretability-supporting.
5. Use the new strict pre-event nested-CV outputs as final candidates; retain older campaign results as developmental.
6. Use cross-fitted inner-validation thresholds for primary clinical detection metrics; report threshold 0.5 as reference.
7. Regenerate biological interpretation from the final checkpoints and reselect cases from final OOF predictions.

## Repository Scope

This repository should contain:

- project direction and decisions;
- audit-derived evidence summaries;
- data contracts and cohort definitions;
- reproducible scripts that operate on external data paths;
- small configuration files;
- reusable evaluation modules under `src/barrett/`;
- documentation for how to regenerate results.

This repository should not contain:

- raw histology slides;
- CNV profiles or matrices;
- patient-level raw clinical metadata;
- derived master CSVs;
- fold assignment CSVs;
- raw prediction CSVs;
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

## Reproduce Final Tables

After cloning this branch on the cluster, set external paths in your shell or job config:

```bash
export BARRETTS_EXPERIMENT_ROOT=/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
export BARRETTS_MASTER_CSV="$BARRETTS_EXPERIMENT_ROOT/data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv"
```

The frozen external release is:

```text
analysis/chapter1_lgd2_final_pre_event_20260713_final/
```

Validate and collect complete OOF outputs, then regenerate the lightweight final tables:

```bash
/home/zuberi01/miniforge3/envs/erin/bin/python scripts/27_collect_lgd2_final_oof.py \
  --release-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1

/home/zuberi01/miniforge3/envs/erin/bin/python scripts/28_make_lgd2_final_pre_event_results.py \
  --output-root ../analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1
```

Then follow:

- `docs/data_contract.md` for required table columns.
- `docs/experiment_plan.md` for the minimum final result set.
- `docs/code_data_boundary.md` for what belongs in Git versus external storage.
- `scripts/assert_no_data_tracked.sh` before any commit.

## Current Status

This repository now contains the frozen model registry, migrated model definitions, patient-disjoint nested-CV runner, late-fusion derivation, output contracts, final patient-level tables, and lightweight provenance reports. Heavy data and model artifacts remain external.
