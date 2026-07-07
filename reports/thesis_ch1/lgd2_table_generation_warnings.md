# LGD2+ Table Generation Warnings

| category | item | note |
|---|---|---|
| review_manually | lgd2_foundation_combo | Prediction file lacks patient_id in audited header; join needed before patient metrics. |
| review_manually | lgd2_clinical_augmentation | Relevant but not primary unless explicitly included. |
| review_manually | lgd2_tile_magnification_comparison | Do not claim complete until exact summary table is identified. |
| skipped | lgd2_foundation_combo | Not included because patient IDs were not validated in manifest. |
| unavailable | late_fusion | No validated patient-level late-fusion row found in recomputed metrics. |
