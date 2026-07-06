# No-Data Policy

This repository must not contain raw, derived, or patient-level data.

## Forbidden In Git

- Histology slides: `.svs`, `.ndpi`, `.tif`, `.tiff`
- Patch images or generated patient figures: `.png`, `.jpg`, `.jpeg`, `.pdf`
- CNV matrices/profiles/features: `.csv`, `.tsv`, `.npy`, `.npz`, `.h5`, `.hdf5`
- Derived cohort tables and manifests: `.csv`, `.tsv`, `.xlsx`, `.xls`
- Model checkpoints: `.pt`, `.pth`, `.ckpt`, `.pkl`, `.pickle`
- Prediction files and patient-level result tables
- Raw clinical metadata or scrape outputs
- Slurm logs and large generated reports

## Allowed In Git

- Markdown documentation.
- Small scripts that operate on external paths.
- Small schema/config examples with no patient data.
- Audit summaries that contain paths, counts, and methodology but no raw tables.

## Required Check Before Push

Run:

```bash
scripts/assert_no_data_tracked.sh
```

The script checks the Git index for forbidden file extensions and data/result directory names.
