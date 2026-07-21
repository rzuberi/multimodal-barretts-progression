# Multitask + MoE results summary (20260721)

Patient-level, nested 5-fold patient-disjoint CV, on the frozen 707-row / 150-patient
pre-event cohort (identical rows across tasks → paired comparison). Backbones: UNI2 +
GigaPath. Full model set per task: cnv_only, image_only, early/intermediate/coattention
fusion, end-to-end MoE, derived late_mean / late_stack_logit. No gaps.

## Cross-task detection grid — ROC AUC (specificity@90%-sensitivity), best backbone

Full family set (no gaps). Final column = best family per task ranked by AUPRC (the
primary metric; breaks ROC ties). See `cross_task_grid.md` for the reproducible source.

| task | image_only | cnv_only | early_fusion | intermediate_fusion | coattention_fusion | moe | late_mean | late_stack_logit | best_by_auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.82 (0.37) | 0.78 (0.47) | 0.77 (0.50) | 0.73 (0.42) | 0.82 (0.58) | 0.80 (0.51) | early_fusion (0.575) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.85 (0.52) | 0.81 (0.36) | 0.84 (0.54) | 0.84 (0.57) | 0.89 (0.78) | 0.87 (0.71) | late_mean (0.898) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.76 (0.41) | 0.72 (0.46) | 0.75 (0.49) | 0.73 (0.34) | 0.77 (0.36) | 0.74 (0.39) | late_mean (0.625) |

## Findings
1. **Task choice matters.** `at_risk_3y` is the strongest endpoint (late_mean ROC AUC
   0.89) and clearly beats next-biopsy progression (0.77) — reproducing the March deck's
   observation that horizon/ever-progression framings carry cleaner signal than
   next-biopsy, now under the stricter patient-level nested-CV protocol.
2. **Multimodal fusion wins on every task**, but the winning *fusion variant* is not
   always late-mean. Late-mean is best (or ROC-tied) on `at_risk_3y` and
   `next_biopsy_progression`; on `ever_progress` **early_fusion (gigapath) takes the top
   AUPRC** (0.575 vs late-mean 0.552) and ties late-mean on ROC AUC (both 0.82). So the
   honest read is "fusion beats either single modality on all three tasks; late-mean is the
   most consistent fusion but early_fusion edges it on ever_progress."
3. **End-to-end MoE lands mid-pack** (ROC AUC 0.73 / 0.84 / 0.73), not beating late-mean.
   Consistent with the Chapter-2 small-n finding: a jointly-trained gate+experts is
   over-parameterised at ~150 patients. Its value here is interpretability, not accuracy.
4. **MoE routing is interpretable.** The gate routes the majority (59–69%) of biopsies to
   the multimodal expert and higher-risk biopsies preferentially there (at_risk_3y:
   multimodal progressor-rate 0.51 vs image-expert 0.35); the CNV-only expert is barely
   used. See each `train/<backbone>/oof/moe_routing_report.md`.

## Caveats
- Numbers are LOWER than the March deck (AUC 0.81–0.88) because that used biopsy-level
  scoring with per-model operating points; this is patient-level nested-CV. The grid above
  is the honest apples-to-apples read.
- `at_risk_3y` uses the deck's `AtRisk_3y` label as-is; 395/707 rows are negatives with
  <3y recorded follow-up (see each task's `task_cohort_audit.json`). Treat `at_risk_3y`
  results as optimistic pending a censored re-run.
- Internal cross-validation only; no external validation.

## Artifacts (external, not in Git)
`analysis/multitask_moe_20260721/<task>/train/<backbone>/oof/` — per-family OOF predictions,
completeness manifests, MoE routing reports. Result tables committed under
`multitask_moe/reports/`.
