# LGD2+ Histology Interpretation Input Audit

## Scope

Audit for the 8 selected LGD2+ thesis interpretation cases. Heavy WSI, tile, feature, checkpoint, and attention outputs remain external.

## Required Inputs

| input | status | evidence / external ref | safe for Git? | notes |
| --- | --- | --- | --- | --- |
| selected case slide IDs | FOUND | `reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv`: `slide_id`, `sample_id`, `patient_id` | yes, basenames only | all 8 cases have slide IDs |
| LGD2+ master cohort | FOUND external | `../data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv` | no | used only for lookup; not copied |
| UNI2 feature index | FOUND external | `../data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/image/all_samples/core_gpu/index/virchow2_index.csv` | no | index rows found for all 8 selected `sample_id`s; filename is legacy `virchow2_index.csv` but feature refs point to `uni2_tile224_lvl2` |
| UNI2 feature NPZ refs | FOUND external | `reports/thesis_ch1/lgd2_wsi_case_manifest.csv`: `feature_path_ref` | refs only | all 8 have `uni2_tile224_lvl2/slide_embeddings/*.npz` refs; NPZ files were not opened |
| tile coordinates | FOUND inside external feature NPZ refs | `tile_coords_ref` in `lgd2_wsi_case_manifest.csv` | refs only | runner can read coords from NPZ externally |
| image model prediction rows | FOUND external | `lgd2_image_uni2` prediction files; selected rows matched for `abmil` | refs only | folds identified for all 8 cases |
| image model checkpoints | FOUND external | `image_checkpoint_ref` in `lgd2_wsi_case_manifest.csv` | refs only | fold-matched `abmil` checkpoints found for all 8 |
| fusion model prediction rows | FOUND external | `lgd2_early_fusion_uni2` prediction files; selected rows matched for `early_mean_mlp` | refs only | folds identified for all 8 cases |
| fusion model checkpoints | FOUND external | `fusion_checkpoint_ref` in `lgd2_wsi_case_manifest.csv` | refs only | fold-matched `early_mean_mlp` checkpoints found for all 8 |
| LGD2+ tile-score / attention outputs | MISSING | `reports/thesis_ch1/lgd2_histology_interpretation_summary.csv`: `top_patch_refs=MISSING`, `attention_summary=MISSING` | yes, summary only | must be regenerated externally |
| external output directory | MISSING | `analysis/lgd2_interpretation_regeneration_20260707/histology/` | no heavy outputs in Git | directory not present at audit time |

## Case Completeness

All 8 selected cases have enough validated lightweight references to prepare external WSI explainability:

- `A_true_positive_early_01`
- `A_true_positive_early_02`
- `B_false_negative_07`
- `C_false_positive_12`
- `E_cnv_rescue_19`
- `F_histology_rescue_24`
- `G_fusion_hurt_26`
- `I_modality_disagreement_37`

No selected case is blocked at the manifest/input-reference stage.

## Blockers

- LGD2+ top-patch, tile-score, attention-spread, and heatmap outputs have not been regenerated.
- The legacy `run_wsi_explainability_case.py` opens WSI files, reads feature NPZs, loads checkpoints, and writes PNG/tile-score outputs, so it should be run only externally.
- The Git-safe `lgd2_wsi_case_manifest.csv` stores compact references. The legacy runner needs a full external manifest with raw external paths and must not write outputs into Git.
