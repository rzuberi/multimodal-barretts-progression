# LGD2+ Final Foundation Provenance (Phase 0)

- Clean repo branch: `chapter1-final-analysis-foundation` (from `main` @ `1d56fb3`).
- Test/analysis env: `/home/zuberi01/miniforge3/envs/erin/bin/python` (pandas, numpy, sklearn 1.5.2).
- Model-training env (external): `.conda_mil` / campaign envs (used only by the deferred Phase 8 rerun).
- Source master: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
  (60 columns incl. CurrentGradeInt, LGDStreakSoFar, NextBiopsyLabel, Date, NextBiopsyDate,
  DaysToNextBiopsy, EventDate/EventType, DaysFromCurrentToEvent, NextBiopsyProgression_LGD2plus).
- Developmental campaign (regression reference, NOT reused as final):
  `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`.
- Source hashes are recorded in the external release `cohort_release_metadata.json`
  (source_master_sha256, lgd2/pre_event module hashes, code git commit).

## Endpoint/split source scripts inventoried
- Canonical master: external derivation (upstream; EventDate uses an LGDx3 rule — see below).
- New endpoint/eligibility: `src/barrett/labels/lgd2.py`, `src/barrett/data/pre_event.py`, `scripts/17`.
- New matched set + splits: `src/barrett/data/matched_cohort.py`, `src/barrett/data/splits.py`, `scripts/18`.
- CNV-only / image / fusion trainers (external, Phase 8): `scripts/run_mil_cnv_only_cv.py`,
  `scripts/run_mil_cv.sh`, `scripts/run_mil_multimodal_cv.py` (image_mil package).

## Key provenance finding
The canonical `EventDate` column was generated with an **LGDx3 (three-consecutive-LGD)** rule
(10/38 event patients disagree with the locked two-LGD timeline). The locked endpoint column
itself is two-LGD-consistent (0/921 disagreements). Eligibility therefore derives the event
boundary from the full per-patient timeline (every patient starts at biopsy index 1) under the
locked two-consecutive-LGD rule; canonical `EventDate` is NOT used.
