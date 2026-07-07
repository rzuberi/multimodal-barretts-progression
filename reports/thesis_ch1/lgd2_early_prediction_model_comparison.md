# LGD2+ Early-Prediction Model Comparison

Rows are representative final-candidate models at `patient_max` aggregation.
Ranking uses AUPRC, then ROC AUC, sensitivity/progressors detected, then lower false-positive burden.

| comparison_slot | result_id | model_key | auprc | roc_auc | sensitivity | specificity | ppv | npv | tp | fp | fn | false_positives_per_detected_progressor | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best_early_fusion | lgd2_early_fusion_uni2 | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.764 | 0.864 | 0.740 | 0.810 | 0.661 | 0.862 | 37 | 19 | 13 | 0.514 | 0.154 |
| best_multimodal_overall | lgd2_early_fusion_uni2 | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.764 | 0.864 | 0.740 | 0.810 | 0.661 | 0.862 | 37 | 19 | 13 | 0.514 | 0.154 |
| best_coattention | lgd2_coattention_uni2 | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.712 | 0.846 | 0.840 | 0.700 | 0.583 | 0.897 | 42 | 30 | 8 | 0.714 | 0.175 |
| best_intermediate_fusion | lgd2_intermediate_fusion_gigapath | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.710 | 0.810 | 0.820 | 0.600 | 0.506 | 0.870 | 41 | 40 | 9 | 0.976 | 0.210 |
| best_image_only | lgd2_image_uni2 | model_name=abmil | 0.706 | 0.801 | 0.820 | 0.520 | 0.461 | 0.852 | 41 | 48 | 9 | 1.171 | 0.220 |
| cnv_only | lgd2_cnv_core | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 0.553 | 0.674 | 0.280 | 0.960 | 0.778 | 0.727 | 14 | 4 | 36 | 0.286 | 0.201 |
