# LGD2+ Patient-Level Metrics - all_samples

Endpoint: `NextBiopsyProgression_LGD2plus`.
Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
Evaluation: 5-fold patient-disjoint out-of-fold predictions.
Primary reporting level: `patient_max`.

## Ranked patient_max table

| rank | result_id | model | AUPRC | ROC AUC | sensitivity | specificity | PPV | NPV | TP | FP | TN | FN | FP/detected | Brier |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `lgd2_early_fusion_uni2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.849 | 0.907 | 0.800 | 0.820 | 0.710 | 0.882 | 44 | 18 | 82 | 11 | 0.409 | 0.138 |
| 2 | `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.843 | 0.912 | 0.855 | 0.810 | 0.712 | 0.910 | 47 | 19 | 81 | 8 | 0.404 | 0.131 |
| 3 | `lgd2_intermediate_fusion_gigapath` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.838 | 0.887 | 0.927 | 0.590 | 0.554 | 0.937 | 51 | 41 | 59 | 4 | 0.804 | 0.190 |
| 4 | `lgd2_intermediate_fusion_uni2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.796 | 0.889 | 0.891 | 0.680 | 0.605 | 0.919 | 49 | 32 | 68 | 6 | 0.653 | 0.163 |
| 5 | `lgd2_coattention_uni2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.791 | 0.889 | 0.873 | 0.710 | 0.623 | 0.910 | 48 | 29 | 71 | 7 | 0.604 | 0.159 |
| 6 | `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.783 | 0.884 | 0.927 | 0.690 | 0.622 | 0.945 | 51 | 31 | 69 | 4 | 0.608 | 0.172 |
| 7 | `lgd2_image_uni2` | model_name=abmil | 0.779 | 0.855 | 0.891 | 0.510 | 0.500 | 0.895 | 49 | 49 | 51 | 6 | 1.000 | 0.206 |
| 8 | `lgd2_image_virchow2` | model_name=abmil | 0.768 | 0.846 | 0.891 | 0.570 | 0.533 | 0.905 | 49 | 43 | 57 | 6 | 0.878 | 0.203 |
| 9 | `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.759 | 0.852 | 0.709 | 0.760 | 0.619 | 0.826 | 39 | 24 | 76 | 16 | 0.615 | 0.164 |
| 10 | `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.757 | 0.829 | 0.709 | 0.780 | 0.639 | 0.830 | 39 | 22 | 78 | 16 | 0.564 | 0.166 |
| 11 | `lgd2_early_fusion_uni2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.756 | 0.830 | 0.655 | 0.770 | 0.610 | 0.802 | 36 | 23 | 77 | 19 | 0.639 | 0.169 |
| 12 | `lgd2_image_uni2` | model_name=set_transformer_lite | 0.751 | 0.865 | 0.964 | 0.550 | 0.541 | 0.965 | 53 | 45 | 55 | 2 | 0.849 | 0.199 |
| 13 | `lgd2_intermediate_fusion_virchow2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.748 | 0.858 | 0.891 | 0.670 | 0.598 | 0.918 | 49 | 33 | 67 | 6 | 0.673 | 0.187 |
| 14 | `lgd2_coattention_gigapath` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.747 | 0.851 | 0.945 | 0.500 | 0.510 | 0.943 | 52 | 50 | 50 | 3 | 0.962 | 0.214 |
| 15 | `lgd2_image_virchow2` | model_name=set_transformer_lite | 0.747 | 0.848 | 0.855 | 0.660 | 0.580 | 0.892 | 47 | 34 | 66 | 8 | 0.723 | 0.177 |
| 16 | `lgd2_coattention_virchow2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 0.739 | 0.852 | 0.909 | 0.560 | 0.532 | 0.918 | 50 | 44 | 56 | 5 | 0.880 | 0.200 |
| 17 | `lgd2_image_gigapath` | model_name=set_transformer_lite | 0.729 | 0.829 | 0.891 | 0.590 | 0.544 | 0.908 | 49 | 41 | 59 | 6 | 0.837 | 0.219 |
| 18 | `lgd2_cnv_core` | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 0.660 | 0.777 | 0.345 | 0.960 | 0.826 | 0.727 | 19 | 4 | 96 | 36 | 0.211 | 0.190 |

## Detected and missed progressors

| result_id | model | progressors detected | progressors missed | false positives | false positives per detected progressor |
|---|---|---:|---:|---:|---:|
| `lgd2_early_fusion_uni2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 44 | 11 | 18 | 0.409 |
| `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 47 | 8 | 19 | 0.404 |
| `lgd2_intermediate_fusion_gigapath` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 51 | 4 | 41 | 0.804 |
| `lgd2_intermediate_fusion_uni2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 49 | 6 | 32 | 0.653 |
| `lgd2_coattention_uni2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 48 | 7 | 29 | 0.604 |
| `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 51 | 4 | 31 | 0.608 |
| `lgd2_image_uni2` | model_name=abmil | 49 | 6 | 49 | 1.000 |
| `lgd2_image_virchow2` | model_name=abmil | 49 | 6 | 43 | 0.878 |
| `lgd2_early_fusion_virchow2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 39 | 16 | 24 | 0.615 |
| `lgd2_early_fusion_gigapath` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 39 | 16 | 22 | 0.564 |
| `lgd2_early_fusion_uni2` | model_name=early_mean_mlp_timev1; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 36 | 19 | 23 | 0.639 |
| `lgd2_image_uni2` | model_name=set_transformer_lite | 53 | 2 | 45 | 0.849 |
| `lgd2_intermediate_fusion_virchow2` | model_name=intermediate_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 49 | 6 | 33 | 0.673 |
| `lgd2_coattention_gigapath` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 52 | 3 | 50 | 0.962 |
| `lgd2_image_virchow2` | model_name=set_transformer_lite | 47 | 8 | 34 | 0.723 |
| `lgd2_coattention_virchow2` | model_name=coattn_abmil_cnv; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none; instance_k=0; subsample_mode=uniform; embed_pca_dim=0 | 50 | 5 | 44 | 0.880 |
| `lgd2_image_gigapath` | model_name=set_transformer_lite | 49 | 6 | 41 | 0.837 |
| `lgd2_cnv_core` | model_name=cnv_random_forest; cnv_variant=windows_armdiff_plus_arms_plus_cx; cnv_mask_name=none | 19 | 36 | 4 | 0.211 |

## Notes

- Includes all labelled prediction rows in the selected final-candidate LGD2+ files.
- Threshold-dependent metrics use default threshold `0.5`; fixed operating point columns are in the CSV.
- Bootstrap confidence intervals are reported for patient-level aggregations; biopsy/sample rows keep CI columns blank.
