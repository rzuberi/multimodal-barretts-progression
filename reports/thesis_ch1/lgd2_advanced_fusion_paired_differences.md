# LGD2+ Advanced Fusion Paired Differences

| model_a | model_b | contrast_role | n_patients | n_positive | n_negative | n_boot | valid_fraction | delta_auprc | delta_auprc_ci_low | delta_auprc_ci_high | delta_auprc_sign_prob | delta_roc_auc | delta_roc_auc_ci_low | delta_roc_auc_ci_high | delta_roc_auc_sign_prob | delta_brier | delta_brier_ci_low | delta_brier_ci_high | delta_brier_sign_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cnv_token_cross_attention | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.122 | -0.195 | -0.035 | 0.008 | -0.084 | -0.134 | -0.034 | 0.000 | 0.060 | 0.023 | 0.100 | 0.003 |
| cnv_token_cross_attention | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.031 | -0.157 | 0.121 | 0.760 | 0.027 | -0.105 | 0.158 | 0.676 | 0.028 | -0.033 | 0.090 | 0.356 |
| cnv_token_cross_attention | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.050 | -0.118 | 0.014 | 0.130 | -0.041 | -0.086 | 0.003 | 0.072 | -0.001 | -0.032 | 0.030 | 0.920 |
| foundation_ensemble_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.006 | -0.098 | 0.096 | 0.979 | -0.046 | -0.114 | 0.021 | 0.172 | 0.024 | -0.008 | 0.056 | 0.132 |
| foundation_ensemble_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.097 | -0.053 | 0.244 | 0.199 | 0.065 | -0.060 | 0.195 | 0.301 | -0.008 | -0.057 | 0.040 | 0.757 |
| foundation_ensemble_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.079 | -0.037 | 0.162 | 0.205 | -0.003 | -0.068 | 0.061 | 0.932 | -0.037 | -0.076 | 0.003 | 0.068 |
| hierarchical_patient_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.001 | -0.108 | 0.132 | 0.900 | 0.024 | -0.051 | 0.102 | 0.552 | -0.004 | -0.040 | 0.033 | 0.798 |
| hierarchical_patient_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.092 | -0.024 | 0.233 | 0.118 | 0.135 | 0.033 | 0.234 | 0.009 | -0.036 | -0.083 | 0.011 | 0.128 |
| hierarchical_patient_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.074 | -0.063 | 0.208 | 0.287 | 0.067 | -0.019 | 0.152 | 0.126 | -0.065 | -0.114 | -0.017 | 0.011 |
| low_rank_bilinear_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.115 | -0.206 | -0.033 | 0.006 | -0.108 | -0.184 | -0.040 | 0.002 | 0.060 | 0.029 | 0.093 | 0.000 |
| low_rank_bilinear_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.024 | -0.135 | 0.090 | 0.684 | 0.003 | -0.113 | 0.119 | 0.970 | 0.028 | -0.022 | 0.078 | 0.278 |
| low_rank_bilinear_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.043 | -0.160 | 0.051 | 0.340 | -0.065 | -0.147 | 0.011 | 0.102 | -0.002 | -0.040 | 0.038 | 0.956 |
| multitask_temporal_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.096 | -0.173 | -0.020 | 0.018 | -0.074 | -0.131 | -0.016 | 0.016 | 0.047 | 0.016 | 0.079 | 0.003 |
| multitask_temporal_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.005 | -0.114 | 0.121 | 0.988 | 0.037 | -0.073 | 0.154 | 0.515 | 0.015 | -0.037 | 0.068 | 0.593 |
| multitask_temporal_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.023 | -0.130 | 0.065 | 0.566 | -0.031 | -0.099 | 0.038 | 0.389 | -0.014 | -0.047 | 0.018 | 0.384 |
| optimal_transport_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.065 | -0.146 | 0.028 | 0.180 | -0.047 | -0.115 | 0.019 | 0.160 | 0.017 | -0.001 | 0.036 | 0.064 |
| optimal_transport_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.026 | -0.106 | 0.176 | 0.636 | 0.065 | -0.055 | 0.187 | 0.299 | -0.015 | -0.053 | 0.024 | 0.470 |
| optimal_transport_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.008 | -0.083 | 0.089 | 0.888 | -0.004 | -0.072 | 0.063 | 0.922 | -0.044 | -0.080 | -0.008 | 0.013 |
| reliability_gated_fusion | late_mean | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.128 | -0.218 | -0.038 | 0.006 | -0.092 | -0.155 | -0.030 | 0.003 | 0.042 | 0.014 | 0.071 | 0.004 |
| reliability_gated_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.037 | -0.154 | 0.090 | 0.585 | 0.019 | -0.104 | 0.140 | 0.780 | 0.010 | -0.038 | 0.059 | 0.712 |
| reliability_gated_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.055 | -0.169 | 0.042 | 0.258 | -0.049 | -0.118 | 0.019 | 0.146 | -0.019 | -0.050 | 0.012 | 0.232 |
