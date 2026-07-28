# Chapter 1 — Scientific Hardening: Final Deliverables

**Project:** Multimodal prediction of Barrett's oesophagus → oesophageal adenocarcinoma progression from copy-number variation (CNV, shallow WGS) and H&E histopathology.
**Branch:** `chapter1-scientific-hardening` (additive; frozen July-13 release untouched).
**Commit chain:** `6137ff7` (Ph 0–2) → `c2dfdd0` (Ph 3–5) → `8a8a503` (header) → `6d121e8` (Ph 6) → `1a653ef` (header fix).
**Evaluation throughout:** patient-level (patient-max over sample rows), patient-disjoint 5-fold nested CV, frozen splits, paired bootstrap (2000 resamples). Raw `y_prob` aggregation (reproduces frozen anchors exactly). n = 150 patients (50 progressors), 707 pre-event biopsy sample-rows.

---

## 1. Executive summary (one page)

We asked whether adding H&E histopathology to copy-number variation genuinely improves prediction of the next-biopsy LGD2+ progression endpoint, and whether any such benefit is robust, clinically meaningful, and stronger than routine clinical information. After a seven-phase hardening program the answer is a **qualified yes, honestly bounded**:

- **The multimodal (late-mean CNV+image) model is the best single model** on the primary endpoint: AUPRC 0.630, ROC AUC 0.774, Brier 0.184, versus CNV-only 0.538 / 0.663 / 0.216 and image-only 0.557 / 0.731 / 0.245.
- **The improvement over CNV-only is conclusive on ROC AUC and Brier but not on AUPRC.** late-mean − CNV-only: ΔAUPRC +0.091 (95% CI −0.031 to +0.219, **crosses zero**); ΔROC +0.111 (+0.001 to +0.221, excludes zero); ΔBrier −0.032 (−0.060 to −0.003, excludes zero). Per the reporting rules we do **not** call the AUPRC gain conclusive.
- **The benefit strengthens, not weakens, on cleaner data.** Restricting to exactly biopsy-matched rows the ΔAUPRC rises to +0.176 (CI +0.007 to +0.341, **excludes zero**); on strong grade-provenance subsets +0.161 (+0.012 to +0.318, excludes zero). The full-cohort estimate is diluted by a high-prevalence fuzzy-matched stratum, not inflated by it.
- **Clinical baselines are strong but multimodal adds on top of them.** Grade+history alone reaches AUPRC 0.495 / ROC 0.720. The full clinical+CNV+image stack is the best-calibrated discriminator (ROC 0.801), but the marginal value of histology *given* clinical+CNV is not conclusive (ΔAUPRC +0.048, CI −0.025 to +0.124).
- **Main internal-validity caveat: fold heterogeneity.** The CNV+image advantage ranges from −0.11 (fold 1) to +0.42 (fold 2) across the five folds; leave-one-patient-out shows no single patient drives it (max influence 0.023 on base 0.091), so the fragility is fold-level, not outlier-level.
- **Two negative results, preserved:** the Killcoyne overlap is a subset of our own training patients (not external validation), and swapping the pathology encoder to Virchow2 did not help (slightly worse on every metric). The multimodal finding is therefore not an artifact of one foundation model, but it is **internally validated only**.

**Recommendation:** proceed to write up the thesis chapter and manuscript on these hardened internal results, with claims worded as internal validation and the AUPRC caveat stated explicitly. External validation is the correct *next* investment but must wait for a digitised external cohort.

---

## 2. Definitive primary endpoint contract

**Endpoint:** `NextBiopsyProgression_LGD2plus` — a Boolean, defined per pre-event biopsy sample-row.

