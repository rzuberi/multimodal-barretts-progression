# Multitask + Mixture-of-Experts campaign

Isolated rebuild of the March multi-task + MoE work on top of the frozen
Chapter-1 harness. Nothing here modifies `src/` or the frozen results; all new
code imports the `barrett` package as a library. Lives on branch `multitask-moe`.

## Tasks (core 3)
- `ever_progress` — `Progressor_label`
- `at_risk_3y` — `AtRisk_3y` (censored to ≥3y follow-up or event)
- `next_biopsy_progression` — `NextBiopsyProgression_LGD2plus` (reuses frozen 707/150 cohort)

## Model set per task (no gaps), backbones = {uni2, gigapath}
`cnv_only` (backbone-independent) · `image_only` · `early_fusion` ·
`intermediate_fusion` · `coattention_fusion` · **`moe`** (end-to-end) ·
derived `late_mean` / `late_stack_logit`.

## Layout
- `src/moe.py`, `src/moe_training.py` — end-to-end MixtureOfExperts + nested-CV-safe trainer.
- `scripts/train_outer_fold.py` — one (task, backbone, family, fold); copy of frozen script 24 + moe.
- `scripts/submit_campaign.py` — duplicate-per-node self-dedup sbatch orchestrator (dry-run by default).
- `slurm/run_unit.sh` — per-unit wrapper: atomic claim, self-cancel if already running/done, retry on failure.
- `configs/tasks.yaml`, `configs/models_{uni2,gigapath}.yaml`.
- Data/checkpoints/OOF go OUTSIDE git to
  `analysis/multitask_moe_20260721/<task>/{release,train/<backbone>}` (no-data policy).

## Run
```
# dry run (default) — prints the plan
python multitask_moe/scripts/submit_campaign.py
# submit everything (one copy per node; duplicates self-cancel)
python multitask_moe/scripts/submit_campaign.py --submit
# resume: re-run the same command; done/queued units are skipped
```
GPU lane → h200 + cuda (all nodes); CPU lane (cnv) → epyc (capped to 8 nodes).
