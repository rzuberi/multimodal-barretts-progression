# Model Code Migration Plan

Old model code was inspected only enough to identify source locations and coupling. No training code or heavy dependencies were copied in this stage.

| model family | old source path | dependencies | safe to migrate now? | cleanup needed |
|---|---|---|---|---|
| CNV-only | `scripts/run_mil_cnv_only_cv.py`; `scripts/run_cnv_only_candidate_fold.py`; `scripts/build_cnv_masks.py` | scikit-learn/xgboost-style estimators, CNV mask builders, campaign tables | No | Extract estimator factories and CNV mask schemas from CV launch code; remove HPC path assumptions. |
| image-only MIL | `image_mil/models.py`; `scripts/run_mil_cv.py` | PyTorch, MIL bag tensors, feature loaders | Not yet | Separate pure model definitions from feature IO and training loops; add dependency policy for PyTorch. |
| late fusion | `scripts/run_late_fusion_cv.py`; `scripts/run_late_fusion_matrix.py`; `scripts/run_foundation_combo_fusion_matrix.py` | saved OOF predictions, pandas/numpy, cohort joins | Maybe later | Extract lightweight score-fusion logic after patient-level reporting code is stable. |
| early fusion | `image_mil/multimodal.py`; `scripts/run_mil_multimodal_cv.py` | PyTorch, CNV vectors, MIL bags, time covariates | Not yet | Split `EarlyFusionMLP` from dataloaders, CLI args, Slurm/campaign assumptions. |
| intermediate fusion | `image_mil/multimodal.py`; `scripts/run_mil_multimodal_cv.py` | PyTorch, attention MIL, CNV branch | Not yet | Extract `IntermediateABMILCNV` and minimal config dataclass; avoid importing training script globals. |
| co-attention | `image_mil/multimodal.py`; `scripts/run_mil_multimodal_cv.py` | PyTorch, cross-modal attention, MIL bags | Not yet | Extract `CoAttnABMILCNV`, document tensor contracts, add toy shape tests before use. |

Recommendation: keep this repo evaluation-first until Chapter 1 tables are locked. Migrate model definitions only when a concrete rerun or interpretability task requires them.

