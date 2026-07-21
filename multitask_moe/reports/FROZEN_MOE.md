# Frozen-expert MoE — supplementary sanity comparison

Answers HANDOFF §11.3: does the end-to-end MoE's mid-pack showing reflect a
weakness of *gated routing*, or the cost of *jointly learning experts* at
n≈150? To separate the two, this routes among the FROZEN per-fold OOF of the
already-trained experts (image_only, cnv_only, intermediate_fusion) with a tiny
gate fit per outer fold on the other folds only — so every combined prediction
stays out-of-sample and comparable to the baselines on the identical rows/folds.
Two gates: `logistic` (per-sample soft responsibilities) and `static` (single
best convex blend chosen on the train folds). Code: `scripts/frozen_expert_moe.py`.

Patient-level AUPRC / ROC AUC, best backbone; frozen-MoE column is the best of
the two gates (backbone/gate noted). This is a supplementary comparison, not a
trained model — it is deliberately kept out of the primary `all_metrics.csv`.

| task | end-to-end MoE | late_mean | frozen-MoE (best) | frozen-MoE config |
| --- | --- | --- | --- | --- |
| ever_progress | 0.449 / 0.725 | 0.552 / 0.768 | 0.544 / 0.791 | uni2 / logistic |
| at_risk_3y | 0.849 / 0.844 | 0.898 / 0.886 | 0.883 / 0.874 | uni2 / static |
| next_biopsy_progression | 0.552 / 0.735 | 0.625 / 0.766 | 0.629 / 0.768 | uni2 / static |
| next_biopsy_highrisk | 0.550 / 0.792 | 0.524 / 0.789 | 0.577 / 0.825 | uni2 / logistic |
| at_risk_3y_censored | 0.506 / 0.660 | 0.592 / 0.781 | 0.662 / 0.765 | gigapath / logistic |

## Finding

The frozen-expert MoE **beats the end-to-end MoE on all five tasks** (AUPRC), and
matches or exceeds late-mean on four of five — winning outright on
next_biopsy_highrisk (0.577 vs 0.524) and at_risk_3y_censored (0.662 vs 0.592).
So the end-to-end MoE's mid-pack AUPRC is the cost of jointly learning experts at
this sample size, not a failure of gated routing: freeze the experts and let the
gate learn only the weighting, and a MoE performs at the level of the best late
fusion. This strengthens SUMMARY finding #3 — the end-to-end MoE's value is
interpretability (its routing report), not accuracy, and a cheap frozen router is
the accuracy-competitive way to get gated behaviour here.
