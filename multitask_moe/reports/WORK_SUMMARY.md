# Multitask + Mixture-of-Experts (`multitask_moe/`) — full work summary

**Scope.** This subfolder is a self-contained *update* to the Barrett's oesophagus →
oesophageal adenocarcinoma progression project. It lives on its own git branch
(`multitask-moe`) and folder (`multitask_moe/`), is entirely additive (it imports the
`barrett` package and edits nothing in `src/`), and **never touched the frozen Chapter-1
results**. This document covers everything done in the subfolder: the original build
(rebuilding the March-deck multitask + MoE experiments) and the subsequent update wave
(honesty corrections, two new endpoints, and a frozen-expert MoE comparison).

- **Branch / remote:** `multitask-moe` on `git@github.com:rzuberi/multimodal-barretts-progression.git`
- **Latest HEAD at time of writing:** `70b0a1e`
- **External output root (NOT in git — data / checkpoints / OOF / heatmaps):**
  `analysis/multitask_moe_20260721/` on the CRUK CI cluster
- **Protocol for every result below:** patient-level, nested 5-fold **patient-disjoint** CV,
  patient score = max over that patient's biopsies. This is the honest, stricter read; it
  runs lower than the March deck's biopsy-level scoring with per-model operating points.

---

## Part A — Original build (pre-update baseline)

The March 2026 Fitzgerald-group deck had shown four task framings, a Mixture-of-Experts
routing each biopsy to an image / CNV / multimodal expert, and whole-slide attention
heatmaps. The frozen production repo had dropped all of that (single endpoint, no MoE,
stale heatmaps). Part A rebuilt those experiments in isolation.

### What was built
- **MoE model + trainer** (`src/moe.py`, `src/moe_training.py`): three experts (image via
  gated-attention MIL mirroring `barrett.models.AttentionMIL`; CNV MLP; multimodal fusion),
  a softmax gate over the three, and a load-balancing auxiliary loss. Trained end-to-end.
  The trainer mirrors the frozen `fit_neural` exactly (validation-only early stopping on
  patient-max AUPRC, pos_weight BCE, train-split CNV normalisation) so the MoE is selected
  and calibrated under the identical nested-CV contract as the baselines. The MoE dataset
  reuses `family="intermediate_fusion"` so each batch carries both image bag + CNV vector
  without modifying shared `data.py`.
- **Per-task release builder** (`scripts/build_task_release.py`): re-labels the frozen
  707-row / 150-patient matched cohort per task and builds a stratified patient-disjoint
  5-fold split. Because all tasks reuse the frozen CNV / UNI2 / GigaPath feature views,
  the first three tasks are row-matched (clean paired comparison, no re-embedding).
- **Self-deduplicating sbatch campaign** (`scripts/submit_campaign.py`, `slurm/run_unit.sh`):
  submits one copy of each work-unit `(task, backbone, family, fold)` to every healthy node
  in its lane; each copy atomically claims the unit (`mkdir` on shared Lustre), the winner
  cancels its pending siblings, and completion markers make re-runs a free resume. GPU lane
  = h200 (`--qos h200_preempt`) + cuda; CPU lane = epyc for the backbone-independent
  `cnv_only`. The original 165-unit campaign ran ~1,300 job copies with 0 submit errors,
  each unit executing exactly once, in ~37 min.
- **Collection + results** (`scripts/collect_and_report.py`, `scripts/make_results.py`):
  collects per-family OOF, derives late-fusion families (late_mean, late_stack_logit),
  builds the MoE routing report, and computes per-(task, backbone) metrics, bootstrap
  paired comparisons, and a cross-task grid.
- **Attention heatmaps** (`scripts/heatmaps/make_heatmaps.py`): whole-slide gated-attention
  overlays + top-tile grids from the `image_only` checkpoints, for the top true-positive
  progressor cases.

### Original 3 tasks, full model set (no gaps)
`ever_progress` (`Progressor_label`), `at_risk_3y` (`AtRisk_3y`),
`next_biopsy_progression` (`NextBiopsyProgression_LGD2plus`); backbones UNI2 + GigaPath;
families cnv_only, image_only, early/intermediate/coattention fusion, end-to-end MoE,
derived late_mean / late_stack_logit.

### Original findings (as first reported)
1. Task choice matters — `at_risk_3y` was the strongest endpoint, next-biopsy the weakest.
2. Multimodal fusion beat either single modality on every task.
3. The end-to-end MoE landed mid-pack — consistent with over-parameterisation at n≈150;
   its value is interpretability, not accuracy.
4. MoE routing is interpretable — the gate sends most biopsies (59–69%) to the multimodal
   expert and higher-risk biopsies preferentially there; the CNV-only expert is barely used.

*(Original commits: `d2df495` scaffold → `47e1f12` release/collect/results → `a31dbe6`
results + summary → `452e3f5` heatmaps → `80bf93c` HANDOFF.)*

---

## Part B — Update wave (this work, on top of Part A)

