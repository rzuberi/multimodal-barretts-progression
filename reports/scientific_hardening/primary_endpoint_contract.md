# Primary Endpoint Contract — NextBiopsyProgression_LGD2plus

**Verified this session by independent reconstruction from source columns.** Implementation: `src/barrett/labels/lgd2.py::derive_next_biopsy_lgd2plus`; temporal eligibility: `src/barrett/data/pre_event.py::build_pre_event_flags`. Grade-integer convention (`CurrentGradeInt`/`NextBiopsyLabel`): 0/1 = ND/indefinite, 2 = LGD, 3+ = HGD/IMC/OAC.

## Exact Boolean definition (next-biopsy endpoint)
```
positive  <=>  (NextBiopsyLabel >= 3)  OR  (NextBiopsyLabel == 2 AND LGDStreakSoFar >= 1)
NaN       <=>  NextBiopsyLabel is missing
otherwise negative
```

## Answers to the required questions
| Question | Answer (Verified) |
|---|---|
| What "LGD2+" means | The **next** biopsy is at least LGD *when it completes two consecutive LGD*, or is HGD/IMC/OAC outright. |
| Consecutive-LGD handling | A next LGD (`NextBiopsyLabel==2`) is an event **only if `LGDStreakSoFar >= 1`** (current biopsy already LGD, so the next completes a **second consecutive** LGD). A lone LGD after non-LGD is **not** an event. |
| Second consecutive LGD an event? | **Yes.** |
| HGD / IMC / OAC | Always an event (`NextBiopsyLabel >= 3`), regardless of streak. |
| Strictly later biopsy date required? | **Yes** — eligibility requires `next_biopsy_is_future`. Verified: 707/707 have NextBiopsyDate > Date. |
| Same-day events excluded? | **Yes, empirically.** 0/707 equal dates; 0/707 DaysToNextBiopsy==0; 0/707 DaysFromCurrentToEvent==0. (172 same-day rows in the canonical master are all removed by the strict pre-event filter — resolves a prior [U] flag.) |
| Patients without a subsequent biopsy | Excluded (`endpoint_evaluable` needs non-null NextBiopsyLabel; `next_biopsy_is_future` needs a real next biopsy). |
| Multiple biopsies at one timepoint | Grade already collapsed to one value/timepoint upstream (worst-grade); 0/356 timepoints vary. Modelling scores each sample-row, aggregated to patient by max. |
| Future information in eligibility/features? | Eligibility uses the next biopsy's date/label (that IS the endpoint). Model **features** = current CNV + current H&E only; `LGDStreakSoFar` uses past+current biopsies only. No future info in features. |
| Do all 707 rows satisfy the temporal definition? | **Yes** — 707/707 strictly-future, 0 same-day, 0 days-only fallback. |

## Independent reconstruction result
- Rows: **707**; stored pos **107** / neg **600** / NaN 0.
- Derived: pos **107** / neg **600** / NaN 0.
- **Discrepancies: 0 / 707 comparable rows (rate 0.0).**
- **Conclusion: frozen endpoint reproduced exactly. Downstream modelling may proceed.**

## Temporal integrity (Verified)
- NextBiopsyDate > Date: 707/707; equal 0; missing 0.
- DaysToNextBiopsy > 0: 707/707; ==0 0; missing 0.
- Future via days-only (not date): 0.
- DaysFromCurrentToEvent==0 in eval set: 0 (positive: 0).
