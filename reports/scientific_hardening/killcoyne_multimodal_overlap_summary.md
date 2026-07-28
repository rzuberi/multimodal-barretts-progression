# Killcoyne multimodal overlap — summary (Phase 5.1)

## Cohort linkage (Verified, keyed on BiopsyID_real / PSID `ps##.#####`)
- Killcoyne discovery cohort: 777 sample rows → **345 distinct pathology-block PSIDs**.
- **329/345 (95%) map to the local master**; **242 PSIDs fall in the strict-eligible multimodal cohort**.
- These map to **69 of the 150 multimodal patients**, and that 69-patient set is **entirely a subset of the 150** (`subset_of_150 = True`).

## Modality availability on the eligible overlap (454 rows / 69 patients)
| Modality | Rows available |
|---|---|
| CNV (shallow WGS path) | 454 / 454 |
| H&E (image path) | 454 / 454 |
| UNI2 embeddings | 454 / 454 |
| GigaPath embeddings | 454 / 454 |
| Virchow2 embeddings | 454 / 454 |

Full multimodal data are present for every overlapping eligible row.

## Outcome & composition
- Local LGD2+ outcome on the overlap: **54 positive rows / 27 positive patients** (of 69).
- Index grade: NDBE 333, LGD 69, indefinite 52.
- Biopsies per patient: median 6, max 19.

## Deliverables
`killcoyne_multimodal_overlap_counts.csv`, `killcoyne_multimodal_overlap_summary.json`, `killcoyne_overlap_raw.txt`.