Four commits (`bf0875b`, `ff02b0d`, `f119af8`, `70b0a1e`). All authored `rzuberi
<rehan.zuberi@cruk.cam.ac.uk>` (the branch's established address), data guard passing on
each, pushed and in sync with origin.

### B1 — Honesty corrections to the reported results (`bf0875b`)
A verification of the reported tables against the raw metrics found the original SUMMARY
overclaimed: it said "late-mean fusion wins every task." It does not on `ever_progress`,
where **early_fusion (gigapath) takes the top AUPRC (0.575 vs 0.552) and ties late-mean on
ROC AUC (both 0.82)**. Two fixes:
- Reworded the finding to the honest read: fusion beats either single modality on all
  tasks; late-mean is the most consistent fusion but early_fusion edges it on ever_progress.
- The cross-task grid had shown only 5 of 8 families, hiding early_fusion (the ever_progress
  winner). It now shows all 8 families plus a `best_by_auprc` column (AUPRC breaks the
  ever_progress ROC tie). `make_results.py` regenerates the grid this way, verified
  byte-identical to the committed tables — reproducible, not hand-edited.

### B2 — Frozen-expert MoE sanity comparison (`ff02b0d`, extended in `f119af8`)
New `scripts/frozen_expert_moe.py` answers the open question "is the end-to-end MoE's
mid-pack showing a weakness of *gated routing*, or the cost of *jointly learning experts*
at small n?" It routes among the **frozen** per-fold OOF of the already-trained experts
(image_only, cnv_only, intermediate_fusion), learning only a tiny gate fit per outer fold
on the other folds only — so every combined prediction stays out-of-sample and comparable
to the baselines on identical rows/folds. Two gate variants: `logistic` (per-sample soft
responsibilities) and `static` (single best convex blend on train folds).

**Result across all five tasks (see `FROZEN_MOE.md`):** the frozen-expert MoE **beats the
end-to-end MoE on every task** and matches or exceeds late-mean on **three of five**
(winning outright on next_biopsy_progression, next_biopsy_highrisk and at_risk_3y_censored;
trailing late-mean narrowly on ever_progress by 0.008 and at_risk_3y by 0.015 AUPRC). This
confirms the mechanism: the end-to-end MoE's mid-pack AUPRC is the cost of jointly
*learning* experts at n≈150, not a failure of gated routing — freeze the experts and a
cheap gate performs at the level of the best late fusion.

### B3 — Two new endpoints (`f119af8`)
Both scored under the identical nested-CV protocol and collected with derived late fusion.

- **`next_biopsy_highrisk`** (4th deck task; `NextBiopsyHighRisk_ge3`). The handoff had
  flagged this as shrinking from NaNs, but on the *matched* cohort it is clean: 707 rows,
  150 patients, 36 positive patients. **early_fusion (uni2) tops it at AUPRC 0.613 / ROC
  0.832** — the highest early-fusion result across all tasks — with fusion clearly beating
  single modalities.

- **`at_risk_3y_censored`** — the **honest 3-year at-risk endpoint**. The original
  `at_risk_3y` used the deck's precomputed label, whose entire "negative" class is
  under-followed biopsies (every `AtRisk_3y=0` row has <3y follow-up), which inflates
  performance. A naive `--censor-underfollowed` on that column collapses to a single class
  (all negatives removed). The fix (`build_task_release.py --derive-at-risk
  --horizon-years N`) **derives** the label from event timing + observed follow-up:
  positive = progression event within the horizon; negative = confirmed event-free THROUGH
  the horizon (a progressor whose event is beyond it, or a non-progressor followed ≥ the
  horizon); everything else (under-followed, no event yet) censored out. Honest 3-year
  cohort: **77 patients, 25 positive, 404 biopsies censored.** Best model drops from ROC
  **0.89 (optimistic) to 0.78** (intermediate_fusion, AUPRC 0.682) — quantifying how much
  the deck's `at_risk_3y` was inflated by easy under-followed negatives. Fusion still leads
  (late_mean vs cnv_only ΔAUPRC +0.126) but CIs cross zero at this smaller n. **Use the
  censored numbers.** The `--horizon-years` flag also makes the 1y/2y/4y/5y horizons a
  one-command build + campaign each.

`make_results.py` and `submit_campaign.py` both gained a `--tasks` flag so new endpoints
score/submit without editing hardcoded lists.

### B4 — Reported-claim correction (`70b0a1e`)
A follow-up check caught that the frozen-MoE writeup said "matches or exceeds late-mean on
four of five" — it is **three of five** (ever_progress and at_risk_3y trail late-mean by
0.008 / 0.015 AUPRC). Corrected in `FROZEN_MOE.md` and `SUMMARY.md`.

### B5 — Infrastructure hardening (delivered across the wave)
- **`--exclude-nodes`** added to `submit_campaign.py` after GPU node `clust1-cuda-4` threw
  persistent `cudaErrorECCUncorrectable` while SLURM still listed it healthy — it silently
  killed units and left partial output dirs that blocked reruns (the training runner's
  overwrite-guard treats a 1-file partial dir as "complete"). Cleared the ECC-orphaned
  partials and resubmitted on healthy nodes; the 4th-task campaign then completed 55/55.
