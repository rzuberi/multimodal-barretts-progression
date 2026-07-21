# Multitask + MoE results summary (20260721)

Patient-level, nested 5-fold patient-disjoint CV, on the frozen 707-row / 150-patient
pre-event cohort (identical rows across the first three tasks → paired comparison).
Backbones: UNI2 + GigaPath. Full model set per task: cnv_only, image_only,
early/intermediate/coattention fusion, end-to-end MoE, derived late_mean /
late_stack_logit. No gaps.

Five tasks: the three original endpoints plus two added here — `next_biopsy_highrisk`
(4th deck task, `NextBiopsyHighRisk_ge3`, 707 rows / 36 positive patients) and
`at_risk_3y_censored` (the HONEST 3-year at-risk endpoint; see finding #5 and caveats).
A frozen-expert MoE sanity comparison is reported separately in `FROZEN_MOE.md`.

## Cross-task detection grid — ROC AUC (specificity@90%-sensitivity), best backbone

Full family set (no gaps). Final column = best family per task ranked by AUPRC (the
primary metric; breaks ROC ties). See `cross_task_grid.md` for the reproducible source.

| task | image_only | cnv_only | early_fusion | intermediate_fusion | coattention_fusion | moe | late_mean | late_stack_logit | best_by_auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.82 (0.37) | 0.78 (0.47) | 0.77 (0.50) | 0.73 (0.42) | 0.82 (0.58) | 0.80 (0.51) | early_fusion (0.575) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.85 (0.52) | 0.81 (0.36) | 0.84 (0.54) | 0.84 (0.57) | 0.89 (0.78) | 0.87 (0.71) | late_mean (0.898) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.76 (0.41) | 0.72 (0.46) | 0.75 (0.49) | 0.73 (0.34) | 0.77 (0.36) | 0.74 (0.39) | late_mean (0.625) |
| next_biopsy_highrisk | 0.76 (0.30) | 0.76 (0.56) | 0.84 (0.55) | 0.82 (0.61) | 0.81 (0.53) | 0.79 (0.50) | 0.79 (0.38) | 0.75 (0.30) | early_fusion (0.613) |
| at_risk_3y_censored | 0.76 (0.25) | 0.72 (0.40) | 0.73 (0.27) | 0.73 (0.21) | 0.63 (0.19) | 0.66 (0.04) | 0.78 (0.48) | 0.77 (0.40) | intermediate_fusion (0.682) |

(`next_biopsy_highrisk` and `at_risk_3y_censored` use their own cohorts, so they are NOT
row-matched to the first three tasks or to each other — read them as standalone, not as
paired contrasts against the other rows.)

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
   The frozen-expert MoE (`FROZEN_MOE.md`) isolates the cause: routing among the *frozen*
   trained experts beats the end-to-end MoE on all five tasks and matches/exceeds late-mean
   on four — so the mid-pack result is the cost of jointly *learning* experts at this n,
   not a weakness of gated routing.
4. **MoE routing is interpretable.** The gate routes the majority (59–69%) of biopsies to
   the multimodal expert and higher-risk biopsies preferentially there (at_risk_3y:
   multimodal progressor-rate 0.51 vs image-expert 0.35); the CNV-only expert is barely
   used. See each `train/<backbone>/oof/moe_routing_report.md`.
5. **Honest 3-year at-risk costs ~0.11 ROC AUC.** The original `at_risk_3y` used the deck's
   precomputed label, whose "negative" class is entirely under-followed biopsies (every
   AtRisk_3y=0 row has <3y follow-up) — inflating performance. `at_risk_3y_censored`
   redefines the label from event timing + observed follow-up: positive = event within 3y,
   negative = confirmed event-free THROUGH 3y (77 patients, 25 positive; 404 under-followed
   biopsies censored out). Best model drops from ROC 0.89 (optimistic) to **0.78**
   (intermediate_fusion AUPRC 0.682). Fusion still beats single modalities (late_mean vs
   cnv_only ΔAUPRC +0.126) but CIs cross zero at this smaller n. Use the censored numbers.
6. **4th task (next_biopsy_highrisk) is early-fusion's strongest endpoint.** early_fusion
   (uni2) tops it at AUPRC 0.613 / ROC 0.832 — the highest early-fusion result across all
   tasks — with fusion clearly beating single modalities.

## Caveats
- Numbers are LOWER than the March deck (AUC 0.81–0.88) because that used biopsy-level
  scoring with per-model operating points; this is patient-level nested-CV. The grid above
  is the honest apples-to-apples read.
- `at_risk_3y` (the original row) uses the deck's `AtRisk_3y` label as-is, whose negatives
  are all under-followed (<3y) biopsies — it is OPTIMISTIC and kept only for continuity with
  the deck. `at_risk_3y_censored` is the honest version (finding #5); prefer it.
- Internal cross-validation only; no external validation.

## Artifacts (external, not in Git)
`analysis/multitask_moe_20260721/<task>/train/<backbone>/oof/` — per-family OOF predictions,
completeness manifests, MoE routing reports. Result tables committed under
`multitask_moe/reports/`.
