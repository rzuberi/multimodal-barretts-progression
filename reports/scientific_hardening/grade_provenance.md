# Grade Provenance (Phase 0.3)

## Where raw pathology grades originate (Verified)
- The repo **consumes** grade columns from an **external master CSV**, referenced via `docs/final_results_manifest.csv` (`result_id == lgd2_primary_cohort`) and env var `BARRETTS_EXPERIMENT_ROOT`. Master path: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv` (60 cols, 959 rows).
- **Grade columns (`CurrentGradeInt`, `CurrentGradeNorm`, `NextBiopsyLabel`, `LGDStreakSoFar`, `MaxPathologySoFar`, `max_pathology`) are READ but never ASSIGNED anywhere in the repo.** An assignment-pattern grep (`<col>=`, excluding `==`/`!=` comparisons and synthetic fixtures) across `src/` and `scripts/` for all six columns returns **zero matches** — none is ever written. A separate presence grep confirms the only files referencing them are *readers* (`lgd2.py`, `pre_event.py`, `03_make_cohort_table.py`, `31_build_lgd2_advanced_feature_views.py`; `make_synthetic_fixtures.py` assigns them only for test fixtures).

## Is the upstream master-table derivation version-controlled? (Verified: NO)
- **The worst-grade collapse and the `LGDStreakSoFar` / `NextBiopsyLabel` computation happen UPSTREAM of this repo, in the master-CSV derivation, which is NOT in this repository.** This is a genuine reproducibility gap ([HIGH] risk): the endpoint *rule* is version-controlled (`lgd2.py`), but the *inputs to that rule* (the collapsed per-timepoint grade and the streak) are produced by an external, unversioned pipeline.

## How multiple biopsy grades at one timepoint are collapsed (Verified)
- Collapse is **worst-grade per surveillance timepoint**, performed **upstream** (not in-repo). Evidence: in the frozen cohort, `CurrentGradeInt` shows **0/356 within-timepoint variation** — every timepoint already carries a single collapsed grade. The raw pre-collapse per-biopsy grades are **absent from the frozen release**.
- **Can raw pre-collapse biopsy-level grades be recovered?** [Unknown] — not from the frozen release; only from the upstream master derivation / source pathology records, which are outside this repo.

## Field construction (Verified reading of the rule that consumes them)
| Field | Meaning | Constructed where |
|---|---|---|
| `CurrentGradeInt` | Collapsed index grade, integer: 0/1 ND/IND, 2 LGD, 3+ HGD/IMC/OAC | Upstream (external) |
| `CurrentGradeNorm` | Normalised grade label (NDBE/ID/LGD/HGD/IMC) | Upstream (external) |
| `NextBiopsyLabel` | Collapsed grade integer of the next surveillance biopsy | Upstream (external) |
| `LGDStreakSoFar` | Count of consecutive LGD biopsies up to and INCLUDING current (past+current only) | Upstream (external) |
| `max_pathology` | Worst grade seen so far (0..5) | Upstream (external) |

## Would grade information used by a model have been available at prediction time?
- **`CurrentGradeInt`/`CurrentGradeNorm`/`LGDStreakSoFar`/`max_pathology` describe the CURRENT and PAST biopsies -> available at prediction time.** They are prediction-time-safe as clinical features.
- **`NextBiopsyLabel` is the OUTCOME -> must NEVER be a feature.**
- Caveat: `CurrentGradeInt` is a *worst-grade-collapsed* value; a model using it assumes the pathologist's worst-grade read is available at prediction time (it is, in routine practice).

## Flow diagram
```
[source pathology records]  (outside repo, [U] location)
        |  worst-grade collapse per (patient,timepoint)   <-- UPSTREAM, unversioned
        v
[external master CSV: derived_master.csv]  CurrentGradeInt, CurrentGradeNorm,
        |                                  NextBiopsyLabel, LGDStreakSoFar, max_pathology
        |  read via manifest (BARRETTS_EXPERIMENT_ROOT)
        v
[repo: src/barrett/labels/lgd2.py]  derive_next_biopsy_lgd2plus()  <-- VERSIONED (endpoint rule)
        |
        v
[repo: src/barrett/data/pre_event.py]  build_pre_event_flags()      <-- VERSIONED (eligibility)
        |
        v
[frozen release: pre_event_cohort.csv / matched_manifest.csv]  strict_pre_event_eligible, endpoint
```
