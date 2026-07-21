# Multitask + Mixture-of-Experts — Handoff

Self-contained handoff for continuing the Barrett's oesophagus multitask + MoE work.
Written 2026-07-21. No prior conversation context is required to pick this up.

---

## 1. Goal & background

The March 2026 Fitzgerald-group deck showed strong results across **four task framings**
and a **Mixture-of-Experts (MoE)** that routed each biopsy to an image / CNV / multimodal
expert, plus whole-slide attention heatmaps. The current frozen repo had dropped all of
that — it trains only one endpoint (`NextBiopsyProgression_LGD2plus`), has no MoE, and its
LGD2+ heatmaps were stale.

This work **rebuilds the multitask + MoE experiments in isolation** (new branch + folder),
runs them as parallel self-deduplicating sbatch jobs, and regenerates heatmaps — with the
**full model set for every task including MoE (no gaps)**. The frozen Chapter-1 results
were never touched.

### Decisions taken (by the project owner)
- **Tasks (core 3):** `ever_progress` (`Progressor_label`), `at_risk_3y` (`AtRisk_3y`),
  `next_biopsy_progression` (`NextBiopsyProgression_LGD2plus`).
- **Backbones:** UNI2 + GigaPath now; **Virchow2 deferred** (no embeddings exist — needs a
  GPU precompute of all 959 slides).
- **MoE:** end-to-end trained gate+experts (not frozen-expert routing).
- **Isolation:** git branch `multitask-moe` + folder `multitask_moe/`; commit/push as
  `rzuberi` with brief messages.

---

## 2. Where everything lives

- **Cluster access:** `ssh cluster` (non-interactive; each command is a fresh shell — use
  absolute paths).
- **Repo (git):** `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression`
  - Branch: **`multitask-moe`** (remote `git@github.com:rzuberi/multimodal-barretts-progression.git`).
  - This work: **`multitask_moe/`** (everything additive; imports the `barrett` package,
    edits nothing in `src/`).
- **External output root (NOT in git — data/checkpoints/OOF/heatmaps):**
  `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/multitask_moe_20260721/`
  - Per task: `<task>/release/` (cohort+splits+feature views, mostly symlinks to frozen),
    `<task>/train/<backbone>/` (per-family per-fold outputs + `oof/`), `<task>/train/shared/cnv_only/`,
    `state/` (self-dedup markers), `slurm_logs/`.
- **Frozen Chapter-1 release reused (read-only):**
  `.../analysis/chapter1_lgd2_final_pre_event_20260713_final/` — provides `matched_manifest.csv`,
  `pre_event_cohort.csv` (carries every task label), and `feature_views/{cnv,uni2,gigapath}`.
- **Conda environments:**
  - Training / collect / results: `/home/zuberi01/miniforge3/envs/virchow2/bin/python` (torch+CUDA).
  - Heatmaps: `/home/zuberi01/miniforge3/envs/pathology/bin/python` (torch 2.7.1 + openslide).
- **Cached foundation features (per-slide NPZ, task-independent):**
  `.../barretts_retraining/data/foundation_outputs/{uni2,gigapath}_tile224_lvl2/slide_embeddings/*.npz`
  (959 slides each; keys include `embeddings (256,1536)`, `coords_level`, `slide_path`, `level`, `tile_size`).

---

## 3. How the harness works (what was reused vs added)

The frozen harness is **task-agnostic below the manifest layer**: training reads only a
generic `y_progressor` column; the endpoint is bound at manifest-build time. The frozen
chain is `17 (cohort) → 18 (splits) → 21 (manifest) → 22 (feature views) → 24 (train fold)
→ 27 (collect+late) → 28 (results)`.

Reused unchanged from `src/barrett/` (imported as a library):
- `training/loops.py` — `fit_neural`, `predict_neural`, `build_model`, `patient_max_predictions`, `NeuralFit`.
- `training/data.py` — `CanonicalFeatureStore`, `FinalDataset`, `load_cnv_matrix`, `collate_final`.
- `training/inner_cv.py`, `evaluation/nested_selection.py`, `evaluation/cross_fitted_thresholds.py`,
  `evaluation/output_contract.py`, `evaluation/metrics.py`, `evaluation/paired_comparison.py`,
  `training/artifacts.py` (`collect_family`, `reject_repo_output`), `training/late_fusion.py` (`derive_late_fold`),
  `data/splits.py` (`make_patient_folds`), `models/*`.

