# Killcoyne LOPO multimodal feasibility & protocol decision (Phase 5.2–5.4)

## Is this independent validation? **NO.**
The 69 overlapping patients are a **strict subset of the 150-patient local multimodal cohort** on which the frozen image/fusion models were trained (patient-disjoint 5-fold CV). Any evaluation of those frozen models on the Killcoyne subset would re-use patients the base models have already seen → **it is a within-cohort benchmark, not external validation** (spec rule #11). Calling it external validation would be incorrect.

## Would LOPO retraining help? Only marginally, and it does not buy independence.
- A fresh multimodal LOPO campaign on the 69/27-positive overlap is technically feasible (all embeddings present) but the patients still overlap the local cohort, so it remains internal.
- **27 positive patients across LOPO** is statistically fragile (worse than the current 5-fold with 50 positives). Per rule: 5-fold patient-disjoint CV is more stable than LOPO here.
- The published Killcoyne headline is a **CNV-only** LOPO result; there is no histology in their cohort, so a *like-for-like* multimodal comparison to the paper is impossible regardless.

## Must the 0.780–0.801 vs 0.87 CNV gap be reconciled first? Yes, before any paper comparison.
The local CNV LOPO reproduction (0.780–0.801) sits ~0.07–0.09 below the paper's reported 0.87 (leading hypothesis: QC-mode / preprocessing differences). Any claim benchmarked against Killcoyne's number must first reconcile this gap; it does not block an internal multimodal benchmark that compares only local models to each other.

## RECOMMENDATION — Option 3 (with a defined internal use), NOT Option 1
**Do NOT launch a multimodal LOPO GPU campaign.** Recommended:
1. **Use the Killcoyne overlap only as a labelled internal benchmark subset** — report the existing frozen multimodal models' performance on the 69-patient / 27-positive overlap as a *sensitivity analysis* (reusing existing OOF where the fold assignment already isolates each patient), clearly labelled "within-cohort, not external validation."
2. **Keep the CNV-only Killcoyne LOPO (0.78–0.80) as the paper-comparison anchor**, with the documented gap to 0.87.
3. **Defer any external-validation claim** until a genuinely independent digitised cohort is available (spec explicitly defers this).

Rationale: the overlap is a subset (no independence), positive count is small (27), and the paper's endpoint is CNV-only — so full multimodal LOPO retraining spends GPU budget without producing an independent or paper-comparable result. The scientifically honest move is a labelled internal sensitivity analysis, not a validation claim.

## Deliverables
`killcoyne_lopo_feasibility.md` (this file), `killcoyne_protocol_comparison.md`.
