# Cross-task detection grid — ROC AUC (spec@sens90)

Patient-level, nested 5-fold CV. Best backbone per family shown. Cells: ROC AUC (specificity@90%-sensitivity).
Final column: best family per task ranked by AUPRC (the primary metric; breaks ROC ties).

| task | image_only | cnv_only | early_fusion | intermediate_fusion | coattention_fusion | moe | late_mean | late_stack_logit | best_by_auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.82 (0.37) | 0.78 (0.47) | 0.77 (0.50) | 0.73 (0.42) | 0.82 (0.58) | 0.80 (0.51) | early_fusion (0.575) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.85 (0.52) | 0.81 (0.36) | 0.84 (0.54) | 0.84 (0.57) | 0.89 (0.78) | 0.87 (0.71) | late_mean (0.898) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.76 (0.41) | 0.72 (0.46) | 0.75 (0.49) | 0.73 (0.34) | 0.77 (0.36) | 0.74 (0.39) | late_mean (0.625) |
| next_biopsy_highrisk | 0.76 (0.30) | 0.76 (0.56) | 0.84 (0.55) | 0.82 (0.61) | 0.81 (0.53) | 0.79 (0.50) | 0.79 (0.38) | 0.75 (0.30) | early_fusion (0.613) |
| at_risk_3y_censored | 0.76 (0.25) | 0.72 (0.40) | 0.73 (0.27) | 0.73 (0.21) | 0.63 (0.19) | 0.66 (0.04) | 0.78 (0.48) | 0.77 (0.40) | intermediate_fusion (0.682) |
