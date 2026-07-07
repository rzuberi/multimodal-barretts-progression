# LGD2+ Histology Dry-Run Pair Comparison

Both dry-run cases completed structurally valid ABMIL histology interpretation outputs.

| item | A true-positive early | B false-negative |
| --- | --- | --- |
| case_id | `A_true_positive_early_02` | `B_false_negative_07` |
| patient_id | `PR1/BED/060` | `AHM1146` |
| true_label | `1` | `1` |
| image_probability | `0.964` | `0.104` |
| fusion_probability | `0.993` | `0.285` |
| tiles scored | `256` | `256` |
| top-score range | `0.04553629; 0.044974424; 0.032111093; 0.02829201; 0.026603399` | `0.01266778; 0.011998858; 0.011351064; 0.0109072095; 0.010797691` |
| top patches exist | `True` | `True` |
| heatmap/overlay exist | `True` | `True` |
| ready for manual review | `READY_FOR_MANUAL_REVIEW` | `READY_FOR_MANUAL_REVIEW` |

## Interpretation Readiness

- Row 0 is a high-confidence true-positive early case and has complete top-patch, tile-score, and heatmap/overlay outputs.
- Row 1 is a false-negative progressor case and has complete top-patch, tile-score, and heatmap/overlay outputs.
- Both are ready for manual visual review; this does not by itself validate biological interpretation.

## Recommendation

Inspect these two external visual outputs manually first. If they look correct, it is reasonable to run the remaining 6 selected cases with the same environment and external output root.
