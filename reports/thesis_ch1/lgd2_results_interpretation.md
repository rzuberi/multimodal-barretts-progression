# LGD2+ Results Interpretation

## All samples

- Best AUPRC: lgd2_early_fusion_uni2 (model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0), AUPRC 0.849.
- Best AUC: lgd2_early_fusion_gigapath (model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0), AUC 0.912.
- Most progressors detected: lgd2_image_uni2 (model_name=set_transformer_lite), TP 53.
- Fewest progressors missed: lgd2_image_uni2 (model_name=set_transformer_lite), FN 2.
- Lowest false-positive burden: lgd2_cnv_core (model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none), FP/detected 0.211.
- Best multimodal vs CNV-only: multimodal AUPRC 0.849 vs CNV-only 0.660.
- Best multimodal vs image-only: multimodal AUPRC 0.849 vs image-only 0.779.

## Early-prediction-only

- Best AUPRC: lgd2_early_fusion_uni2 (model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0), AUPRC 0.764.
- Best AUC: lgd2_early_fusion_uni2 (model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0), AUC 0.864.
- Ranking conclusion is similar: the same best multimodal family remains strongest.

## Recommended headline

- Recommended headline model: lgd2_early_fusion_uni2 (model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0).
- Use early-prediction-only results as an important sensitivity analysis because at-event rows inflate clinical detectability.
- Do not overclaim small metric differences without confidence intervals and clinical review.

## Exclusions and caveats

- Foundation-combo and clinical-augmentation rows remain excluded unless manual-review status changes.
- LGD2+ interpretability outputs are still missing.
- Model comparison is based on saved out-of-fold predictions; no model training was run here.
- See `lgd2_table_generation_warnings.md` for table-generation warnings.
