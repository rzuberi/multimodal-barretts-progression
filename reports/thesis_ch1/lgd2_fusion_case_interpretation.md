# LGD2+ Fusion Case Interpretation

| case_id | true | cnv | image | fusion | label | sentence |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `A_true_positive_early_02` | `1` | `0.448` | `0.964` | `0.993` | `fusion_rescues_cnv` | A_true_positive_early_02 is a A_true_positive_early case with true label 1. CNV/image/fusion predictions are 0/1/1; fusion label: fusion_rescues_cnv. |
| `B_false_negative_07` | `1` | `0.527` | `0.104` | `0.285` | `fusion_hurts` | B_false_negative_07 is a B_false_negative case with true label 1. CNV/image/fusion predictions are 1/0/0; fusion label: fusion_hurts. |
| `E_cnv_rescue_19` | `1` | `0.529` | `0.462` | `0.947` | `fusion_rescues_image` | E_cnv_rescue_19 is a E_cnv_rescue case with true label 1. CNV/image/fusion predictions are 1/0/1; fusion label: fusion_rescues_image. |

Threshold: 0.5. Labels are probability-level summaries and should be interpreted with the histology/CNV panels.
