# Lgd2 Final Pre Event Paired Differences

| model_a | model_b | contrast_role | n_patients | n_positive | n_negative | n_boot | valid_fraction | delta_auprc | delta_auprc_ci_low | delta_auprc_ci_high | delta_auprc_sign_prob | delta_roc_auc | delta_roc_auc_ci_low | delta_roc_auc_ci_high | delta_roc_auc_sign_prob | delta_brier | delta_brier_ci_low | delta_brier_ci_high | delta_brier_sign_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| early_fusion | cnv_only | primary | 150 | 50 | 100 | 5000 | 1 | 0.051 | -0.053 | 0.167 | 0.342 | 0.075 | -0.034 | 0.184 | 0.178 | -0.003 | -0.055 | 0.049 | 0.922 |
| intermediate_fusion | cnv_only | primary | 150 | 50 | 100 | 5000 | 1 | 0.029 | -0.084 | 0.157 | 0.591 | 0.078 | -0.032 | 0.192 | 0.179 | 0.008 | -0.048 | 0.065 | 0.795 |
| late_mean | cnv_only | primary | 150 | 50 | 100 | 5000 | 1 | 0.091 | -0.036 | 0.219 | 0.155 | 0.111 | 0.002 | 0.219 | 0.045 | -0.032 | -0.062 | -0.004 | 0.024 |
| late_stack_logit | cnv_only | primary | 150 | 50 | 100 | 5000 | 1 | -0.008 | -0.120 | 0.123 | 0.961 | 0.074 | -0.039 | 0.190 | 0.194 | -0.013 | -0.031 | 0.003 | 0.095 |
| image_only | cnv_only | contextual | 150 | 50 | 100 | 5000 | 1 | 0.019 | -0.121 | 0.181 | 0.731 | 0.068 | -0.060 | 0.192 | 0.303 | 0.029 | -0.032 | 0.093 | 0.348 |
| early_fusion | image_only | contextual | 150 | 50 | 100 | 5000 | 1 | 0.033 | -0.080 | 0.126 | 0.599 | 0.007 | -0.056 | 0.070 | 0.821 | -0.032 | -0.069 | 0.006 | 0.097 |
| intermediate_fusion | image_only | contextual | 150 | 50 | 100 | 5000 | 1 | 0.010 | -0.089 | 0.092 | 0.918 | 0.010 | -0.051 | 0.071 | 0.753 | -0.021 | -0.051 | 0.009 | 0.171 |
| late_mean | image_only | contextual | 150 | 50 | 100 | 5000 | 1 | 0.073 | 0.006 | 0.125 | 0.031 | 0.043 | 0.015 | 0.071 | 0.002 | -0.061 | -0.095 | -0.027 | 0.000 |
| late_stack_logit | image_only | contextual | 150 | 50 | 100 | 5000 | 1 | -0.027 | -0.109 | 0.042 | 0.431 | 0.005 | -0.029 | 0.038 | 0.739 | -0.043 | -0.093 | 0.008 | 0.098 |
| coattention_fusion | cnv_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | 0.010 | -0.103 | 0.136 | 0.807 | 0.076 | -0.035 | 0.185 | 0.166 | 0.014 | -0.047 | 0.073 | 0.632 |
| coattention_fusion | image_only | supplementary_post_hoc | 150 | 50 | 100 | 5000 | 1 | -0.009 | -0.131 | 0.099 | 0.833 | 0.008 | -0.076 | 0.088 | 0.860 | -0.015 | -0.052 | 0.023 | 0.424 |
