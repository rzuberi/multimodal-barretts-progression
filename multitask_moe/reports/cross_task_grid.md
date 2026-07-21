# Cross-task detection grid — ROC AUC (spec@sens90)

Patient-level, nested 5-fold CV. Best backbone per family shown.

| task | image_only | cnv_only | moe | late_mean | intermediate_fusion |
| --- | --- | --- | --- | --- | --- |
| ever_progress | 0.78 (0.39) | 0.66 (0.36) | 0.73 (0.42) | 0.82 (0.58) | 0.78 (0.47) |
| at_risk_3y | 0.87 (0.67) | 0.82 (0.51) | 0.84 (0.57) | 0.89 (0.78) | 0.81 (0.36) |
| next_biopsy_progression | 0.73 (0.37) | 0.67 (0.14) | 0.73 (0.34) | 0.77 (0.36) | 0.72 (0.46) |
