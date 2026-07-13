# Lgd2 Final Pre Event Cross Fitted Operating Points

| model_family | outer_fold | threshold_method | threshold | validation_achieved_specificity | validation_fallback | n_patients | tp | fp | tn | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cnv_only | 1 | inner_validation_target_90_specificity | 0.334 | 0.900 | False | 30 | 4 | 4 | 16 | 6 |
| cnv_only | 1 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| cnv_only | 2 | inner_validation_target_90_specificity | 0.345 | 0.912 | False | 30 | 1 | 2 | 18 | 9 |
| cnv_only | 2 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| cnv_only | 3 | inner_validation_target_90_specificity | 0.314 | 0.912 | False | 30 | 4 | 1 | 19 | 6 |
| cnv_only | 3 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| cnv_only | 4 | inner_validation_target_90_specificity | 0.323 | 0.900 | False | 30 | 3 | 1 | 19 | 7 |
| cnv_only | 4 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| cnv_only | 5 | inner_validation_target_90_specificity | 0.295 | 0.900 | False | 30 | 2 | 2 | 18 | 8 |
| cnv_only | 5 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| cnv_only | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 14 | 10 | 90 | 36 |
| cnv_only | POOLED | default_0p5 | 0.500 |  | False | 150 | 0 | 0 | 100 | 50 |
| image_only | 1 | inner_validation_target_90_specificity | 0.610 | 0.900 | False | 30 | 4 | 10 | 10 | 6 |
| image_only | 1 | default_0p5 | 0.500 |  | False | 30 | 6 | 11 | 9 | 4 |
| image_only | 2 | inner_validation_target_90_specificity | 0.609 | 0.900 | False | 30 | 6 | 2 | 18 | 4 |
| image_only | 2 | default_0p5 | 0.500 |  | False | 30 | 7 | 5 | 15 | 3 |
| image_only | 3 | inner_validation_target_90_specificity | 0.622 | 0.925 | False | 30 | 9 | 12 | 8 | 1 |
| image_only | 3 | default_0p5 | 0.500 |  | False | 30 | 9 | 12 | 8 | 1 |
| image_only | 4 | inner_validation_target_90_specificity | 0.691 | 0.925 | False | 30 | 5 | 1 | 19 | 5 |
| image_only | 4 | default_0p5 | 0.500 |  | False | 30 | 6 | 6 | 14 | 4 |
| image_only | 5 | inner_validation_target_90_specificity | 0.772 | 0.900 | False | 30 | 6 | 3 | 17 | 4 |
| image_only | 5 | default_0p5 | 0.500 |  | False | 30 | 10 | 10 | 10 | 0 |
| image_only | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 30 | 28 | 72 | 20 |
| image_only | POOLED | default_0p5 | 0.500 |  | False | 150 | 38 | 44 | 56 | 12 |
| early_fusion | 1 | inner_validation_target_90_specificity | 0.781 | 0.900 | False | 30 | 4 | 3 | 17 | 6 |
| early_fusion | 1 | default_0p5 | 0.500 |  | False | 30 | 4 | 5 | 15 | 6 |
| early_fusion | 2 | inner_validation_target_90_specificity | 0.516 | 0.900 | False | 30 | 7 | 1 | 19 | 3 |
| early_fusion | 2 | default_0p5 | 0.500 |  | False | 30 | 7 | 2 | 18 | 3 |
| early_fusion | 3 | inner_validation_target_90_specificity | 0.771 | 0.912 | False | 30 | 6 | 4 | 16 | 4 |
| early_fusion | 3 | default_0p5 | 0.500 |  | False | 30 | 7 | 8 | 12 | 3 |
| early_fusion | 4 | inner_validation_target_90_specificity | 0.785 | 0.912 | False | 30 | 4 | 0 | 20 | 6 |
| early_fusion | 4 | default_0p5 | 0.500 |  | False | 30 | 5 | 1 | 19 | 5 |
| early_fusion | 5 | inner_validation_target_90_specificity | 0.681 | 0.900 | False | 30 | 8 | 7 | 13 | 2 |
| early_fusion | 5 | default_0p5 | 0.500 |  | False | 30 | 9 | 12 | 8 | 1 |
| early_fusion | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 29 | 15 | 85 | 21 |
| early_fusion | POOLED | default_0p5 | 0.500 |  | False | 150 | 32 | 28 | 72 | 18 |
| intermediate_fusion | 1 | inner_validation_target_90_specificity | 0.808 | 0.900 | False | 30 | 4 | 6 | 14 | 6 |
| intermediate_fusion | 1 | default_0p5 | 0.500 |  | False | 30 | 5 | 13 | 7 | 5 |
| intermediate_fusion | 2 | inner_validation_target_90_specificity | 0.862 | 0.900 | False | 30 | 2 | 0 | 20 | 8 |
| intermediate_fusion | 2 | default_0p5 | 0.500 |  | False | 30 | 7 | 4 | 16 | 3 |
| intermediate_fusion | 3 | inner_validation_target_90_specificity | 0.529 | 0.900 | False | 30 | 8 | 9 | 11 | 2 |
| intermediate_fusion | 3 | default_0p5 | 0.500 |  | False | 30 | 8 | 9 | 11 | 2 |
| intermediate_fusion | 4 | inner_validation_target_90_specificity | 0.621 | 0.925 | False | 30 | 5 | 0 | 20 | 5 |
| intermediate_fusion | 4 | default_0p5 | 0.500 |  | False | 30 | 6 | 2 | 18 | 4 |
| intermediate_fusion | 5 | inner_validation_target_90_specificity | 0.676 | 0.900 | False | 30 | 5 | 1 | 19 | 5 |
| intermediate_fusion | 5 | default_0p5 | 0.500 |  | False | 30 | 6 | 9 | 11 | 4 |
| intermediate_fusion | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 24 | 16 | 84 | 26 |
| intermediate_fusion | POOLED | default_0p5 | 0.500 |  | False | 150 | 32 | 37 | 63 | 18 |
| late_mean | 1 | inner_validation_target_90_specificity | 0.450 | 0.900 | False | 30 | 4 | 8 | 12 | 6 |
| late_mean | 1 | default_0p5 | 0.500 |  | False | 30 | 4 | 7 | 13 | 6 |
| late_mean | 2 | inner_validation_target_90_specificity | 0.424 | 0.900 | False | 30 | 6 | 2 | 18 | 4 |
| late_mean | 2 | default_0p5 | 0.500 |  | False | 30 | 3 | 0 | 20 | 7 |
| late_mean | 3 | inner_validation_target_90_specificity | 0.432 | 0.938 | False | 30 | 9 | 7 | 13 | 1 |
| late_mean | 3 | default_0p5 | 0.500 |  | False | 30 | 6 | 3 | 17 | 4 |
| late_mean | 4 | inner_validation_target_90_specificity | 0.444 | 0.900 | False | 30 | 5 | 1 | 19 | 5 |
| late_mean | 4 | default_0p5 | 0.500 |  | False | 30 | 4 | 0 | 20 | 6 |
| late_mean | 5 | inner_validation_target_90_specificity | 0.477 | 0.912 | False | 30 | 5 | 2 | 18 | 5 |
| late_mean | 5 | default_0p5 | 0.500 |  | False | 30 | 3 | 2 | 18 | 7 |
| late_mean | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 29 | 20 | 80 | 21 |
| late_mean | POOLED | default_0p5 | 0.500 |  | False | 150 | 20 | 12 | 88 | 30 |
| late_stack_logit | 1 | inner_validation_target_90_specificity | 0.336 | 0.912 | False | 30 | 4 | 10 | 10 | 6 |
| late_stack_logit | 1 | default_0p5 | 0.500 |  | False | 30 | 3 | 1 | 19 | 7 |
| late_stack_logit | 2 | inner_validation_target_90_specificity | 0.281 | 0.950 | False | 30 | 6 | 2 | 18 | 4 |
| late_stack_logit | 2 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| late_stack_logit | 3 | inner_validation_target_90_specificity | 0.311 | 0.963 | False | 30 | 9 | 9 | 11 | 1 |
| late_stack_logit | 3 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| late_stack_logit | 4 | inner_validation_target_90_specificity | 0.264 | 0.912 | False | 30 | 5 | 1 | 19 | 5 |
| late_stack_logit | 4 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| late_stack_logit | 5 | inner_validation_target_90_specificity | 0.297 | 0.912 | False | 30 | 6 | 3 | 17 | 4 |
| late_stack_logit | 5 | default_0p5 | 0.500 |  | False | 30 | 0 | 0 | 20 | 10 |
| late_stack_logit | POOLED | cross_fitted_inner_validation_target_90_specificity |  |  | False | 150 | 30 | 25 | 75 | 20 |
| late_stack_logit | POOLED | default_0p5 | 0.500 |  | False | 150 | 3 | 1 | 99 | 47 |
