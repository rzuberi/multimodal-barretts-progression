# Killcoyne protocol comparison (Phase 5)

| Dimension | Killcoyne paper (discovery) | Local multimodal cohort |
|---|---|---|
| Modality | CNV (shallow WGS) only | CNV + H&E histology |
| Evaluation | Leave-one-patient-out | 5-fold patient-disjoint CV |
| Cohort | 88 patients / 777 samples | 150 patients / 707 eligible rows |
| Endpoint | Progressor status (P/NP) | NextBiopsyProgression_LGD2plus |
| Published metric | LOPO AUC 0.87 (50 kb) | local CNV LOPO 0.78–0.80 |
| Overlap | — | 69/150 local patients are Killcoyne-discovery PSIDs (subset) |

**Comparability caveats:**
- Different evaluation protocol (LOPO vs 5-fold) — LOPO is higher-variance at this n; 5-fold preferred locally.
- Different preprocessing/QC (leading explanation for the 0.78 vs 0.87 CNV gap).
- No histology in Killcoyne → no like-for-like multimodal comparison possible.
- Overlap patients are a subset of the local training cohort → not independent.

**Valid comparisons:** (a) local CNV-only LOPO vs paper CNV LOPO (with QC-gap caveat); (b) local multimodal models on the overlap subset as an internal sensitivity analysis. **Invalid:** describing any Killcoyne-subset result as external validation.