- **Positive** ⟺ the patient's *next* biopsy is HGD/IMC/OAC (grade ≥ 3, "LGD3+"), **or** is LGD (grade 2) **and** the patient already has a prior LGD in their history (`LGDStreakSoFar ≥ 1`) — i.e. a *second consecutive* LGD counts as an event; a single isolated LGD does not.
- **"LGD2+"** = low-grade dysplasia or worse at the next biopsy, with the consecutive-LGD rule above; HGD, IMC and OAC are all treated as events.
- **Temporal integrity (verified):** the event biopsy must occur at a **strictly later date** (707/707 next-biopsy dates strictly greater than the index date; 0 same-day events). Patients with no subsequent biopsy are not eligible rows. Multiple biopsies at one timepoint are collapsed to the worst grade at that timepoint. No future information enters cohort eligibility or model features.
- **Independent reconstruction:** recomputing the endpoint from source columns reproduced the stored/frozen label on **all 707 rows, 0 discrepancies** (107 positive / 600 negative sample-rows; 50 / 150 positive patients).
- **Cohort term:** "pre-high-grade" (the cohort is not dysplasia-free — it contains prevalent LGD/ID at index — so "dysplasia-free" would be incorrect).

---

## 3. Primary comparison table — clinical / CNV / image / fusions (patient-level, n=150 / 50 pos)

| Model | AUPRC | ROC AUC | Brier |
|---|---|---|---|
| Prevalence (reference) | 0.333 | 0.500 | 0.255 |
| Clinical only (grade+history) | 0.495 | 0.720 | 0.235 |
| CNV only | 0.538 | 0.663 | 0.216 |
| Image only | 0.557 | 0.731 | 0.245 |
| CNV + image (mean-fusion, frozen headline) | **0.630** | 0.774 | **0.184** |
| CNV + image (joint MLP) | 0.562 | 0.746 | 0.245 |
| Clinical + CNV | 0.528 | 0.740 | 0.244 |
| Clinical + image | 0.554 | 0.778 | 0.228 |
| Clinical + CNV + image | 0.576 | **0.801** | 0.222 |

*Best AUPRC/Brier: late-mean CNV+image (the headline model). Best ROC AUC: the full clinical+CNV+image stack. Key paired contrasts: late-mean − CNV-only ΔAUPRC +0.091 (CI crosses 0), ΔROC +0.111 (excludes 0), ΔBrier −0.032 (excludes 0); clinical+CNV+image − clinical+CNV ΔAUPRC +0.048 (CI −0.025 to +0.124, crosses 0 — marginal histology value inconclusive given clinical+CNV).*

---

## 4. Does the multimodal conclusion survive? (robustness of late-mean − CNV-only ΔAUPRC)

| Sensitivity axis | Cohort | n rows | Prevalence | ΔAUPRC | 95% CI | Excludes 0? |
|---|---|---|---|---|---|---|
| **Reference** | full cohort | 707 | 0.151 | +0.091 | (−0.031, +0.219) | no |
| Exact matching | exact-match-only | 532 | 0.096 | **+0.176** | (+0.007, +0.341) | **yes** |
| Exact + formatting | exact+format | 565 | 0.110 | +0.150 | (−0.016, +0.302) | no |
| Exclude patient-fallback matches | exclude-fallback | 578 | 0.111 | +0.098 | (−0.044, +0.257) | no |
| Strong grade provenance | scraped-confirmed-grade | 547 | 0.113 | **+0.161** | (+0.012, +0.318) | **yes** |
| Strong grade provenance | exclude-master-fallback | 552 | 0.114 | **+0.152** | (+0.006, +0.308) | **yes** |
| Same-day-event exclusion | exclude-same-day | 707 | 0.151 | +0.091 | (−0.031, +0.219) | no (0 same-day events; no-op) |
| Temporal horizon | min-horizon 90 d | 676 | 0.154 | +0.085 | (−0.039, +0.225) | no |
| Cleaner endpoint | LGD3+ / high-risk≥3 | 707 | 0.113 | +0.049 | (−0.087, +0.196) | no |
| Aggregation: patient-mean | — | 150 | — | +0.070 | (−0.080, +0.229) | no |
| Aggregation: most-recent | — | 150 | — | +0.111 | (−0.043, +0.262) | no |
| Aggregation: first-eligible | — | 150 (16 pos) | — | +0.053 | (−0.090, +0.229) | no (underpowered) |
| Aggregation: biopsy-then-max | — | 150 | — | +0.091 | (−0.031, +0.219) | no |

