# Model Architectures

This catalog lists every model discovered in the experiment universe and how it is produced (trainable vs derived).

- Total models listed: `23`
- Modalities: `image`, `cnv`, `multimodal`
- Derived models are generated from fold predictions (not trained as independent base learners).

## Image Models

| Model | Kind | Task Types | Architecture Summary |
|---|---|---|---|
| `latefusion_abmil_img_only` | `derived` | `binary,multiclass,regression` | Late-fusion derived baseline using ABMIL image predictions only |
| `latefusion_pool_mean_img_only` | `derived` | `binary,multiclass,regression` | Late-fusion derived baseline using pool_mean image predictions only |
| `abmil` | `trainable` | `binary,multiclass,regression` | Attention MIL (gated attention pooling over tile embeddings) |
| `abmil_nogate` | `trainable` | `binary,multiclass,regression` | Attention MIL (non-gated attention pooling variant) |
| `pool_mean` | `trainable` | `binary,multiclass,regression` | Mean pooling MIL baseline over slide-level tile embeddings |
| `set_transformer_lite` | `trainable` | `binary,multiclass,regression` | Lightweight Set-Transformer MIL encoder over tile sets |

## Cnv Models

| Model | Kind | Task Types | Architecture Summary |
|---|---|---|---|
| `latefusion_cnv_only` | `derived` | `binary,multiclass,regression` | Late-fusion derived baseline using CNV predictions only |
| `cnv_elasticnet_logreg` | `trainable` | `binary,multiclass,regression` | Elastic-net generalized linear family (classification/regression) |
| `cnv_linear_svm_calibrated` | `trainable` | `binary,multiclass,regression` | Linear SVM family with probability calibration / SVR variant |
| `cnv_mlp` | `trainable` | `binary,multiclass,regression` | Feed-forward MLP classifier/regressor for CNV tabular features |
| `cnv_pca_logreg` | `trainable` | `binary,multiclass,regression` | PCA-reduced CNV features + L2 logistic / ridge family |
| `cnv_random_forest` | `trainable` | `binary,multiclass,regression` | Random forest classifier/regressor on CNV feature vectors |
| `cnv_temporal_delta_logreg` | `trainable` | `binary,multiclass,regression` | Temporal-delta CNV augmentation + PCA + linear model |
| `cnv_xgboost` | `trainable` | `binary,multiclass,regression` | XGBoost gradient-boosted trees (with sklearn fallback) |

## Multimodal Models

| Model | Kind | Task Types | Architecture Summary |
|---|---|---|---|
| `latefusion_abmil_mean` | `derived` | `binary,multiclass,regression` | Late fusion: mean of ABMIL image + CNV fold predictions |
| `latefusion_abmil_stack_logit` | `derived` | `binary,multiclass,regression` | Late fusion: leakage-safe logistic stacker on ABMIL+CNV fold predictions |
| `latefusion_pool_mean_mean` | `derived` | `binary,multiclass,regression` | Late fusion: mean of pool_mean image + CNV fold predictions |
| `latefusion_pool_mean_stack_logit` | `derived` | `binary,multiclass,regression` | Late fusion: leakage-safe logistic stacker on pool_mean+CNV fold predictions |
| `coattn_abmil_cnv` | `trainable` | `binary,multiclass,regression` | Cross-modal co-attention between ABMIL image tokens and CNV features |
| `early_max_mlp` | `trainable` | `binary,multiclass,regression` | Early fusion (max/alt pooling variant) + MLP head |
| `early_mean_mlp` | `trainable` | `binary,multiclass,regression` | Early fusion: concatenate image+CNV representations -> MLP head |
| `early_mean_mlp_timev1` | `trainable` | `binary,multiclass,regression` | Early fusion with temporal-aware feature variant + MLP head |
| `intermediate_abmil_cnv` | `trainable` | `binary,multiclass,regression` | Intermediate fusion between ABMIL image branch and CNV branch |

## Notes

- `latefusion_*` entries are derived outputs produced by the late-fusion stage and are included in coverage accounting.
- Multimodal trainable families include early fusion, intermediate fusion, and co-attention variants.
- CNV models now support binary, multiclass, and regression tasks in the full-coverage LGD3plus campaign.
