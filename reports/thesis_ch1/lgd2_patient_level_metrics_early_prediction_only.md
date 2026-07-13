# LGD2+ Patient-Level Metrics - early_prediction_only

Endpoint: `NextBiopsyProgression_LGD2plus`.
Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
Evaluation: 5-fold patient-disjoint out-of-fold predictions.
Primary reporting level: `patient_max`.

## Ranked patient_max table

| rank | result_id | model | AUPRC | ROC AUC | sensitivity | specificity | PPV | NPV | TP | FP | TN | FN | FP/detected | Brier |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `lgd2_early_fusion_uni2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.764 | 0.864 | 0.740 | 0.810 | 0.661 | 0.862 | 37 | 19 | 81 | 13 | 0.514 | 0.154 |
| 2 | `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.738 | 0.844 | 0.720 | 0.810 | 0.655 | 0.853 | 36 | 19 | 81 | 14 | 0.528 | 0.156 |
| 3 | `lgd2_coattention_uni2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.712 | 0.846 | 0.840 | 0.700 | 0.583 | 0.897 | 42 | 30 | 70 | 8 | 0.714 | 0.175 |
| 4 | `lgd2_intermediate_fusion_gigapath` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.710 | 0.810 | 0.820 | 0.600 | 0.506 | 0.870 | 41 | 40 | 60 | 9 | 0.976 | 0.210 |
| 5 | `lgd2_image_uni2` | model_name=abmil | 0.706 | 0.801 | 0.820 | 0.520 | 0.461 | 0.852 | 41 | 48 | 52 | 9 | 1.171 | 0.220 |
| 6 | `lgd2_late_fusion_uni2` | fusion_method=mean | 0.689 | 0.811 | 0.580 | 0.820 | 0.617 | 0.796 | 29 | 18 | 82 | 21 | 0.621 | 0.179 |
| 7 | `lgd2_early_fusion_uni2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.681 | 0.789 | 0.600 | 0.760 | 0.556 | 0.792 | 30 | 24 | 76 | 20 | 0.800 | 0.182 |
| 8 | `lgd2_late_fusion_virchow2` | fusion_method=mean | 0.680 | 0.791 | 0.600 | 0.870 | 0.698 | 0.813 | 30 | 13 | 87 | 20 | 0.433 | 0.184 |
| 9 | `lgd2_intermediate_fusion_uni2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.671 | 0.831 | 0.800 | 0.690 | 0.563 | 0.873 | 40 | 31 | 69 | 10 | 0.775 | 0.182 |
| 10 | `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.666 | 0.808 | 0.740 | 0.680 | 0.536 | 0.840 | 37 | 32 | 68 | 13 | 0.865 | 0.199 |
| 11 | `lgd2_image_virchow2` | model_name=abmil | 0.664 | 0.764 | 0.760 | 0.570 | 0.469 | 0.826 | 38 | 43 | 57 | 12 | 1.132 | 0.224 |
| 12 | `lgd2_image_uni2` | model_name=set_transformer_lite | 0.661 | 0.801 | 0.880 | 0.550 | 0.494 | 0.902 | 44 | 45 | 55 | 6 | 1.023 | 0.221 |
| 13 | `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.659 | 0.779 | 0.660 | 0.770 | 0.589 | 0.819 | 33 | 23 | 77 | 17 | 0.697 | 0.182 |
| 14 | `lgd2_late_fusion_uni2` | fusion_method=stack_logit | 0.654 | 0.771 | 0.380 | 0.940 | 0.760 | 0.752 | 19 | 6 | 94 | 31 | 0.316 | 0.175 |
| 15 | `lgd2_late_fusion_virchow2` | fusion_method=stack_logit | 0.652 | 0.757 | 0.380 | 0.930 | 0.731 | 0.750 | 19 | 7 | 93 | 31 | 0.368 | 0.180 |
| 16 | `lgd2_image_virchow2` | model_name=set_transformer_lite | 0.651 | 0.780 | 0.740 | 0.660 | 0.521 | 0.835 | 37 | 34 | 66 | 13 | 0.919 | 0.202 |
| 17 | `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.634 | 0.799 | 0.620 | 0.750 | 0.554 | 0.798 | 31 | 25 | 75 | 19 | 0.806 | 0.183 |
| 18 | `lgd2_coattention_gigapath` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.623 | 0.773 | 0.820 | 0.500 | 0.451 | 0.847 | 41 | 50 | 50 | 9 | 1.220 | 0.235 |
| 19 | `lgd2_late_fusion_gigapath` | fusion_method=mean | 0.608 | 0.754 | 0.600 | 0.700 | 0.500 | 0.778 | 30 | 30 | 70 | 20 | 1.000 | 0.192 |
| 20 | `lgd2_intermediate_fusion_virchow2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.605 | 0.757 | 0.740 | 0.670 | 0.529 | 0.838 | 37 | 33 | 67 | 13 | 0.892 | 0.218 |
| 21 | `lgd2_coattention_virchow2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.601 | 0.747 | 0.740 | 0.560 | 0.457 | 0.812 | 37 | 44 | 56 | 13 | 1.189 | 0.229 |
| 22 | `lgd2_image_gigapath` | model_name=set_transformer_lite | 0.578 | 0.733 | 0.800 | 0.590 | 0.494 | 0.855 | 40 | 41 | 59 | 10 | 1.025 | 0.251 |
| 23 | `lgd2_cnv_core` | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 0.553 | 0.674 | 0.280 | 0.960 | 0.778 | 0.727 | 14 | 4 | 96 | 36 | 0.286 | 0.201 |
| 24 | `lgd2_late_fusion_gigapath` | fusion_method=stack_logit | 0.507 | 0.689 | 0.180 | 0.800 | 0.310 | 0.661 | 9 | 20 | 80 | 41 | 2.222 | 0.211 |