Key trick: the MoE dataset is built with `family="intermediate_fusion"` so each batch
carries both the image bag and the CNV vector **without modifying shared `data.py`**.

---

## 4. Files in `multitask_moe/` (what each does)

```
multitask_moe/
├── README.md                     # short orientation
├── plan.md                       # the approved implementation plan
├── HANDOFF.md                    # this file
├── configs/
│   ├── tasks.yaml                # 3 task defs: label column, eligibility, cohort scope, balances
│   ├── models_uni2.yaml          # model registry (clone of frozen + `image_index` key + `moe` family)
│   └── models_gigapath.yaml      # same, image_index -> gigapath (generated via sed uni2->gigapath)
├── src/
│   ├── moe.py                    # MixtureOfExperts nn.Module + GatedAttentionPool + load_balance_loss
│   └── moe_training.py           # fit_moe / predict_moe (nested-CV-safe; mirrors fit_neural)
├── scripts/
│   ├── build_task_release.py     # RE-LABEL frozen cohort per task; build manifest + stratified splits
│   ├── train_outer_fold.py       # one (task,backbone,family,fold); copy of frozen 24 + moe + generic index
│   ├── submit_campaign.py        # duplicate-per-node self-dedup sbatch orchestrator (dry-run default)
│   ├── collect_and_report.py     # collect OOF + derive late fusion + MoE routing report (per task,backbone)
│   ├── make_results.py           # per-(task,backbone) metrics/paired diffs + cross-task grid
│   └── heatmaps/
│       └── make_heatmaps.py      # WSI attention overlays + top-tile grids from image_only checkpoints
├── slurm/
│   └── run_unit.sh               # per-unit wrapper: done-check, atomic mkdir claim, self-cancel, retry
└── reports/                      # COMMITTED result tables + figures
    ├── SUMMARY.md                # results narrative + caveats
    ├── cross_task_grid.{csv,md}
    ├── all_metrics.csv
    ├── metrics_<task>_<backbone>.csv
    ├── paired_<task>_<backbone>.csv
    └── figures/                  # 2 downsized example overlays
```

---

## 5. The self-deduplicating sbatch scheme (the required design)

`submit_campaign.py` enumerates work-units `(task, backbone, family, fold)` and submits
**one copy to every healthy node** in the unit's lane partition(s):
- GPU lane (neural + moe): `h200` (`--qos h200_preempt --gres gpu:nvidia_h200:1`) + `cuda`
  (`--gres gpu:L40S:1`), all nodes.
- CPU lane (`cnv_only`): `epyc` (`--qos epyc_limit`), capped to 8 nodes (change `LANES["cpu"]["max_nodes"]`).
- CNV is backbone-independent → trained once per task under `train/shared`, symlinked into
  each backbone dir at collect time.

Each copy runs `slurm/run_unit.sh <state_dir> <unit_id>`:
1. if `state/<unit_id>.done` exists → exit 0 (already complete).
2. `mkdir state/<unit_id>.claim` (atomic) → win, else self-cancel (exit 0). Stale-claim
   recovery: if the owning job id is gone from `squeue`, reclaim.
3. winner best-effort `scancel --name barrett_mm_<unit_id> --state=PENDING` (drops siblings).
4. runs the command in `state/<unit_id>.cmd` (with `--resume`); on success `touch .done`;
   trap always releases the claim so failures retry.

**Resume is free:** re-running `submit_campaign.py --submit` skips `.done` and already-queued
units. Default run is a **dry run**; pass `--submit`. Filters: `--tasks --backbones --families
--folds --lanes --max-nodes-per-unit`.

Validated at scale: the full 165-unit campaign (~1,300 copies) ran with 0 submit errors;
each unit executed exactly once; finished in ~37 min wall time.

---

## 6. Reproduce / re-run (exact commands)

All from the repo root, `PY=/home/zuberi01/miniforge3/envs/virchow2/bin/python`.

