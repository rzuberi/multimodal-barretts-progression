# LGD2+ CNV Interpretation Commands

No CNV regeneration command was run in this stage. The commands below are templates that must be validated against the LGD2+ campaign before execution.

External output root:

`analysis/lgd2_interpretation_regeneration_20260707/`

## `scripts/cnv_feature_importance.py`

What it appears to do: builds a CNV feature-importance worklist, runs per-row importance jobs, and aggregates fold/model importances. It imports model-building/fitting utilities from `scripts/run_mil_cnv_only_cv.py`, so it is not just a lightweight reader.

Reuse for LGD2+: possible, but requires manual review.

Arguments that must change from LGD3+/legacy to LGD2+:

- task/condition registry must point to `NextBiopsyProgression_LGD2plus`;
- model must be `cnv_random_forest`;
- resolution/mask should match `windows_armdiff_plus_arms_plus_cx`;
- input cohort/campaign must be the LGD2+ 20260319 campaign;
- output root must be external.

Command template, not yet verified:

```bash
python scripts/cnv_feature_importance.py   --mode build_worklist   --out_root analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance   --task_registry <LGD2_TASK_REGISTRY_JSON_OR_CSV>   --worklist_csv analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance/admin/importance_worklist.csv

python scripts/cnv_feature_importance.py   --mode row   --worklist_csv analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance/admin/importance_worklist.csv   --row_idx <ROW_INDEX>   --out_root analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance

python scripts/cnv_feature_importance.py   --mode aggregate   --worklist_csv analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance/admin/importance_worklist.csv   --out_root analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance
```

External inputs: LGD2+ cohort, CNV feature table/matrix, model settings/worklist registry. These were not validated in this stage.

Git policy: aggregate top-window summaries may be reduced and committed; raw importance arrays, fitted models, feature matrices, and logs stay external.

## `scripts/cnv_bins_to_genes.py`

What it appears to do: maps selected CNV bins/windows to overlapping genes using a mask file, bin map CSV, optional importance CSV, and GTF.

Reuse for LGD2+: yes after top LGD2+ windows exist.

Command template, not yet verified:

```bash
python scripts/cnv_bins_to_genes.py   --mask_file <LGD2_SELECTED_MASK_FILE>   --binmap_csv <LGD2_BINMAP_CSV>   --importance_csv analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance/<TOP_WINDOWS_OR_IMPORTANCE>.csv   --importance_col <IMPORTANCE_COLUMN>   --gtf_path <GENE_ANNOTATION_GTF>   --out_dir analysis/lgd2_interpretation_regeneration_20260707/cnv_gene_maps   --top_n 200
```

External inputs: selected mask, bin map, importance CSV, gene annotation GTF. Legacy binmaps exist under `analysis/cnv_explainability/binmaps/`, but LGD2+ selected top windows are missing.

Git policy: reduced top-gene summaries can be committed if small; full mapping tables stay external unless reviewed.

## `scripts/export_clinician_cnv_window_gene_summaries.py`

What it appears to do: exports clinician-facing top-window/top-gene summaries from an existing case batch with `cnv_region_gene_mapping` outputs.

Reuse for LGD2+: yes after the selected 8-case LGD2+ external case folders exist.

Command template, not yet verified:

```bash
python scripts/export_clinician_cnv_window_gene_summaries.py   --batch_root analysis/lgd2_interpretation_regeneration_20260707   --top_n 10
```

External inputs: regenerated per-case folders containing `cnv_region_gene_mapping/*.csv` and selected-case metadata.

Git policy: final top-window/top-gene batch summaries may be committed if small and deidentified; per-case raw mappings and plots stay external.

## Summary decision

Optional safe run was not performed. Required feature/model/worklist inputs are not yet validated, and running `cnv_feature_importance.py` may refit or compute heavy importances. The safe next action is to validate the LGD2+ task registry and feature/model paths externally, then run into `analysis/lgd2_interpretation_regeneration_20260707/`.
