# Multimodal Barrett's Progression

## Very Short Explanation

This project is about trying to tell which Barrett's oesophagus patients look more likely to get worse over time. We use two kinds of information from the same biopsy visit: patterns from histopathology images and patterns from copy-number DNA data. The goal is not to replace doctors, but to see whether combining these signals can help identify higher-risk patients earlier.

## Train On Your Own CNV Data

This public repo now includes a small headless CNV workflow. If you already have shallow whole-genome sequencing copy-number features in a table, you can clone the repo, install the dependencies, train a binary classifier from the terminal, and run inference from the terminal without using notebooks or a GUI.

In simple terms: each row is one biopsy or sample, each numeric column is a copy-number feature, and the model learns to separate two groups such as progressor vs non-progressor. The public repo does **not** include the private Barrett's patient-level training data from our study, but it **does** include reusable code so you can train the same style of elastic-net CNV baseline on your own data.

### 1. Install

```bash
git clone https://github.com/rzuberi/multimodal-barretts-progression.git
cd multimodal-barretts-progression
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Expected input format

Your training CSV should have:

- one row per sample
- one sample identifier column, for example `sample_id`
- one binary label column, for example `label`
- numeric copy-number feature columns such as chromosome-arm values, 5 Mb windows, or other segmented CNV features

Minimal example:

```csv
sample_id,label,cn_1p,cn_1q,cn_3p,cn_17p
S1,0,-0.10,0.02,-0.05,-0.20
S2,1,0.32,0.41,0.15,-0.62
```

The public CLI expects features that are already computed. It does not start from BAMs in this public repo. In practice that means you should first run your own sWGS preprocessing, then export a sample-by-feature CNV table.

### 3. Train a model

```bash
python3 scripts/train_cnv_model.py \
  --train_csv examples/toy_cnv_train.csv \
  --label_col label \
  --id_col sample_id \
  --output_dir outputs/toy_model
```

Optional grouped training if you have repeated biopsies per patient:

```bash
python3 scripts/train_cnv_model.py \
  --train_csv your_train_table.csv \
  --label_col label \
  --id_col sample_id \
  --group_col patient_id \
  --output_dir outputs/patient_grouped_model
```

Training writes:

- `model.joblib`
- `train_metrics.json`
- `cv_predictions.csv`
- `feature_columns.txt`

The training model is a standardized elastic-net logistic regression baseline, which is a reasonable public analogue for CNV-only binary prediction.

### 4. Run inference

```bash
python3 scripts/predict_cnv_model.py \
  --model_path outputs/toy_model/model.joblib \
  --input_csv examples/toy_cnv_infer.csv \
  --id_col sample_id \
  --output_csv outputs/toy_predictions.csv
