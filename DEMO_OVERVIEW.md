# Multimodal AI for Early Cancer Progression Detection

AI system for combining pathology, genomics, and longitudinal biopsy history to estimate cancer progression risk earlier.

## Problem

- Hospitals generate large volumes of histopathology images.
- They also generate genomic copy number variation (CNV) data.
- Patients have longitudinal biopsy timelines across surveillance visits.
- These signals are rarely integrated for early cancer progression detection.

## Multimodal Data Sources

```mermaid
flowchart LR
    A[Histopathology Slides<br/>WSI] --> B[Foundation Model Features]
    C[Copy Number Variation<br/>CNV] --> D[Genomic Feature Engineering]
    E[Longitudinal Biopsy Timeline] --> F[Temporal Representation]

    B --> G[Multimodal Model]
    D --> G
    F --> G

    G --> H[Cancer Progression Prediction]
```

## System Architecture

```mermaid
flowchart TD
    A[Clinical Data]

    A --> B[Whole Slide Images]
    B --> C[Feature Extraction<br/>Foundation Models]

    A --> D[Genomic Data<br/>CNV]
    D --> E[Feature Engineering]

    A --> F[Patient Timeline]
    F --> G[Longitudinal Structure]

    C --> H[Multimodal Model]
    E --> H
    G --> H

    H --> I[Progression Risk Prediction]
```

## Experiment Framework

- Train multiple model variants.
- Test different feature sets and modality combinations.
- Track experiments reproducibly.
- Compare performance across model families and tasks.

## Terminal Usage

```bash
git clone https://github.com/rzuberi/multimodal-barretts-progression
cd multimodal-barretts-progression

python train_model.py --config configs/example.yaml
```

- Runs headless training.
- Supports custom datasets.
- Allows testing new models and feature pipelines.

## Goal

- Detect cancer progression earlier.
- Integrate multimodal clinical data.
- Build reusable research infrastructure.