```bash
# (A) Build per-task releases (re-label frozen cohort; ~instant)
$PY multitask_moe/scripts/build_task_release.py --task ever_progress --label-column Progressor_label \
    --out-release <BASE>/ever_progress/release
$PY multitask_moe/scripts/build_task_release.py --task at_risk_3y --label-column AtRisk_3y \
    --out-release <BASE>/at_risk_3y/release            # add --censor-underfollowed for the censored variant
$PY multitask_moe/scripts/build_task_release.py --task next_biopsy_progression \
    --label-column NextBiopsyProgression_LGD2plus --out-release <BASE>/next_biopsy_progression/release --reuse-frozen

# (B) Submit the whole campaign (dry-run first, then --submit)
$PY multitask_moe/scripts/submit_campaign.py                 # dry run
$PY multitask_moe/scripts/submit_campaign.py --submit        # submit; re-run to resume

# (C) Collect + derive late fusion + MoE routing report (per task,backbone)
for t in ever_progress at_risk_3y next_biopsy_progression; do for b in uni2 gigapath; do
  $PY multitask_moe/scripts/collect_and_report.py --task $t --backbone $b --derive-late; done; done

# (D) Results tables + cross-task grid (writes multitask_moe/reports/)
$PY multitask_moe/scripts/make_results.py

# (E) Heatmaps (pathology env)
PP=/home/zuberi01/miniforge3/envs/pathology/bin/python
$PP multitask_moe/scripts/heatmaps/make_heatmaps.py --task next_biopsy_progression --backbone uni2 --n-cases 4
```
`<BASE>` = `.../analysis/multitask_moe_20260721`. Monitor with
`squeue -u zuberi01 -h | grep barrett_mm` and `ls <BASE>/state/*.done | wc -l` (target 165).

---

## 7. Results (patient-level, nested 5-fold patient-disjoint CV, 707 rows / 150 patients)

Cross-task grid — ROC AUC (specificity@90%-sensitivity), best backbone:

| task | image_only | cnv_only | moe | late_mean | intermediate_fusion |
| --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.73 (0.42) | 0.82 (0.58) | 0.78 (0.47) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.84 (0.57) | 0.89 (0.78) | 0.81 (0.36) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.73 (0.34) | 0.77 (0.36) | 0.72 (0.46) |

Findings: (1) task choice matters — `at_risk_3y` (0.89) beats next-biopsy (0.77);
(2) **late_mean fusion wins every task**; (3) **end-to-end MoE is mid-pack** (over-parameterised
at n≈150 — expected); (4) MoE routing is interpretable (gate → 59–69% multimodal, higher-risk
biopsies preferentially to multimodal, CNV expert barely used). Full tables in
`multitask_moe/reports/`; per-model OOF + routing reports under
`<BASE>/<task>/train/<backbone>/oof/`.

---

## 8. MoE design details

`src/moe.py::MixtureOfExperts` — three experts each emit a logit:
- **image** = `GatedAttentionPool` (mirrors `barrett.models.AttentionMIL`) → head.
- **cnv** = MLP on the standardized CNV vector → head.
- **multimodal** = independent image pool + CNV branch → fusion → head.
- **gate** = MLP over `[image_feat, cnv_feat]` → softmax over 3 experts; final logit = weighted sum.

Small by design (img_hidden 128, cnv_hidden 64, dropout 0.3–0.4) + **load-balancing loss**
(`load_balance_loss`, minimised at uniform routing, weight `load_balance_lambda`). Trained
in `src/moe_training.py::fit_moe`, which mirrors `fit_neural` exactly (validation-only early
stopping on patient-max AUPRC, pos_weight BCE, CNV normalisation from train split) so MoE is
selected/calibrated under the identical nested-CV contract. `train_outer_fold.py` writes
per-fold `moe_routing.csv` (gate weights + argmax expert); `collect_and_report.py` aggregates
it into `moe_routing_report.{csv,md}` (routing %, progressor rate, mean days-to-progression).
Two candidate configs (`moe_small_lb05`, `moe_small_lb10`) in the model registries.

---

## 9. Heatmaps