```

This writes a CSV with:

- sample identifier
- predicted probability for the positive class
- hard class call at the chosen threshold

### 5. Rebuild the public aggregate snapshot

If you only want the public figures and aggregate tables from this repo:

```bash
python3 scripts/build_public_snapshot.py
```

This regenerates the de-identified tables in [data_snapshots](data_snapshots) and figures in [figures](figures).

## What This Public Repo Contains

This GitHub repo is public-safe and aggregate-focused. It contains summary tables, figures, short writeups, and now a small reusable CNV training and inference CLI for users' own data. It does not contain patient identifiers, row-level predictions from the original study, slide embeddings, or private master tables.

## Privacy Boundary

Included:

- aggregate leaderboard tables
- de-identified patient-level summary tables
- static figures and narrative interpretation
- a small public CNV training and inference CLI for users' own data

Excluded:

- patient or sample identifiers from the original study
- row-level predictions from the original study
- private derived cohort tables
- slide embeddings and private training manifests
- any file that could reconstruct patient trajectories

This means the repo is reproducible at the aggregate-report layer and reusable as a public CNV baseline toolkit, but it is not a full public release of the original private multimodal training cohort.

## Main Update In This Snapshot

The March 2026 public update adds three things that were not in the earlier public snapshot:

1. A stricter patient-level next-biopsy analysis where progression is defined more conservatively.
2. A patient-level data-efficiency result showing that reduced pathology input can still work well for one endpoint.
3. Patient-level modality-ablation evidence showing that both image and CNV signals matter.

## New Headline Results

### 1. Strict patient-level next-biopsy progression still looks strong

For the corrected strict endpoint `NextBiopsyProgression_LGD2plus`, the best patient-level model was still a plain multimodal model:

- best multimodal: patient AUC `0.926`
- best image-only: patient AUC `0.865`
- best CNV-only: patient AUC `0.854`
- best routing / MoE: patient AUC `0.887`

This is the cleanest current headline because it uses the stricter progression definition and patient-level evaluation.

Source table:

- [data_snapshots/strict_lgd2_patient_level_headline.csv](data_snapshots/strict_lgd2_patient_level_headline.csv)

### 2. For the progressor task, less pathology data can still work

On `Progressor_label`, the best reduced-patch multimodal model slightly exceeded the best full multimodal baseline at patient level:

- best image-only baseline: `0.879`
- best full multimodal baseline: `0.922`
- best reduced-patch multimodal: `0.927`
- best simplified CNV-only model: `0.869`

So the public story here is not just "bigger models on more data win". For one important patient-level endpoint, a leaner pathology input still kept the signal.

Source table:

- [data_snapshots/progressor_patient_level_data_efficiency.csv](data_snapshots/progressor_patient_level_data_efficiency.csv)

### 3. Modality ablations support a real multimodal signal

Patient-level H200 ablations were rerun under the strict rule. The pattern was:

- `NextBiopsyProgression_LGD2plus`: baseline `0.926`, shuffle image `0.861`, shuffle CNV `0.888`, shuffle both `0.727`
- `Progressor_label`: baseline `0.918`, shuffle image `0.878`, shuffle CNV `0.879`, shuffle both `0.704`

That means both modalities are contributing useful information, and destroying both causes a large collapse in patient-level performance.

Source table:

- [data_snapshots/strict_lgd2_patient_level_modality_ablation.csv](data_snapshots/strict_lgd2_patient_level_modality_ablation.csv)

## Earlier Public Snapshot Still Included

The older public material is still useful and remains in the repo:

- canonical `LGD3plus` next-biopsy snapshot tables
- AtRisk no-leak tables
- biopsy-to-patient aggregation tables
- distance-to-progression and modality-reliance summaries

Those files still matter for the broader story, but they are no longer the cleanest single headline after the stricter patient-level refresh.

## Suggested Reading Order

1. [data_snapshots/strict_lgd2_patient_level_headline.csv](data_snapshots/strict_lgd2_patient_level_headline.csv)
2. [data_snapshots/progressor_patient_level_data_efficiency.csv](data_snapshots/progressor_patient_level_data_efficiency.csv)
3. [data_snapshots/strict_lgd2_patient_level_modality_ablation.csv](data_snapshots/strict_lgd2_patient_level_modality_ablation.csv)
4. [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
5. [SNAPSHOT_PROVENANCE.md](SNAPSHOT_PROVENANCE.md)

## Older Figures And Tables

The earlier public figures and tables are still available:

- [figures/figure1_baseline_headline_auc.png](figures/figure1_baseline_headline_auc.png)
- [figures/figure3_atrisk_noleak_auc.png](figures/figure3_atrisk_noleak_auc.png)
- [figures/figure4_biopsy_patient_aggregation_auc.png](figures/figure4_biopsy_patient_aggregation_auc.png)
- [figures/figure6_distance_to_progression.png](figures/figure6_distance_to_progression.png)
- [figures/figure7_modality_weight_shift.png](figures/figure7_modality_weight_shift.png)

## Limitations

- The original private multimodal training cohort is not included here.
- The public CNV CLI expects precomputed CNV features, not raw BAM-to-feature processing.
- Some analyses remain represented only by derived aggregate tables, not full public pipelines.
- External validation, calibration work, subgroup robustness, and prospective evaluation remain open gaps.

## Provenance And Navigation

- Snapshot provenance and exclusion rules: [SNAPSHOT_PROVENANCE.md](SNAPSHOT_PROVENANCE.md)
- Baseline results summary: [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
- Aggregate source inputs used by the rebuild script: [source_aggregates](source_aggregates)
