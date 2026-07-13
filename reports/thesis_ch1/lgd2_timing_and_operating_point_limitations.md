# LGD2+ Timing and Operating-Point Limitations

Concise limitations note for the early-prediction sensitivity analysis and the
fixed operating points. The locked filters and existing outputs are unchanged.

## Early-prediction filter
- The early-prediction-only analysis removes rows with `DaysFromCurrentToEvent == 0`.
- Rows with **missing** timing values are RETAINED by the current locked filter.
- Therefore this is an **"at-event excluded"** analysis, NOT a strict known-lead-time
  cohort. It reduces current-event inflation but does not guarantee a confirmed
  temporal gap between the biopsy and the event for every retained positive.
- A future strict lead-time analysis would require confirmed temporal ordering or a
  positive `DaysFromCurrentToEvent` for progressors.

## Fixed operating points
- The fixed operating-point columns (sensitivity_at_90_specificity, etc.) choose
  thresholds from the pooled evaluated OOF predictions. These are **exploratory /
  post-hoc** estimates and are optimistic relative to a prospectively fixed threshold.
- Threshold-0.5 metrics are reported alongside and are not affected.

## Remaining work
- **Cross-fitted thresholding is not yet implemented.** A leakage-safe version would,
  for each held-out fold, choose the threshold from the other OOF folds, apply it only
  to the held-out fold, and pool held-out confusion counts (preserving
  patient-disjointness), reported separately from the post-hoc operating points. This
  is deferred, not done.
