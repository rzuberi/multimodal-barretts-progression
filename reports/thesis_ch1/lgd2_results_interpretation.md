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
- LGD2+ interpretability status: ABMIL histology interpretation is complete for all eight selected cases; probability-level fusion case interpretation is complete for the first three case packs; CNV region/gene interpretation and model-internal fusion attribution remain missing.
- Model comparison is based on saved out-of-fold predictions; no model training was run here.

## Paired patient-level comparison (added value of histopathology)

- Paired shared-index bootstrap deltas are in `lgd2_paired_model_differences_all_samples.csv/.md` and the early-prediction equivalent.
- Adding histopathology to CNV improved internal out-of-fold patient-level discrimination for next-biopsy LGD2+ progression in the matched cohort: early-fusion UNI2 minus CNV-only has a delta AUPRC 95% CI excluding zero, and late-fusion UNI2 (mean) minus CNV-only also excludes zero.
- Image-only UNI2 minus CNV-only crosses zero for delta AUPRC, so image-only superiority over CNV is not established on this internal cohort.
- Model-selected 'best' contrasts are optimistic; where a delta CI crosses zero, no superiority is claimed.

## Supporting evidence and limitations

- Modality ablation (image/CNV shuffling) is in `lgd2_modality_ablation_comparison.csv/.md`; image shuffling degrades performance, supporting a histology contribution. This is supporting evidence, not causal proof.
- Endpoint is LGD2+ neoplastic progression (`NextBiopsyProgression_LGD2plus`), NOT cancer/OAC prediction: it includes LGD and HGD and the cohort has a single current-grade OAC row.
- Timing/operating-point caveats: see `lgd2_timing_and_operating_point_limitations.md` (at-event excluded, not strict known-lead-time; fixed operating points are post-hoc).
- These are internal cross-validated estimates; no external validation.
- See `lgd2_table_generation_warnings.md` for table-generation warnings.
