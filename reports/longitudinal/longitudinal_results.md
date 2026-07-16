# Longitudinal (landmarking) model — results note

**Question.** Does adding a patient's biopsy *history* to the multimodal model
improve prediction of the Chapter 1 endpoint (`NextBiopsyProgression_LGD2plus`)?

**Design.** Landmarking: each biopsy row is one landmark, encoded together with
that patient's biopsy history-to-date (attention-MIL over UNI2 tile bags + a CNV
branch per biopsy, aggregated over the ordered sequence by a GRU or a learned
attention pooler, with an inter-biopsy time-gap feature). Trained from scratch
under the identical nested 5-fold patient-disjoint CV, inner-selection on
patient-max AUPRC, and validation-derived threshold as the frozen Chapter 1
baselines. The endpoint and the 707 biopsy rows are identical to the baselines,
so this is a paired comparison over the same 150 patients.

**Run.** 5 outer folds, GPU (H200), commit `952b678`. 707 landmarks total
(174/130/138/121/144 per fold), exactly matching the frozen cohort's 707 rows.
Selected configs varied by fold (attn_h256 ×2, gru_h256 ×2, gru_h128 ×1),
final epochs 4–14 — early stopping kept the from-scratch temporal model shallow.

## Patient-level metrics (patient-max aggregation, n=150)

| Model | AUPRC | ROC AUC | Brier |
|---|---|---|---|
| **Longitudinal (+history)** | 0.575 | 0.717 | 0.225 |
| CNV only | 0.538 | 0.663 | 0.216 |
| H&E (image) only | 0.557 | 0.731 | 0.245 |
| Intermediate fusion | 0.567 | 0.741 | 0.224 |
| **Late-mean fusion (headline)** | **0.630** | **0.774** | **0.184** |

## Paired deltas (longitudinal − baseline), 95% bootstrap CI (2000 resamples)

| Baseline | Metric | Δ | 95% CI | CI excludes 0 |
|---|---|---|---|---|
| CNV only | AUPRC | +0.037 | (−0.092, +0.164) | no |
| CNV only | ROC AUC | +0.054 | (−0.058, +0.168) | no |
| CNV only | Brier | +0.009 | (−0.041, +0.063) | no |
| Late-mean | AUPRC | −0.054 | (−0.154, +0.038) | no |
| Late-mean | ROC AUC | −0.057 | (−0.129, +0.014) | no |
| Late-mean | Brier | +0.041 | (+0.007, +0.078) | **yes (late-mean better)** |
| Intermediate fusion | AUPRC | +0.008 | (−0.091, +0.095) | no |

## Interpretation

**The longitudinal model does not beat the frozen late-mean fusion baseline.**
On the headline metric it is lower (AUPRC 0.575 vs 0.630; ROC AUC 0.717 vs
0.774), and the only paired difference whose CI excludes zero is Brier, where it
is *worse*-calibrated than late-mean (+0.041, CI 0.007–0.078). Against the
weaker single-timepoint arms the point estimates favour history (e.g. +0.037
AUPRC and +0.054 ROC AUC over CNV-only), but every one of those CIs includes
zero, so none is conclusive at n=150.

**Why this is a defensible, informative negative.** With 150 patients / 50
progressors, a from-scratch temporal encoder is heavily over-parameterised — the
selected models stopped after 4–14 epochs, and the shared per-biopsy encoder is
trained on landmark rows that are strongly correlated within patient. The
late-mean baseline, by contrast, reuses independently-tuned unimodal heads and a
parameter-free fusion, which is hard to beat in this small-n regime. The honest
read is that **history, encoded this way and trained end-to-end from scratch, is
not worth its parameters here** — consistent with the Chapter 1 finding that the
multimodal benefit itself is modest and not conclusive on AUPRC.

**What would change the verdict** (not run here): (1) initialise the per-biopsy
encoder from the frozen single-timepoint fusion weights and only learn the
temporal layer (transfer, far fewer free parameters); (2) a fixed-horizon /
time-to-event framing that uses the `AtRisk_*` fields rather than next-biopsy;
(3) a simpler history summary (e.g. last biopsy + count/trend features) fused
late, rather than a learned sequence encoder.

## Artifacts
- `reports/longitudinal/longitudinal_vs_baselines_patient_metrics.csv`
- `reports/longitudinal/longitudinal_paired_deltas.csv`
- `reports/longitudinal/longitudinal_comparison.png`
- Runners: `scripts/27_run_longitudinal_outer_fold.py`, `scripts/28_launch_longitudinal_rerun.sh`, `scripts/29_evaluate_longitudinal.py`
- Model/training code: `src/barrett/models/longitudinal.py`, `src/barrett/training/longitudinal.py` (+ `tests/test_longitudinal.py`)
