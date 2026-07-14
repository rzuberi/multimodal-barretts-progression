#!/usr/bin/env python
"""Generate a synthetic master-cohort CSV matching the real data contract.

Produces a **fully synthetic** table (random values, fake paths) that conforms to
the column schema in ``docs/data_contract.md``. Its purpose is to let anyone
inspect and dry-run the pipeline — cohort derivation, label logic, split
assignment, metric assembly — WITHOUT access to the private CRUK dataset.

It contains no real patient data of any kind. Every identifier, date, and path
is randomly generated. The file is written outside Git by default (the
no-data policy still forbids committing any ``*master*.csv``); use it locally or
point pipeline scripts at it via ``$BARRETTS_MASTER_CSV``.

Usage:
    python scripts/make_synthetic_fixtures.py --out /tmp/synthetic_master.csv \
        --n-patients 40 --seed 0
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Columns required by docs/data_contract.md
GRADES = ["ND", "IND", "LGD", "HGD", "IMC", "OAC"]
GRADE_INT = {"ND": 0, "IND": 1, "LGD": 2, "HGD": 3, "IMC": 4, "OAC": 5}


def generate(n_patients: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_patients):
        pid = f"SYN{p:04d}"
        n_biopsies = int(rng.integers(2, 7))
        # a synthetic biopsy timeline with dates
        start = np.datetime64("2010-01-01") + rng.integers(0, 2000).astype("timedelta64[D]")
        gaps = rng.integers(180, 900, size=n_biopsies).cumsum()
        dates = start + gaps.astype("timedelta64[D]")
        progressor = rng.random() < 0.33
        for b in range(n_biopsies):
            grade = rng.choice(GRADES, p=[0.45, 0.15, 0.25, 0.08, 0.04, 0.03])
            next_grade = GRADES[min(len(GRADES) - 1, GRADE_INT[grade] + int(rng.integers(0, 3)))]
            next_int = GRADE_INT[next_grade]
            is_last = b == n_biopsies - 1
            next_date = dates[b + 1] if not is_last else np.datetime64("NaT")
            days_to_next = (next_date - dates[b]).astype("timedelta64[D]").astype(float) if not is_last else np.nan
            lgd2plus = int((next_int >= 3) or (next_int == 2 and rng.random() < 0.4)) if not is_last else 0
            rows.append({
                "PatientID": pid,
                "BiopsyID_int": p * 100 + b,
                "SampleID": f"{pid}_S{b}",
                "ImageAbsPath": f"/synthetic/imaging/{pid}_S{b}.svs",
                "CNVAbsPath": f"/synthetic/cnv/{pid}_S{b}.npy",
                "Progressor_label": int(progressor),
                "CurrentGradeNorm": grade,
                "CurrentGradeInt": GRADE_INT[grade],
                "NextBiopsyLabel": next_int if not is_last else np.nan,
                "NextBiopsyProgression_LGD2plus": lgd2plus,
                "NextBiopsyProgression_LGD3plus": int(next_int >= 3) if not is_last else 0,
                "Date": np.datetime_as_string(dates[b], unit="D"),
                "NextBiopsyDate": np.datetime_as_string(next_date, unit="D") if not is_last else "",
                "DaysToNextBiopsy": days_to_next,
                "EventDate": "",
                "EventType": "LGD2plus" if progressor else "",
                "DaysFromCurrentToEvent": float(rng.integers(100, 1500)) if progressor else np.nan,
                "MonthsBeforeLastBiopsy": float(n_biopsies - b),
                "AtRisk_1y": 1, "AtRisk_2y": 1, "AtRisk_3y": 1, "AtRisk_4y": 1, "AtRisk_5y": 1,
                "has_image": 1, "has_cnv": 1,
                "included_in_multimodal_cohort": 1,
                "included_in_cnv_only_cohort": 1,
                "is_at_event": 0,
                "is_early_prediction_sample": int(rng.random() < 0.5),
                "exclusion_reason": "",
                "patient_id_for_split": pid,
                "fold_id": p % 5,
                "heldout_patient_id": pid,
            })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="/tmp/synthetic_master.csv",
                    help="Output path (kept OUTSIDE the repo by default).")
    ap.add_argument("--n-patients", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    df = generate(args.n_patients, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {out}  ({len(df)} synthetic rows, {df.PatientID.nunique()} patients)")
    print(f"columns: {len(df.columns)}")
    print(f"LGD2+ positive rows: {int(df.NextBiopsyProgression_LGD2plus.sum())}")


if __name__ == "__main__":
    main()
