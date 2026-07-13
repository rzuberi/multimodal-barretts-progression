# Phase 8 Launch Commands (LGD2+ Final Strict Pre-Event Rerun)

Readiness gates PASS (see `reports/thesis_ch1/lgd2_final_rerun_readiness.md`). The frozen
inputs are external:

```
REL=/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/chapter1_lgd2_final_pre_event_20260713_final
# $REL/pre_event_cohort.csv, matched_manifest.csv, patient_splits.csv, training_manifest.csv,
#      tasks_chapter1_lgd2_final.json, *_metadata.json
```

The training manifest loads via `image_mil.data.load_manifest`; all 5 outer folds are
patient-disjoint (verified). Endpoint resolves via the versioned registry
`$REL/tasks_chapter1_lgd2_final.json`.

## Two prerequisites BEFORE launching (do not skip — jobs will train on wrong data otherwise)

1. **CNV feature source for the frozen cohort.** The CNV-only trainer reads
   `features_5mb_armdiff.csv`, `features_arms.csv`, `cx.csv` from `--base_dir`. The only
   such files found are under `data/killcoyne_*` — a DIFFERENT cohort whose sample_ids do
   not cover the 707 frozen LGD2 samples. Locate (or regenerate from each sample's
   `CNVAbsPath`) the CNV variant sources that cover the frozen `SampleID`s, and set
   `--base_dir` to that directory. Verify every training-manifest `sample_id` is present.
2. **UNI2 feature index for image/fusion families.** The image (ABMIL) and fusion trainers
   need the UNI2 tile-feature index/tensors. Point them at the campaign's UNI2 feature
   index and confirm coverage of the frozen `SampleID`s.

## CNV-only baseline (CPU, epyc) — runnable once prerequisite 1 is met
```bash
CNV_BASE=<dir with features_5mb_armdiff.csv/features_arms.csv/cx.csv covering the 707 samples>
for f in 1 2 3 4 5; do
  echo "$MILPY scripts/run_mil_cnv_only_cv.py \
    --manifest $REL/training_manifest.csv \
    --master_csv data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv \
    --base_dir $CNV_BASE \
    --task_name NextBiopsyProgression_LGD2plus \
    --task_registry $REL/tasks_chapter1_lgd2_final.json \
    --condition all_samples --rep 1 --fold $f \
    --cnv_variant windows_armdiff_plus_arms_plus_cx \
    --run_dir $REL/training/cnv_only"
done > $REL/jobs_cnv_only.txt
# submit as a throttled CPU array (uses the generic wrapper in the outer repo slurm/):
slurm/submit_array.sh --jobs $REL/jobs_cnv_only.txt --partition epyc --gpus 0 \
  --concurrency 5 --cpus 8 --mem 32G --time 04:00:00 --name lgd2_final_cnv
```
`$MILPY` = the training env python (e.g. `.conda_mil/bin/python`).

## Image / fusion families (GPU, h200,cuda) — runnable once prerequisite 2 is met
Use `slurm/submit_gpu_stage.sh` (partition `h200,cuda`) with the same
`--manifest/--task_name/--task_registry`, per Phase 8 order:
UNI2 ABMIL → early fusion → intermediate fusion (nested inner selection) →
late fusion mean → late fusion stacker → (optional) co-attention.

## Collection (after folds complete)
- Validate each run against the artifact contract:
  `python scripts/19_validate_lgd2_training_artifacts.py --predictions <run>/cv_predictions.csv --manifest <run>/completeness.json`
- Only then derive final metrics from the frozen OOF artifacts (Phase 9).

Do not claim the rerun complete until all five outer folds of every primary family pass
artifact validation.
