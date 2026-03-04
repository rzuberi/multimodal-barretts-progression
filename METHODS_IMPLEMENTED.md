# Methods Implemented

Implementation-level method catalog for this campaign (training, derived fusion, routing/MoE, and audit/orchestration).

## Method Inventory

| Category | Method | What It Does | Task Types | Leakage Safe |
|---|---|---|---|---|
| `labeling` | `LGD3plus_canonical_progression` | Canonical progression: NextBiopsyLabel>=3 OR (==2 and LGDStreakSoFar>=2) | `binary-derived labels` | `no` |
| `training` | `image_mil_pooling` | Image MIL with pooling/attention/set-transformer families | `binary,multiclass,regression` | `not_applicable` |
| `training` | `cnv_tabular_models` | CNV models upgraded for binary + multiclass + regression | `binary,multiclass,regression` | `not_applicable` |
| `training` | `multimodal_early_intermediate_coattn` | Early fusion, intermediate fusion, and co-attention multimodal lanes | `binary,multiclass,regression` | `not_applicable` |
| `derived_fusion` | `latefusion_img_only` | Image-only derived predictions for selected image backbones | `binary,multiclass,regression` | `yes` |
| `derived_fusion` | `latefusion_cnv_only` | CNV-only derived predictions | `binary,multiclass,regression` | `yes` |
| `derived_fusion` | `latefusion_mean` | Arithmetic mean fusion over expert predictions | `binary,multiclass,regression` | `yes` |
| `derived_fusion` | `latefusion_stack_logit` | Fold-safe stacker (trained on non-heldout folds only) | `binary,multiclass,regression` | `yes` |
| `ensemble` | `routing_expert_only` | Single-expert baselines from best available expert(s) | `binary,multiclass,regression` | `yes` |
| `ensemble` | `routing_available_mean` | Mean ensemble across available experts (2 or 3) | `binary,multiclass,regression` | `yes` |
| `ensemble` | `routing_available_stack_logit` | Stacked ensemble across available experts with fold-safe training | `binary,multiclass,regression` | `yes` |
| `ensemble` | `routing_k_hard_soft` | Cluster-and-route MoE for k in configured range; hard/soft routing | `binary,multiclass,regression` | `yes` |
| `ensemble` | `foundation_combo_fusion` | Encoder-combo fusion over multiple image encoders (+ optional CNV) | `binary,multiclass,regression` | `yes` |
| `orchestration` | `skip_if_exists_5fold_policy` | rep=1 and folds=1..5; skip existing outputs to avoid reruns | `all` | `not_applicable` |
| `audit` | `global_summary_coverage` | Global summaries include trainable + derived rows for coverage accounting | `all` | `not_applicable` |

## Campaign-specific Implementation Highlights

- Canonical progression event is LGD3plus across progression-derived labels.
- Late-fusion rows are routed to a deterministic derived stage instead of being treated as unsupported trainable lanes.
- CNV models previously treated as binary-only now run multiclass/regression variants with task-appropriate metrics.
- Routing/MoE now supports binary + multiclass + regression and can operate with partial expert availability.
- Global summary collection ingests trainable + derived + routing + combo-fusion rows so coverage audit reflects completed work.

## Explicit Derived/Ensemble Output Names

- Late-fusion model IDs generated for coverage:
  - `latefusion_abmil_img_only`
  - `latefusion_pool_mean_img_only`
  - `latefusion_cnv_only`
  - `latefusion_abmil_mean`
  - `latefusion_abmil_stack_logit`
  - `latefusion_pool_mean_mean`
  - `latefusion_pool_mean_stack_logit`
- Routing method names produced (task-type aware, depending on available experts):
  - `expert_img_only`, `expert_cnv_only`, `expert_mm_only`
  - `ensemble_available_mean`, `ensemble_available_stack_logit`
  - `ensemble_img_cnv_mean`, `ensemble_mm_cnv_mean`, `ensemble_mm_img_mean`, `ensemble_all3_mean`
  - `ensemble_img_cnv_stack_logit`, `ensemble_mm_cnv_stack_logit`, `ensemble_mm_img_stack_logit`, `ensemble_all3_stack_logit`
  - `routing_k{K}_hard`, `routing_k{K}_soft`
- Foundation combo-fusion method name pattern:
  - `image_combo_<encoder_set>_mean`
  - `cnv_plus_image_combo_<encoder_set>_mean`
