# LGD2+ Histology Case Category Comparison

All 8 selected LGD2+ cases generated structurally complete ABMIL histology outputs and are ready for manual visual review.

| category | case_id | image_prob | fusion_prob | tiles | top_score_range | complete_outputs | figure-use note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `A_true_positive_early` | `A_true_positive_early_01` | `0.954` | `0.993` | `256` | `0.0119531; 0.011362263; 0.011329324; 0.011317418; 0.011065992` | `READY_FOR_MANUAL_REVIEW` | weak/narrow attention score range; inspect before final figure use |
| `A_true_positive_early` | `A_true_positive_early_02` | `0.964` | `0.993` | `256` | `0.04553629; 0.044974424; 0.032111093; 0.02829201; 0.026603399` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |
| `B_false_negative` | `B_false_negative_07` | `0.104` | `0.285` | `256` | `0.01266778; 0.011998858; 0.011351064; 0.0109072095; 0.010797691` | `READY_FOR_MANUAL_REVIEW` | weak/narrow attention score range; inspect before final figure use |
| `C_false_positive` | `C_false_positive_12` | `0.937` | `0.947` | `256` | `0.031084266; 0.02795765; 0.027039673; 0.026914874; 0.026739066` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |
| `E_cnv_rescue` | `E_cnv_rescue_19` | `0.462` | `0.947` | `256` | `0.04644224; 0.039828185; 0.034539554; 0.026262792; 0.02582529` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |
| `F_histology_rescue` | `F_histology_rescue_24` | `0.956` | `0.925` | `256` | `0.04520655; 0.041244384; 0.03707991; 0.033216745; 0.023280129` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |
| `G_fusion_hurt` | `G_fusion_hurt_26` | `0.860` | `0.375` | `256` | `0.031467002; 0.027484288; 0.02278748; 0.02139542; 0.020030105` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |
| `I_modality_disagreement` | `I_modality_disagreement_37` | `0.975` | `0.939` | `256` | `0.057571203; 0.047479805; 0.043931946; 0.04367443; 0.043125942` | `READY_FOR_MANUAL_REVIEW` | manual review candidate |

## Structural Comparison

- True-positive early cases: both generated complete outputs.
- False-negative case: generated complete outputs with a weaker top-score range than the high-confidence true-positive examples.
- False-positive, CNV-rescue, histology-rescue, fusion-hurt, and modality-disagreement cases all generated complete outputs.
- Do not make biological claims from this table alone; use it to prioritise manual visual figure review.

## Recommendation

Manually inspect all 8 external visual outputs. Cases with narrow score ranges may be less visually compelling for final thesis figures even if structurally valid.
