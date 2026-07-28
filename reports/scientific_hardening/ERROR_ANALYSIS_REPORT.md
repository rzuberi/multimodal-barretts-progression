# Error Analysis Report (Phase 4)

---

## Phase 4 — Systematic error analysis  ✅ COMPLETE

**Method:** patient-level (patient-max) OOF predictions. Binary decisions use a **leakage-safe per-fold threshold** = the 90th percentile of *other-fold* negative predictions (a spec≈0.90 proxy that never sees the test fold). Categories are pre-specified from the (fusion-correct, cnv-correct, image-correct) triple — no hand-picking of cases.

### Error taxonomy (n=150; 50 progressors)
| Category | n |
|---|---|
| Correct progressor (fusion) | 18 |
| Fusion-harm missed progressor (a modality was right, fusion wrong) | 10 |
| Missed progressor (all modalities wrong) | 22 |
| Correct non-progressor | 88 |
| Fusion-harm false positive | 9 |
| Persistent false positive (all wrong) | 3 |

### Modality agreement & the central mechanistic finding
- Modalities agree on **71%** of patients (106/150).
- **When they agree**, fusion is accurate (0.76). **When they disagree** (44 patients), fusion accuracy falls to **0.57**.
- **Late-mean fusion averages away a correct unimodal signal on conflict.** On the 44 disagreement cases, at least one single modality was correct in every case (oracle upper bound 1.00 — this is definitional, an *achievable* modality-selector would be lower), yet mean-fusion recovers only 0.57. Fusion support breakdown: 81 all-agree, 21 image-carried, 4 CNV-carried, 44 fusion-wrong. **This is the strongest mechanistic motivation for a learned gating/attention fusion** (deferred by scope), and explains why the AUPRC benefit is modest: mean-fusion wins on the easy concordant cases and loses ground on conflicts.
- Strong-confident unimodal signal lost by fusion: **3** patients.

### False negatives are distant, not imminent (reassuring)
- Missed progressors (32) have a **longer** median time-to-event (**729 d**) than caught progressors (18; 548 d). The model catches imminent progression and misses distant progression — clinically sensible, and argues against a short-horizon-leakage explanation of the positive signal.

### False positives concentrate in NDBE
- Of the false positives, index-grade distribution: {'NDBE': 7, 'LGD': 3, 'ID': 2} — mostly non-dysplastic Barrett's flagged as high-risk that did not progress in-window.

### Error category by index grade
index_grade  correct_nonprogressor  correct_progressor  fusion_harm_false_positive  fusion_harm_missed_progressor  missed_progressor_all  persistent_false_positive
         ID                      5                   3                           2                              1                      4                          0
        LGD                      5                   7                           1                              4                      8                          2
       NDBE                     78                   8                           6                              5                     10                          1

### Deliverables
`error_analysis_summary.csv`, `error_by_index_grade.csv`, `modality_disagreement_analysis.csv`, `error_analysis_summary.png/.pdf`. Row-level `patient_error_taxonomy.csv` (patient ids) kept on the cluster.

**Phase 4 gate: complete.** Key exploratory finding: mean-fusion's ceiling is set by its behaviour on modality-disagreement cases — a concrete, pre-registered motivation for learned fusion once sample size permits.
