# Threat Model and Failure Modes

## Deployment context assumptions (generic, non-PHI)
- A model output is consumed as a decision-support signal, not an autonomous diagnosis.
- Inputs are histopathology-derived image features and CNV-derived tabular signals processed through the documented pipelines.
- Deployment candidates may differ from snapshot conditions (`all_samples`, `exclude_hgd_imc`, `exclude_lgd_hgd_imc`).
- Evaluation claims in this repo are aggregate, retrospective, and fold-based.

## Threat model: what can go wrong
- **False reassurance (false negatives):** progressor-risk cases may be undercalled, delaying escalation.
- **False alarms (false positives):** overcalling risk can drive unnecessary surveillance or interventions.
- **Distribution shift:** scanner/site/protocol/population changes can break fold-era performance assumptions.
- **Demographic or clinical confounding:** latent covariates may spuriously drive score separability.
- **Site/process artifacts:** non-biological cues can be learned as shortcuts in image or multimodal branches.
- **Modality instability:** one modality may dominate and mask failures in the other (multimodal collapse).
- **Threshold fragility:** acceptable AUC may still map to unsafe sensitivity/specificity in operational settings.

## Testing and mitigations currently in scope
- Canonical label governance: progression uses LGD3plus definition in this campaign family.
- Cross-validation policy locked to `rep=1`, `folds=1..5` with patient-disjoint fold construction.
- Condition-stratified evaluations (`all_samples` and exclusion conditions) expose some sensitivity to cohort filtering.
- Derived fusion stackers are fold-safe (trained on non-heldout folds only) to reduce optimistic leakage.
- Coverage auditing tracks trainable + derived outputs and reports blocked/missing combinations.

## What is not yet done (high-priority gaps)
- External multi-site validation outside the current campaign snapshot.
- Prospective/temporal evaluation in a true forward-looking setting.
- Full calibration program (e.g., calibration curves, recalibration protocols, clinical threshold tuning).
- Decision-curve / net-benefit analysis for clinical actionability.
- Subgroup fairness/robustness analyses (demographic and acquisition strata).
- Formal sensitivity analyses for missing labels/censoring assumptions.

## Safety interpretation guidance
- Treat leaderboard differences as hypothesis-generating, not deployment-ready evidence.
- Require external and prospective checks before any high-stakes use.
- Prefer conservative operating points and explicit uncertainty communication in downstream workflows.