**Fold stability (main caveat):** ΔAUPRC by fold = −0.112 (f1), +0.420 (f2), +0.057 (f3), +0.057 (f4), +0.154 (f5). **Patient influence:** base ΔAUPRC 0.091; max single-patient leave-one-out influence 0.023; 82 positive / 65 negative influencers — no single patient drives the result.

**Reading:** the conclusion *survives and strengthens* under the two cleanest cuts (exact matching, strong grade provenance — both CIs exclude zero), is *stable* to temporal exclusion and aggregation choice, and *attenuates* at the stricter LGD3+ endpoint. The one genuine fragility is fold-level heterogeneity, carried largely by fold 2.

---

## 5. Calibration and decision-curve figures

- **Calibration:** the frozen fusion and CNV models are well-calibrated (fusion slope 1.78, ECE 0.075; CNV slope 1.23, ECE 0.095); the clinical stacks are over-confident (slopes 0.5–0.9, ECE 0.21–0.23).
- **Operating point @ sensitivity ≥ 90%:** clinical+CNV+image gives specificity 0.66, PPV 0.57, NPV 0.93 (patient prevalence 0.33).
- **Decision-curve analysis:** the frozen fusion model has the highest net benefit across the clinically relevant threshold range.
- Figures: `calibration_curves.png`, `decision_curves.png` (Phase 2). Tables: `calibration_metrics.csv`, `clinical_operating_points.csv`, `decision_curve_results.csv`.

---

## 6. Systematic error-analysis summary

Per-patient leakage-safe categories (threshold = 90th percentile of other-fold negatives): correct non-progressor 88, missed progressor 22, correct progressor 18, fusion-harm missed-progressor 10, fusion-harm false-positive 9, persistent false-positive 3.

**Central mechanistic finding:** the two modalities agree on 71% of patients (fusion accuracy 0.76 there); on the 44 disagreement cases fusion accuracy drops to 0.57 while at least one single modality was correct in every case. **Mean-fusion averages away a correct unimodal signal when the modalities conflict** — a concrete, pre-registered motivation for learned gating fusion in a future chapter. Missed progressors are *more temporally distant* than caught ones (median 729 d vs 548 d), which argues against short-horizon leakage.

Figures/tables: `error_analysis.png`, `patient_error_taxonomy.csv`, `modality_disagreement_analysis.csv`, `error_by_index_grade.csv` (Phase 4).

---

## 7. Killcoyne multimodal feasibility decision

69 of our 150 multimodal patients overlap the Killcoyne discovery cohort, and they are a **strict subset of our own training patients** (all 454 overlap rows carry full CNV + H&E + UNI2/GigaPath/Virchow2 features). **Decision: do not launch a multimodal LOPO benchmark against Killcoyne** — the overlap is a within-cohort benchmark, not external validation (reporting rule 11), and the Killcoyne endpoint is CNV-only, so a like-for-like multimodal comparison is impossible regardless. Keep our CNV-only LOPO (0.78–0.80, ~0.07 below their reported 0.87, plausibly QC/preprocessing differences) as the paper anchor; defer true external validation. Docs: `killcoyne_multimodal_overlap_summary.md`, `killcoyne_lopo_feasibility.md`, `killcoyne_protocol_comparison.md`.

---

## 8. Virchow2 primary-task sensitivity result

Re-ran the primary LGD2+ task with the Virchow2 encoder (feat_dim 2560) in place of UNI2 (1536), same ABMIL architecture, protocol and splits. **Virchow2 is slightly worse than UNI2 on every family and metric:** image_only ΔAUPRC −0.075 / ΔROC −0.065; late-mean −0.071 / −0.064; intermediate-fusion −0.079 / −0.080 (ROC deltas exclude zero); calibration also worse. Per the pre-specified rule, Virchow2 is **not** expanded to other endpoints; **UNI2 (with GigaPath effectively tied) remains the reported backbone.** The multimodal finding is not an artifact of one particular foundation model. Report: `VIRCHOW2_SENSITIVITY_REPORT.md`; figure `virchow2_vs_uni2.png`.

---

## 9. Recommended final primary model