## Detected and missed progressors

| result_id | model | progressors detected | progressors missed | false positives | false positives per detected progressor |
|---|---|---:|---:|---:|---:|
| `lgd2_early_fusion_uni2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 37 | 13 | 19 | 0.514 |
| `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 36 | 14 | 19 | 0.528 |
| `lgd2_coattention_uni2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 42 | 8 | 30 | 0.714 |
| `lgd2_intermediate_fusion_gigapath` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 41 | 9 | 40 | 0.976 |
| `lgd2_image_uni2` | model_name=abmil | 41 | 9 | 48 | 1.171 |
| `lgd2_late_fusion_uni2` | fusion_method=mean | 29 | 21 | 18 | 0.621 |
| `lgd2_early_fusion_uni2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 30 | 20 | 24 | 0.800 |
| `lgd2_late_fusion_virchow2` | fusion_method=mean | 30 | 20 | 13 | 0.433 |
| `lgd2_intermediate_fusion_uni2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 40 | 10 | 31 | 0.775 |
| `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 37 | 13 | 32 | 0.865 |
| `lgd2_image_virchow2` | model_name=abmil | 38 | 12 | 43 | 1.132 |
| `lgd2_image_uni2` | model_name=set_transformer_lite | 44 | 6 | 45 | 1.023 |
| `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 33 | 17 | 23 | 0.697 |
| `lgd2_late_fusion_uni2` | fusion_method=stack_logit | 19 | 31 | 6 | 0.316 |
| `lgd2_late_fusion_virchow2` | fusion_method=stack_logit | 19 | 31 | 7 | 0.368 |
| `lgd2_image_virchow2` | model_name=set_transformer_lite | 37 | 13 | 34 | 0.919 |
| `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 31 | 19 | 25 | 0.806 |
| `lgd2_coattention_gigapath` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 41 | 9 | 50 | 1.220 |
| `lgd2_late_fusion_gigapath` | fusion_method=mean | 30 | 20 | 30 | 1.000 |
| `lgd2_intermediate_fusion_virchow2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 37 | 13 | 33 | 0.892 |
| `lgd2_coattention_virchow2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 37 | 13 | 44 | 1.189 |
| `lgd2_image_gigapath` | model_name=set_transformer_lite | 40 | 10 | 41 | 1.025 |
| `lgd2_cnv_core` | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 14 | 36 | 4 | 0.286 |
| `lgd2_late_fusion_gigapath` | fusion_method=stack_logit | 9 | 41 | 20 | 2.222 |

## Notes

- Excludes prediction rows joined to master rows with `DaysFromCurrentToEvent == 0`.
- Threshold-dependent metrics use default threshold `0.5`; fixed operating point columns are in the CSV.
- Bootstrap confidence intervals are reported for patient-level aggregations; biopsy/sample rows keep CI columns blank.
