# LGD2+ Advanced Fusion Model Comparison

| rank | model_family | analysis_role | n_patients | n_positive | auprc | roc_auc | brier_score | ece | sensitivity | specificity | ppv | npv | tp | fp | tn | fn | false_positives_per_detected_progressor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | foundation_ensemble_fusion | advanced_post_hoc | 150 | 50 | 0.636 | 0.728 | 0.208 | 0.157 | 0.440 | 0.890 | 0.667 | 0.761 | 22 | 11 | 89 | 28 | 0.500 |
| 2 | hierarchical_patient_fusion | advanced_post_hoc | 150 | 50 | 0.631 | 0.798 | 0.180 | 0.099 | 0.540 | 0.880 | 0.692 | 0.793 | 27 | 12 | 88 | 23 | 0.444 |
| 3 | late_mean | locked_reference | 150 | 50 | 0.630 | 0.774 | 0.184 | 0.075 | 0.580 | 0.800 | 0.592 | 0.792 | 29 | 20 | 80 | 21 | 0.690 |
| 4 | early_fusion | locked_reference | 150 | 50 | 0.590 | 0.738 | 0.213 | 0.141 | 0.580 | 0.850 | 0.659 | 0.802 | 29 | 15 | 85 | 21 | 0.517 |
| 5 | intermediate_fusion | locked_reference | 150 | 50 | 0.567 | 0.741 | 0.224 | 0.167 | 0.480 | 0.840 | 0.600 | 0.764 | 24 | 16 | 84 | 26 | 0.667 |
| 6 | optimal_transport_fusion | advanced_post_hoc | 150 | 50 | 0.565 | 0.728 | 0.201 | 0.115 | 0.460 | 0.870 | 0.639 | 0.763 | 23 | 13 | 87 | 27 | 0.565 |
| 7 | image_only | locked_reference | 150 | 50 | 0.557 | 0.731 | 0.245 | 0.215 | 0.600 | 0.720 | 0.517 | 0.783 | 30 | 28 | 72 | 20 | 0.933 |
| 8 | coattention_fusion | locked_reference | 150 | 50 | 0.548 | 0.739 | 0.230 | 0.198 | 0.520 | 0.800 | 0.565 | 0.769 | 26 | 20 | 80 | 24 | 0.769 |
| 9 | cnv_only | locked_reference | 150 | 50 | 0.538 | 0.663 | 0.216 | 0.095 | 0.280 | 0.900 | 0.583 | 0.714 | 14 | 10 | 90 | 36 | 0.714 |
| 10 | multitask_temporal_fusion | advanced_post_hoc | 150 | 50 | 0.534 | 0.700 | 0.231 | 0.178 | 0.440 | 0.810 | 0.537 | 0.743 | 22 | 19 | 81 | 28 | 0.864 |
| 11 | late_stack_logit | locked_reference | 150 | 50 | 0.530 | 0.737 | 0.202 | 0.110 | 0.600 | 0.750 | 0.545 | 0.789 | 30 | 25 | 75 | 20 | 0.833 |
| 12 | low_rank_bilinear_fusion | advanced_post_hoc | 150 | 50 | 0.514 | 0.666 | 0.244 | 0.169 | 0.400 | 0.870 | 0.606 | 0.744 | 20 | 13 | 87 | 30 | 0.650 |
| 13 | cnv_token_cross_attention | advanced_post_hoc | 150 | 50 | 0.507 | 0.690 | 0.244 | 0.197 | 0.580 | 0.720 | 0.509 | 0.774 | 29 | 28 | 72 | 21 | 0.966 |
| 14 | reliability_gated_fusion | advanced_post_hoc | 150 | 50 | 0.502 | 0.682 | 0.226 | 0.124 | 0.380 | 0.830 | 0.528 | 0.728 | 19 | 17 | 83 | 31 | 0.895 |