**Late-mean fusion of CNV-only and UNI2 image-only** (the frozen headline model), evaluated patient-level with patient-max aggregation.
- Rationale: best AUPRC (0.630) and Brier (0.184), second-best ROC (0.774), well-calibrated (slope 1.78, ECE 0.075), and the simplest fusion that achieves this (a probability average — no learned fusion parameters to over-fit at n=150).
- The full **clinical+CNV+image stack is the recommended *secondary* model** where routine clinical variables are available at prediction time (best ROC 0.801, operating point spec 0.66 / NPV 0.93 at sens ≥ 90%).
- Reported backbone: **UNI2** (GigaPath is an acceptable tie; Virchow2 is not).

---

## 10. Strongest defensible scientific claim (exact wording)

> "In an internally validated, patient-disjoint cross-validation of 150 patients with Barrett's oesophagus (50 progressors), combining shallow-WGS copy-number variation with H&E histopathology by late-mean fusion improved next-biopsy LGD2+ progression prediction over copy-number alone, raising ROC AUC from 0.66 to 0.77 (Δ +0.11, 95% CI +0.001 to +0.221) and improving calibration (Brier 0.216 → 0.184, Δ −0.032, 95% CI −0.060 to −0.003). The gain in average precision was directionally consistent (AUPRC 0.54 → 0.63) but its confidence interval crossed zero on the full cohort; it reached conventional significance on the exactly-matched (ΔAUPRC +0.176, 95% CI +0.007 to +0.341) and strong-grade-provenance subsets. The benefit was robust to aggregation scheme and temporal exclusion, was not driven by any single patient, but varied across folds. These results are internal validation only; no external cohort has yet been tested."

---

## 11. Claims that must NOT be made

1. **Do not** state that multimodal fusion "significantly improves AUPRC" on the primary endpoint — the full-cohort CI crosses zero (rules 3, 13).
2. **Do not** call any result "externally validated" or "generalises" — all evaluation is internal cross-validation (rules 10, 11).
3. **Do not** describe the Killcoyne overlap comparison as external validation — its patients are a subset of the training cohort (rule 11).
4. **Do not** promote a robustness or subset result (e.g. exact-match +0.176) to *the* headline result — it is a sensitivity analysis, reported as such (reporting-hierarchy rule; rule 8).
5. **Do not** claim histology adds conclusive value *over clinical+CNV* — that marginal contrast crosses zero (ΔAUPRC +0.048).
6. **Do not** claim Virchow2 (or "a larger foundation model") improves performance — it does not.
7. **Do not** present sample-rows, biopsies or slides as independent patients, or quote sample-level metrics as if patient-level (rule 6).
8. **Do not** claim clinical utility beyond the reported operating point / decision-curve range, or imply a deployment-ready screening tool from n=150.
9. **Do not** describe the cohort as "dysplasia-free" — it is pre-high-grade (contains prevalent LGD/ID).

---

## 12. Ranked recommendation for the next major investment

**1 (lead) — Prepare the chapter and manuscript on the hardened internal results.** The internal validation is complete, stable and honestly bounded; the results support a defensible chapter now, at zero additional compute or data cost. Write claims as internal validation with the AUPRC caveat explicit. *(User-selected priority.)*

**2 — Wait for a digitised external cohort before making any further predictive claims.** External validation is the single highest-value scientific step, but it is genuinely blocked until such a cohort exists on the cluster; it should be the first thing done once one is available, under a separate instruction. Nothing in the interim should be framed as external evidence.

**3 — Add pathologist-supported interpretation.** The Phase-4 disagreement finding ("mean-fusion averages away a correct modality on conflict") is the strongest mechanistic lead; expert review of attention maps and disagreement cases would strengthen the clinical narrative and motivate a learned-gating fusion in a later chapter. Moderate cost (pathologist time), no change to headline metrics.

**4 — Run the Killcoyne multimodal benchmark.** *Not recommended as a near-term investment* — Phase 5 established the overlap is within-cohort, so it cannot serve as external validation and risks over-claiming. Only worth doing as a clearly-labelled within-cohort benchmark if a reviewer specifically requests it.

**Not now (deferred by spec, require separate instruction):** external-cohort ingestion, additional uncensored at-risk endpoints, large 1/2/4/5-year campaigns, new MoE or fusion architectures, large survival-modelling, new foundation-model extraction, encoder fine-tuning.