- `iter_units()` generalised to arbitrary task lists (was hardcoded to the original three).

---

## Consolidated results (all five tasks, best model per task)

Patient-level nested 5-fold CV. "Best" ranked by AUPRC (the primary metric).

| task | n patients (pos) | best family | backbone | AUPRC | ROC AUC | Brier | late_mean AUPRC / ROC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ever_progress | 150 (35) | early_fusion | gigapath | 0.575 | 0.821 | 0.201 | 0.552 / 0.768 |
| at_risk_3y *(optimistic)* | 150 (81) | late_mean | uni2 | 0.898 | 0.886 | 0.169 | 0.898 / 0.886 |
| next_biopsy_progression | 150 (50) | late_mean | uni2 | 0.625 | 0.766 | 0.180 | 0.625 / 0.766 |
| next_biopsy_highrisk | 150 (36) | early_fusion | uni2 | 0.613 | 0.832 | 0.174 | 0.524 / 0.789 |
| **at_risk_3y_censored** *(honest 3y)* | 77 (25) | intermediate_fusion | gigapath | 0.682 | 0.735 | 0.232 | 0.592 / 0.781 |

Full 8-family grid (ROC AUC with specificity@90%-sensitivity) is in `cross_task_grid.md`;
per-(task, backbone) metrics and bootstrap paired deltas in `metrics_*.csv` / `paired_*.csv`;
the frozen-expert MoE comparison in `FROZEN_MOE.md` / `frozen_moe_comparison.csv`.

### Headline conclusions (honest)
1. **Multimodal fusion beats either single modality on every task** — but the winning
   *fusion variant* is task-dependent: late-mean on at_risk_3y and next_biopsy_progression,
   early_fusion on ever_progress and next_biopsy_highrisk, intermediate_fusion on the
   honest censored at-risk-3y.
2. **The optimistic at_risk_3y (ROC 0.89) is inflated** by under-followed negatives; the
   honest censored version is **ROC 0.78**. This ~0.11 gap is the single most important
   correction in the update.
3. **The end-to-end MoE is not the way to get gated routing at this n** — a cheap
   frozen-expert router beats it everywhere and matches the best late fusion. The
   end-to-end MoE's value is its interpretable routing report, not accuracy.
4. Effect sizes come with wide bootstrap CIs at n=77–150 (several cross zero); these are
   internal-CV results with no external validation. Do not over-claim.

---

## Reproduce (from repo root; `PY=/home/zuberi01/miniforge3/envs/virchow2/bin/python`)

```bash
# Build releases (BASE = analysis/multitask_moe_20260721)
$PY multitask_moe/scripts/build_task_release.py --task next_biopsy_highrisk \
    --label-column NextBiopsyHighRisk_ge3 --out-release <BASE>/next_biopsy_highrisk/release
$PY multitask_moe/scripts/build_task_release.py --task at_risk_3y_censored --label-column AtRisk_3y \
    --derive-at-risk --horizon-years 3.0 --out-release <BASE>/at_risk_3y_censored/release
# Train (dry-run first; exclude any ECC-faulty node)
$PY multitask_moe/scripts/submit_campaign.py --tasks <task> --exclude-nodes clust1-cuda-4 --submit
# Collect OOF + late fusion, then metrics/grid across all tasks, then frozen-MoE
for b in uni2 gigapath; do $PY multitask_moe/scripts/collect_and_report.py --task <task> --backbone $b --derive-late; done
$PY multitask_moe/scripts/make_results.py --tasks ever_progress,at_risk_3y,next_biopsy_progression,next_biopsy_highrisk,at_risk_3y_censored
for b in uni2 gigapath; do for g in logistic static; do $PY multitask_moe/scripts/frozen_expert_moe.py --task <task> --backbone $b --gate $g; done; done
```

---

## Still open (deferred, with reasons)

- **Virchow2 backbone** — deferred: the prerequisite extraction script named in the handoff
  (`scripts/extract_foundation_from_masks.py`) does not exist in the repo and there is no
  Virchow2 feature dir (only uni2 + gigapath). A 959-slide GPU precompute needs that path +
  gated HF weights confirmed first.
- **Extra at-risk horizons (1y/2y/4y/5y)** — machinery is ready (`--derive-at-risk
  --horizon-years N`); not run to avoid ~220 extra GPU units without a request.
- **PR `multitask-moe` → `main`** — left for the owner to trigger; consider lifting
  `src/moe.py` / `src/moe_training.py` into the `barrett` package on merge.
- **Runner self-heal** — `train_outer_fold.py`'s overwrite-guard treats an ECC-killed
  partial dir as complete; it should clean its own partial output on a fresh claim so future
  campaigns self-heal from node faults (currently handled manually + `--exclude-nodes`).
- **Thesis interpretation figures** — image-vs-multimodal top-patch packs and MoE routing
  figures (the deck had these).

*Inviolable rule throughout: no patient data in Git — only code, small result tables, and
downsized figures are committed; everything heavy stays under the external `<BASE>`.*
