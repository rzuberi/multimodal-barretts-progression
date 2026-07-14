# Agent handoff — Chapter 1 (Barrett's LGD2+ progression)

**Purpose.** This document lets a fresh Claude agent (on a different account,
with no access to the previous session's chat history or sandbox artifacts)
resume the Chapter 1 work from a clean slate. Everything needed is either in
this repository or on the CRUK CI cluster at the paths below. Written after the
work described in git commit `6cc83bf`.

---

## 0. The one rule that governs everything

**Raw patient data never leaves the cluster.** WSIs, CNV matrices, the master
CSV, and any identifiable clinical metadata stay under
`$BARRETTS_EXPERIMENT_ROOT` on the cluster. The GitHub repo is for code, docs,
small allowlisted result CSVs, and the write-up. Figures (`*.png`) are **not**
committed — they are regenerated from allowlisted CSVs by a script.

The machine-enforced version of this rule is `scripts/assert_no_data_tracked.sh`:
it fails if any data-like file (`.csv .png .svs .pt .h5 …`) is tracked except an
explicit allowlist of small result CSVs under `reports/thesis_ch1/`. **Run it
before every commit.** When you add a new result CSV that must be committed,
`git add -f` it AND add a matching `grep -v` allowlist line to that script.

Division of labour observed throughout:
- **External environment** (your sandbox): code quality, reproducibility, tests,
  figures from allowlisted CSVs, interpretation, chapter drafting.
- **CRUK cluster**: everything that touches patient data (training, OOF
  prediction, attention-map generation, reading the master CSV).

---

## 1. Where things live

**GitHub:** `git@github.com:rzuberi/multimodal-barretts-progression.git`
(public repo; commit as GitHub user **rzuberi**, `rehanzuberi@icloud.com` —
never as "Claude"/"Anthropic". There is currently no "Claude" authorship
anywhere in the tree; keep it that way.)

**Cluster clone (has working SSH remote + push access):**
`/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/multimodal-barretts-progression`

**Cluster host:** `ssh:cluster` (login node `clust1-sub-1.cri.camres.org`),
user `zuberi01`, group `fmlab`. Requires the CRUK CI VPN to be connected
manually; the connection sometimes drops. SLURM scheduler; account `fmlab`;
partitions `cuda, rocm, h200, epyc`.

**Data root (env var used throughout the code):**
```
BARRETTS_EXPERIMENT_ROOT=/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training
BARRETTS_MASTER_CSV=$BARRETTS_EXPERIMENT_ROOT/data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv
```

**Frozen final release (July 13) — the source of all Chapter 1 results:**
```
$BARRETTS_EXPERIMENT_ROOT/analysis/chapter1_lgd2_final_pre_event_20260713_final/
  training_final_nested_cv_v1/        # per-family, per-fold checkpoints
    cnv_only/            fold1..fold5/
    image_only/          fold1..fold5/
    early_fusion/        fold1..fold5/
    intermediate_fusion/ fold1..fold5/
    late_mean/           fold1..fold5/
    late_stack_logit/    fold1..fold5/
    coattention_fusion/  fold1..fold5/
    failed_attempts/
  training_advanced_fusion_nested_cv_v1/
  matched_manifest.csv  patient_splits.csv  pre_event_cohort.csv  row_to_fold.csv
```

Each `cnv_only/foldN/` contains: `model.joblib` (sklearn Pipeline),
`platt_calibrator.joblib`, `cnv_feature_importance.csv`, `outer_test_predictions.csv`,
`resolved_config.yaml`, `fold_metadata.json`, `environment.txt`, plus inner-CV files.

**Shared imaging datasets:** `/mnt/scratche/slow/fmlab/datasets/imaging`
(group resource; subdirs `best2/best3/best4`, `delta`, `ERIN`, `occams`,
`SEARCH`, `SWGCohort`, `TissueSegmentation`).

**Conda envs on cluster:** `/home/zuberi01/miniforge3/envs/` — the relevant ones
are `erin` (python 3.10, sklearn 1.5.2 — analysis/figures) and `virchow2`
(python 3.10, sklearn 1.7.2 — the env that produced the frozen checkpoints).

---

## 2. Environment setup

Two environment files exist because the analysis stack and the model-training
stack diverge on scikit-learn (unpickling the frozen models under the wrong
sklearn raises `InconsistentVersionWarning`):

- `environment.yml` / `requirements.txt` — **analysis + figures** (sklearn 1.5.2,
  numpy 1.26.4, pandas 2.2.3, matplotlib 3.10.8). Mirrors cluster `erin`.
- `environment-training.yml` — **model provenance / reload / retrain**
  (sklearn 1.7.2, numpy 2.2.6, pandas 2.3.3, torch 2.9.1). Mirrors cluster
  `virchow2`. **Use this env to load any `model.joblib` from the frozen release.**

`pyproject.toml` makes `src/barrett` an editable package: `pip install -e .`
Tests: `pytest -q` (uses synthetic fixtures only; last run 141 passed, 4 skipped).
`scripts/make_synthetic_fixtures.py` generates a fully synthetic master CSV that
matches the data contract for pipeline inspection without real data.

---

## 3. What this session completed

**Commit `6dd22a7`** — reproducibility packaging + Chapter 1 figures + skeleton:
- Added `pyproject.toml`, `requirements.txt`, `environment.yml`.
- `scripts/make_chapter1_figures.py` — regenerates all figures from allowlisted CSVs.
- `scripts/make_synthetic_fixtures.py`, `scripts/run_all.sh` (two tiers: `figures`
  runs anywhere, `tables` needs the cluster data root).
- `reports/thesis_ch1/chapter1.md` — chapter skeleton, sections 1.1–1.8, Table 1.1,
  figures embedded by relative filename, results pre-drafted from the locked numbers.
- Fixed broken script pointers in `docs/final_results_manifest.md`.

**Commit `b2a8c57`** — CNV window→gene annotation (Task 3 complete):
- `scripts/03_annotate_cnv_genes.py` — queries Ensembl REST API for all 632 CNV
  features (arm-level tiled, window direct). Output: gene annotation CSV.
- `reports/thesis_ch1/lgd2_cnv_feature_gene_annotation.csv` — 632 features ×
  {n_protein_coding_genes, cancer_genes, top_cancer_genes}. 77-gene OAC priority set.
- `reports/thesis_ch1/lgd2_cnv_arm_gene_summary.csv` — top-25 arm features (chapter table).
- `scripts/assert_no_data_tracked.sh` — allowlist extended for two new CSVs.

**Commit `6cc83bf`** — CNV feature-importance interpretability (the item that was
mislabelled "blocked"):
- `scripts/07_aggregate_cnv_importance.py` — reads the five `cnv_only/foldN/cnv_feature_importance.csv`
  and aggregates to `reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv`
  (632 features × mean/std/min/max importance, rank_mean, rank_best, n_folds).
- `scripts/make_chapter1_figures.py` — added `fig_cnv_importance()` → Fig 1.5.
- `environment-training.yml` added; env split documented.
- `chapter1.md` Section 1.6 rewritten with CNV results and caveats.
- `docs/*` and `PROJECT_STATE.md` updated: CNV importance `BLOCKED → AVAILABLE`.
- `scripts/assert_no_data_tracked.sh` allowlist extended for the new CSV.

### Locked Chapter 1 numbers (patient-level, 5-fold patient-disjoint CV, n=150)
- Late-mean (headline multimodal): AUPRC 0.630, ROC AUC 0.774, Brier 0.184, sens 0.58, spec 0.80.
- CNV-only baseline: AUPRC 0.538, ROC AUC 0.663, Brier 0.216, sens 0.28, spec 0.90.
- Late-mean − CNV-only paired deltas (patient bootstrap, 95% CI):
  ΔAUPRC +0.091 (−0.036 to +0.219, **includes 0**),
  ΔROC AUC +0.111 (+0.002 to +0.219, **excludes 0**),
  ΔBrier −0.032 (−0.062 to −0.004, **excludes 0**).
- Primary-metric (AUPRC) benefit is therefore **not conclusive**; the chapter is
  calibrated to say ROC AUC + Brier improve with CIs excluding zero, AUPRC improves
  in point estimate only. Do not overstate this.
- Top CNV loci (all in top ranks of all 5 folds): 20p, 11q, 7p, 17p, 12q
  (17p≈TP53, 7p≈EGFR, 20p/20q gains recurrent in OAC). Importance spread is narrow
  (PCA(64) compresses correlated arm signal) — treat ranking, not magnitude, as the
  signal. Impurity-based → descriptive, not causal.

### Reproduce
```
# figures (no data needed, runs anywhere):
python scripts/make_chapter1_figures.py      # or: bash scripts/run_all.sh figures
# tables + CNV aggregation (cluster, needs $BARRETTS_EXPERIMENT_ROOT):
bash scripts/run_all.sh tables
```

---

## 4. What is still pending (needs a cluster compute run)

These are the remaining Chapter 1 gaps. Data lives in the frozen release; the
work is aggregation/figure/table generation, not new model training.

1. **Histology attention maps** — regenerate from the *final* checkpoints for the
   8 reselected pre-event OOF cases. The existing committed attention figures came
   from developmental models, not the final release. Case selection is in
   `reports/thesis_ch1/lgd2_final_pre_event_interpretation_cases.csv` and
   `scripts/30_select_lgd2_final_interpretation_cases.py`. The image-model
   checkpoints are under `training_final_nested_cv_v1/image_only/foldN/`. Run on a
   GPU partition (`cuda`/`h200`). Transfer back only the reviewed heatmap PNGs
   (kept out of git) + a small summary CSV.

2. **Fusion help/hurt/fail case table** — from the final patient-level OOF
   predictions (`training_final_nested_cv_v1/*/foldN/outer_test_predictions.csv`).
   Compare per-patient probabilities across cnv_only / image_only / late_mean to
   classify each case as fusion-helps / fusion-hurts / fusion-fails. Emit a small
   allowlisted CSV + a chapter table.

3. ~~**Window→gene annotation map**~~ **DONE (commit `b2a8c57`)**
   All 632 features (44 arm-level, 587 5 Mb windows, `cx`) annotated against
   Ensembl GRCh38 protein-coding genes. 101 features carry ≥1 cancer gene from
   a 77-gene OAC/Barrett priority set. Key loci match known OAC biology:
   17p→TP53, 7p→EGFR, 12q→CDK4/MDM2/KMT2D, 18q→SMAD4/BCL2/GATA6, 20p→CDC25B/PCNA/FOXA2.
   Outputs: `reports/thesis_ch1/lgd2_cnv_feature_gene_annotation.csv` (all 632 features),
   `reports/thesis_ch1/lgd2_cnv_arm_gene_summary.csv` (top-25 arm summary),
   `scripts/03_annotate_cnv_genes.py` (reproducible script, external sandbox, ~20 min).

4. **Two wrapper scripts** flagged in `docs/final_results_manifest.md`:
   - `scripts/05_make_early_prediction_table.py` — the data already exists at
     `reports/thesis_ch1/lgd2_patient_level_metrics_early_prediction_only.csv`;
     only the table-assembly wrapper is missing.
   - `scripts/06_make_interpretability_summary.py` — would combine CNV importance
     (now available) with histology attention maps (item 1). Blocked only on item 1.

`chapter1.md` still has `[TODO]`/`[DRAFT]` markers on the narrative prose
(Sections 1.5 interpretation, 1.7, 1.8) that need the author's voice.

---

## 5. Operational notes for working with this cluster (learned this session)

- **`call_command` has a hard 60-second limit.** Anything longer (training,
  attention-map generation, large scans) must go through `submit_job` (SLURM).
  A recursive `du`/scan of the data root will time out — target specific paths.
- **Committing from the cluster:** the sandbox clone and the cluster clone are
  separate; the cluster clone is the one with push access (SSH key authenticates:
  `git@github.com` → "Hi rzuberi! You've successfully authenticated"). Commit
  there with `git -c user.name="rzuberi" -c user.email="rehanzuberi@icloud.com"`.
- **Inline command size limit:** a base64-embedded commit script over ~65 KB hits
  `Argument list too long`. If you must push files whose combined size is large,
  tar+gzip+base64 them into one blob (compresses ~4×) and unpack on the cluster,
  rather than embedding each file uncompressed.
- **Never `git add -A`.** Stage files explicitly so no data-like file is caught
  accidentally; then run `scripts/assert_no_data_tracked.sh` on the staged tree.
- **Loading a frozen `model.joblib`:** use the `virchow2` env (sklearn 1.7.2),
  not `erin` (1.5.2), or you get an `InconsistentVersionWarning`. Introspect
  read-only (print `type`, `n_features_in_`, step names) — do not export the
  model itself off-cluster.

---

## 6. Model architecture reference (cnv_only)

`sklearn.pipeline.Pipeline`:
`SimpleImputer(strategy='median')` → `StandardScaler` →
`PCA(n_components=64, random_state=20261713)` →
`RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_leaf=2,
class_weight='balanced', max_features='sqrt', random_state=20261713)`.
632 genome-window input features; `classes_=[0,1]`; configuration id
`cnv_rf_conservative`; registry version `chapter1_lgd2_final_models_v1`.
Per-fold validation threshold chosen for target specificity 0.9
(fold 1: threshold 0.3337, n_outer_train 533 rows / 120 patients,
n_outer_test 174 rows / 30 patients).

---

## 7. Primary endpoint definition (do not drift)

`NextBiopsyProgression_LGD2plus` — progression = HGD / IMC / OAC **or** two
consecutive LGD biopsies. `NextBiopsyProgression_LGD3plus` is a *supplementary*
endpoint only. LGD3+ legacy interpretation outputs under
`analysis/cnv_explainability/` are a **different endpoint** and are not valid
primary evidence for Chapter 1.

The strict pre-event cohort (generated by `src/barrett/data/pre_event.py`):
959 eligible-schema rows / 470 biopsies / 160 patients → 707 rows / 359 biopsies
/ 150 patients after excluding endpoint-not-evaluable (38 rows), at-event (183),
post-event (31); 107 positive rows / 50 progressor patients. Data contract (33
required columns) is in `docs/data_contract.md`.
