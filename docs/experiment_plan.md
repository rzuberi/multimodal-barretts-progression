# Experiment Plan

## Primary Aim

Build a coherent Chapter 1 result set for multimodal Barrett's progression prediction using histopathology and CNV.

## Minimum Final Result Set

1. Endpoint decision: LGD2+ or LGD3+ future progression.
2. Final cohort table outside Git, with early-prediction samples only.
3. Patient-level evaluation:
   - preferred: LOPO;
   - fallback: patient-disjoint 5-fold CV with justification.
4. Model families:
   - CNV-only baseline;
   - image-only MIL;
   - early fusion;
   - intermediate/co-attention fusion;
   - best selected foundation-model fusion.
5. Clinical detection metrics:
   - ROC AUC;
   - AUPRC;
   - sensitivity;
   - specificity;
   - PPV;
   - NPV;
   - balanced accuracy;
   - Brier/calibration;
   - sensitivity at fixed specificity;
   - specificity at fixed sensitivity;
   - progressors detected and missed;
   - false positives per detected progressor;
   - patient-level confusion matrix.
6. Biological interpretation:
   - histology top patches or attention maps;
   - CNV region/gene rankings;
   - multimodal dependence/rescue/hurt cases.

## Existing Results To Treat As Usable Starting Points

- LGD3+ canonical 5-fold CV.
- LGD3+ patient/biopsy aggregation.
- LGD3+ distance-to-progression analysis.
- LGD3+ clinician/explainability figures.
- CNV-only Killcoyne-style LOPO baselines.
- LGD2+ 5-fold candidate campaigns.

## Missing Results

- Full canonical LOPO for image-only and fusion models.
- LGD2+ LOPO if LGD2+ becomes primary.
- Early-prediction-only recomputation excluding at-event rows.
- Patient-level clinical detection tables with confusion counts.
- LGD2+ interpretation figures.

## Obsolete Or Developmental Results

- Older 50-fold result families.
- Smoke runs.
- Result folders with no saved prediction files.
- LGD3+ headline results if LGD2+ is chosen as the main endpoint.
