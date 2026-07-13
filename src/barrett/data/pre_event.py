"""Strict pre-event LGD2+ cohort derivation and temporal eligibility.

Derives current-event status and the next-biopsy endpoint from source columns,
validates the canonical ``EventDate`` against the two-LGD timeline, and flags each
row's strict-pre-event eligibility with an explicit exclusion reason. See
docs/final_analysis_foundation_implementation_plan.md (Phases 1-2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from barrett.labels.endpoints import LGD2_ENDPOINT
from barrett.labels.lgd2 import current_grade_is_event, derive_next_biopsy_lgd2plus

PATIENT_COL = "PatientID_real"
DATE_TOLERANCE_DAYS = 1  # documented tolerance for date/day-difference agreement


def patient_col(df: pd.DataFrame) -> str:
    return PATIENT_COL if PATIENT_COL in df.columns else "PatientID"


def _dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def _present(s: pd.Series) -> pd.Series:
    v = s.astype("string").str.strip()
    return v.notna() & (v != "") & (v.str.lower() != "nan")


def add_derived_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived current-event flag, derived endpoint, and stored-vs-derived agreement."""
    out = df.copy()
    out["is_lgd2_event_at_current"] = current_grade_is_event(out.get("CurrentGradeInt"), out.get("LGDStreakSoFar"))
    out["derived_NextBiopsyProgression_LGD2plus"] = derive_next_biopsy_lgd2plus(
        out.get("NextBiopsyLabel"), out.get("LGDStreakSoFar")
    )
    stored = pd.to_numeric(out.get(LGD2_ENDPOINT), errors="coerce")
    out["stored_NextBiopsyProgression_LGD2plus"] = stored
    derived = out["derived_NextBiopsyProgression_LGD2plus"]
    evaluable = stored.notna() & derived.notna()
    out["endpoint_agrees"] = np.where(evaluable, stored == derived, np.nan)
    return out


def first_event_date(df: pd.DataFrame) -> pd.Series:
    """Per-patient earliest current-event biopsy Date, derived from the timeline."""
    pc = patient_col(df)
    d = df.copy()
    d["_date"] = _dt(d.get("Date"))
    ev = d[d["is_lgd2_event_at_current"] & d["_date"].notna()]
    return ev.groupby(pc)["_date"].min()


def validate_event_dates(df: pd.DataFrame) -> dict:
    """Compare derived first-event date with canonical EventDate per event patient."""
    pc = patient_col(df)
    derived = first_event_date(df)
    ed = df.copy()
    ed["_ed"] = _dt(ed.get("EventDate"))
    canonical = ed.dropna(subset=["_ed"]).groupby(pc)["_ed"].min()
    both = pd.concat([derived.rename("derived"), canonical.rename("canonical")], axis=1)
    both = both.dropna()
    if both.empty:
        return {"patients_compared": 0, "agree": 0, "disagree": 0, "max_abs_days": None}
    diff = (both["derived"] - both["canonical"]).abs().dt.days
    return {
        "patients_compared": int(len(both)),
        "agree": int((diff <= DATE_TOLERANCE_DAYS).sum()),
        "disagree": int((diff > DATE_TOLERANCE_DAYS).sum()),
        "max_abs_days": int(diff.max()),
        "patients_with_derived_event": int(derived.notna().sum()),
        "patients_with_canonical_event": int(canonical.notna().sum()),
    }


def build_pre_event_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal-eligibility flags, timing evidence, and exclusion_reason."""
    pc = patient_col(df)
    out = add_derived_labels(df)
    out["_date"] = _dt(out.get("Date"))
    out["_nbdate"] = _dt(out.get("NextBiopsyDate"))
    days_next = pd.to_numeric(out.get("DaysToNextBiopsy"), errors="coerce")

    # next biopsy is in the future
    date_future = out["_nbdate"].notna() & out["_date"].notna() & (out["_nbdate"] > out["_date"])
    days_future = days_next > 0
    out["next_biopsy_is_future"] = (date_future | days_future).fillna(False)
    out["timing_evidence_source"] = np.select(
        [date_future.fillna(False), (~date_future.fillna(False)) & days_future.fillna(False)],
        ["next_biopsy_date_gt_date", "days_to_next_biopsy_positive"],
        default="unresolved",
    )

    # endpoint evaluable
    stored = out["stored_NextBiopsyProgression_LGD2plus"]
    nbl = pd.to_numeric(out.get("NextBiopsyLabel"), errors="coerce")
    out["endpoint_evaluable"] = stored.notna() & nbl.notna()

    # post-event: strictly after the patient's first derived event date
    fed = first_event_date(out)
    out["_first_event_date"] = out[pc].map(fed)
    out["is_post_lgd2_event"] = (
        out["_first_event_date"].notna() & out["_date"].notna()
        & (out["_date"] > out["_first_event_date"])
    ).fillna(False)

    # modality availability
    img_ok = _present(out.get("ImageAbsPath", pd.Series(index=out.index, dtype="object")))
    cnv_ok = _present(out.get("CNVAbsPath", pd.Series(index=out.index, dtype="object")))
    out["has_image"] = img_ok
    out["has_cnv"] = cnv_ok

    # exclusion reason (first failing condition, priority order)
    reason = pd.Series("", index=out.index, dtype="object")
    def mark(cond, label):
        m = (reason == "") & cond
        reason[m] = label
    mark(~out["endpoint_evaluable"], "endpoint_not_evaluable")
    mark(out["is_lgd2_event_at_current"], "at_event")
    mark(out["is_post_lgd2_event"], "post_event")
    mark(~out["next_biopsy_is_future"], "next_biopsy_not_future")
    mark(~out["has_image"], "missing_image")
    mark(~out["has_cnv"], "missing_cnv")
    out["exclusion_reason"] = reason
    out["strict_pre_event_eligible"] = reason == ""
    return out.drop(columns=["_date", "_nbdate", "_first_event_date"], errors="ignore")


def cohort_flow(flagged: pd.DataFrame) -> pd.DataFrame:
    """Staged exclusion counts by row / biopsy / patient."""
    pc = patient_col(flagged)
    bcol = "BiopsyID_int" if "BiopsyID_int" in flagged else pc

    def counts(mask, name):
        sub = flagged[mask]
        return {"stage": name, "rows": int(mask.sum()),
                "biopsies": int(sub[bcol].nunique()), "patients": int(sub[pc].nunique())}

    rows = [counts(pd.Series(True, index=flagged.index), "all_rows")]
    for label in ["endpoint_not_evaluable", "at_event", "post_event",
                  "next_biopsy_not_future", "missing_image", "missing_cnv"]:
        rows.append(counts(flagged["exclusion_reason"] == label, f"excluded:{label}"))
    rows.append(counts(flagged["strict_pre_event_eligible"], "strict_pre_event_eligible"))
    elig = flagged[flagged["strict_pre_event_eligible"]]
    ep = pd.to_numeric(elig["stored_NextBiopsyProgression_LGD2plus"], errors="coerce")
    rows.append({"stage": "eligible_positive_rows", "rows": int((ep == 1).sum()),
                 "biopsies": "", "patients": int(elig.loc[ep == 1, pc].nunique())})
    rows.append({"stage": "eligible_negative_rows", "rows": int((ep == 0).sum()),
                 "biopsies": "", "patients": int(elig.loc[ep == 0, pc].nunique())})
    return pd.DataFrame(rows)
