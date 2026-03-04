# Barrett's Retraining Experiments Showcase

Public, aggregate-only snapshot of our Barrett's histopathology + CNV experiment program.
No patient-level data, no slide-level embeddings, and no identifiable records are included in this repository.

## Snapshot

- Snapshot time (UTC): `2026-03-04T20:14:40Z`
- Stable summarized campaign: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_completion_20260304_155636`
- Full-coverage campaign (in progress): `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943`
- Stable rows: `315` (`304` complete, `11` incomplete)
- Full-coverage runlist rows: `864`
- Full-coverage trainable rows: `402`
- Full-coverage derived latefusion rows: `462`
- Full-coverage blocked rows: `0`

## Cohort & Labeling Policy

- Cohort details are reported only as aggregate experiment counts and fold-level totals.
- Canonical progression definition uses `LGD3plus`: the 3rd consecutive LGD counts as progression.
- Progression-derived tasks are trained/evaluated under that canonical definition.
- Legacy non-LGD3plus progression labeling is excluded from this showcase.

## Experiment Universe

- Modalities: `image`, `cnv`, `multimodal`
- Encoders discovered: `virchow2`, `uni2`, `gigapath`, `cnv_anchor`
- Conditions: `all_samples`, `exclude_hgd_imc`, `exclude_lgd_hgd_imc`
- CV policy: `rep=1`, `folds=1..5`

Tasks discovered (from audit):
- AtRisk_1y | no
- AtRisk_2y | no
- AtRisk_3y | no
- AtRisk_4y | no
- AtRisk_5y | no
- CurrentGradeInt | no
- DaysSincePreviousBiopsy | no
- DaysToNextBiopsy | no
- HasNextBiopsy | no
- IsFirstBiopsy | no
- IsLastBiopsy | no
- NextBiopsyExistsInDataset | no
- NextBiopsyLabel | no
- NextBiopsyProgression | no
- NextBiopsyProgression_LGD3plus | yes
- NextBiopsyTier3 | no
- Progress_in_1 | no
- Progress_in_2 | no
- Progress_in_3 | no
- Progress_in_4 | no
- Progress_in_5 | no
- Progressor_label | no
- Time_to_progression | no

Note: `NextBiopsyProgression` appears in historical audit exports but is treated as deprecated/stale; canonical progression reporting is `NextBiopsyProgression_LGD3plus`.

## Current Queue Status (Full-Coverage Campaign)

- Job states: `{'PENDING': 117, 'RUNNING': 32}`
- Partition distribution: `{'epyc': 95, 'cuda': 54}`
- ROCm compatibility flag in plan: `True`

## Files in This Showcase

- `data_snapshots/coverage_status.csv`: high-level coverage and campaign counters
- `data_snapshots/model_leaderboard_binary_auc.csv`: top binary rows by AUC
- `data_snapshots/task_leaders.csv`: best complete row per task (task-type appropriate metric)
- `data_snapshots/fullcoverage_queue_snapshot.csv`: live queue snapshot for the active full-coverage campaign
- `data_snapshots/models_discovered.txt`: discovered model IDs in the experiment universe
- `data_snapshots/encoders_discovered.txt`: discovered encoders/foundation lanes
- `data_snapshots/tasks_discovered_from_audit.txt`: task list from the audit export

## Method Families Included

- Image MIL baselines and variants
- CNV-only models (binary, multiclass, regression)
- Multimodal early/intermediate/co-attention models
- Derived late-fusion models (`latefusion_*`) generated from fold predictions with leakage-safe stacking
- Routing / MoE ensembles over available experts with task-type-aware metrics

## Privacy Boundary

- Included: aggregate metrics, model names, task names, condition names, fold-completion counters, queue metadata.
- Excluded: patient/sample identifiers, raw features, tiles, embeddings, row-level predictions from patients.

## Reproducibility Pointers

- Full-coverage plan: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/admin/plan.json`
- Full-coverage submissions: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/admin/submissions.csv`
- Full-coverage job IDs: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/admin/job_ids.json`

Generated automatically from internal campaign outputs with PHI-safe filtering.
