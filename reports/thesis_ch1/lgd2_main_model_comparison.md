# LGD2+ Main Model Comparison

Rows are representative final-candidate models at `patient_max` aggregation.
Ranking uses AUPRC, then ROC AUC, sensitivity/progressors detected, then lower false-positive burden.

| comparison_slot | result_id | model_key | auprc | roc_auc | sensitivity | specificity | ppv | npv | tp | fp | fn | false_positives_per_detected_progressor | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best_early_fusion | lgd2_early_fusion_uni2 | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.849 | 0.907 | 0.800 | 0.820 | 0.710 | 0.882 | 44 | 18 | 11 | 0.409 | 0.138 |
| best_multimodal_overall | lgd2_early_fusion_uni2 | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.849 | 0.907 | 0.800 | 0.820 | 0.710 | 0.882 | 44 | 18 | 11 | 0.409 | 0.138 |
| best_intermediate_fusion | lgd2_intermediate_fusion_gigapath | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.838 | 0.887 | 0.927 | 0.590 | 0.554 | 0.937 | 51 | 41 | 4 | 0.804 | 0.190 |
| best_late_fusion | lgd2_late_fusion_virchow2 | fusion_method=mean | 0.796 | 0.876 | 0.745 | 0.870 | 0.759 | 0.861 | 41 | 13 | 14 | 0.317 | 0.169 |
| best_coattention | lgd2_coattention_uni2 | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.791 | 0.889 | 0.873 | 0.710 | 0.623 | 0.910 | 48 | 29 | 7 | 0.604 | 0.159 |
| best_image_only | lgd2_image_uni2 | model_name=abmil | 0.779 | 0.855 | 0.891 | 0.510 | 0.500 | 0.895 | 49 | 49 | 6 | 1 | 0.206 |
| cnv_only | lgd2_cnv_core | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 0.660 | 0.777 | 0.345 | 0.960 | 0.826 | 0.727 | 19 | 4 | 36 | 0.211 | 0.190 |