`scripts/heatmaps/make_heatmaps.py` (pathology env). Loads OUR `image_only` `model.pt`
(`state_dict` + `barrett.models.AttentionMIL`), computes per-tile gated attention via
`model.attention_weights(bag)`, and draws overlay + top-tile grid on the slide thumbnail
using the NPZ `coords_level` / `slide_path` (`/scratchc/`→`/mnt/scratche/slow/` remap).
Selects the top true-positive progressor cases from `image_only` OOF. Outputs to
`<BASE>/<task>/train/<backbone>/heatmaps/` (8 sets generated for next_biopsy + ever_progress,
uni2). Full PNGs stay external; 2 downsized examples committed to `reports/figures/`.

**Note:** the March renderer `scripts/run_wsi_explainability_case.py` (outer folder) expects
the old `model_state_dict` key + `image_mil` architecture — it is NOT compatible with our
checkpoints, which is why this self-contained generator exists.

---

## 10. Caveats / known limitations

- **`at_risk_3y` optimistic:** uses the deck's `AtRisk_3y` label as-is. 395/707 rows are
  negatives with <3y recorded follow-up (`MonthsBeforeLastBiopsy < 36`); see each task's
  `<BASE>/<task>/release/... ` → `task_cohort_audit.json` (`n_underfollowed_negatives`).
  A censored variant is one flag away: `build_task_release.py --censor-underfollowed`.
- **Numbers < March deck (0.81–0.88):** the deck was biopsy-level with per-model operating
  points; this is patient-level nested-CV — the stricter, honest read.
- **Internal CV only** — no external validation. Do not over-claim.
- **MoE mid-pack** — its value here is interpretability, not accuracy (small-n).

---

## 11. Open / next work items

1. **Virchow2 backbone (deferred):** no embeddings exist anywhere (the frozen `virchow2`
   index is UNI2 under a legacy name). Needs a GPU precompute over all 959 slides using the
   Virchow2 ViT-H model (check `scripts/extract_foundation_from_masks.py` in the outer folder;
   confirm it supports Virchow2 + gated HF weights), writing to
   `data/foundation_outputs/virchow2_tile224_lvl2/`, then build a `virchow2_index.csv` in each
   release and add `virchow2` to `submit_campaign.py::BACKBONES`.
2. **Censored `at_risk_3y` re-run** (see caveat) — and optionally add horizons 1y/2y/4y/5y
   (labels already in `pre_event_cohort.csv`: `AtRisk_1y..5y`, `Progress_in_1..5`).
3. **MoE variants** — a frozen-expert router (cheap, over already-trained OOF) as a sanity
   comparison to the end-to-end MoE; and/or gate-temperature / lambda sweeps.
4. **Next-biopsy-grade task** (4th deck task) — labels `NextBiopsyLabel` (multiclass) /
   `NextBiopsyHighRisk_ge3` (binary) exist but have ~389 NaN (no next biopsy) → smaller cohort.
5. **Merge:** open a PR `multitask-moe` → `main` when the owner is ready. Consider lifting
   `src/moe.py` / `src/moe_training.py` into `src/barrett/models/` + `src/barrett/training/`.
6. **Interpretation figures** — image-vs-multimodal top-patch comparison packs and MoE
   routing figures for the thesis (the deck had these).

---

## 12. Gotchas

- **No data in Git.** `training/artifacts.reject_repo_output` + policy: only code, small
  result tables, and downsized figures are committed. Everything heavy stays under `<BASE>`.
- **Repo-small principle** — every tracked file should have a clear role.
- **Commit as `rzuberi`:** `git -c user.name='rzuberi' -c user.email='rehan.zuberi@cruk.cam.ac.uk' commit ...`.
- **Editing large Python over ssh is painful** — author locally and `rsync`/`scp` to the repo.
- **`run_unit.sh` must be `chmod +x`** after any rsync that resets perms.
- **State dir is shared Lustre, never `/tmp`** (node-local) — the self-dedup depends on it.

---

## 13. Git history (branch `multitask-moe`)

```
452e3f5  Add WSI attention heatmap generator + example overlays (multitask image_only)
a31dbe6  Add multitask+MoE results: cross-task grid, per-task metrics, MoE routing, summary
47e1f12  Add per-task release builder, collect/report, results scripts; orchestrator CPU cap + stale-claim fix
d2df495  Add multitask+MoE scaffold: MoE model/trainer, fold runner, self-dedup sbatch orchestrator, configs
```
