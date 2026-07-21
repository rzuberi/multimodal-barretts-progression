# Multitask + MoE results summary (20260721)

Patient-level, nested 5-fold patient-disjoint CV, on the frozen 707-row / 150-patient
pre-event cohort (identical rows across tasks → paired comparison). Backbones: UNI2 +
GigaPath. Full model set per task: cnv_only, image_only, early/intermediate/coattention
fusion, end-to-end MoE, derived late_mean / late_stack_logit. No gaps.

## Cross-task detection grid — ROC AUC (specificity@90%-sensitivity), best backbone

| task | image_only | cnv_only | moe | late_mean | intermediate_fusion |
| --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.73 (0.42) | 0.82 (0.58) | 0.78 (0.47) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.84 (0.57) | 0.89 (0.78) | 0.81 (0.36) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.73 (0.34) | 0.77 (0.36) | 0.72 (0.46) |

## Findings
1. **Task choice matters.** `at_risk_3y` is the strongest endpoint (late_mean ROC AUC
   0.89) and clearly beats next-biopsy progression (0.77) — reproducing the March deck's
   observation that horizon/ever-progression framings carry cleaner signal than
   next-biopsy, now under the stricter patient-level nested-CV protocol.
2. **Late-mean fusion wins every task** on AUPRC and ROC AUC. Multimodal fusion helps.
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
