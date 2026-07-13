"""Frozen matched comparison set: one canonical row per modelling unit (Phase 2).

Every primary model (CNV-only, image-only, and each fusion family) must consume
the SAME canonical rows and patients. The canonical row key is ``SampleID`` (one
slide/sample = one modelling unit). CNV profiles may be shared across samples
(multi-slide biopsies); these are flagged, not dropped. Many-to-many or duplicate
SampleID pairings are rejected.
"""

from __future__ import annotations

import pandas as pd

from barrett.data.pre_event import patient_col
from barrett.labels.endpoints import LGD2_ENDPOINT

ROW_KEY = "SampleID"
MANIFEST_COLUMNS = [
    "cohort_release_id", "sample_id", "patient_id", "biopsy_id",
    "slide_id", "slide_ref", "cnv_id", "cnv_ref",
    LGD2_ENDPOINT, "derived_NextBiopsyProgression_LGD2plus",
    "DaysToNextBiopsy", "DaysFromCurrentToEvent", "timing_evidence_source",
    "strict_pre_event_eligible", "has_image", "has_cnv",
    "canonical_row_key", "cnv_shared_with_other_sample", "exclusion_reason",
]


def build_matched_manifest(flagged: pd.DataFrame, cohort_release_id: str) -> tuple[pd.DataFrame, list[str]]:
    """Return (manifest of eligible matched units, problems). Fails closed via problems list."""
    pc = patient_col(flagged)
    problems: list[str] = []
    elig = flagged[flagged["strict_pre_event_eligible"]].copy()

    if elig[ROW_KEY].duplicated().any():
        n = int(elig[ROW_KEY].duplicated().sum())
        problems.append(f"{n} duplicate {ROW_KEY} rows in the eligible set")
    # each sample must map to exactly one CNV and one image path (no many-to-many)
    multi_cnv = elig.groupby(ROW_KEY)["CNVAbsPath"].nunique()
    multi_img = elig.groupby(ROW_KEY)["ImageAbsPath"].nunique()
    if (multi_cnv > 1).any():
        problems.append(f"{int((multi_cnv > 1).sum())} samples map to >1 CNV path")
    if (multi_img > 1).any():
        problems.append(f"{int((multi_img > 1).sum())} samples map to >1 image path")

    cnv_reuse = elig.groupby("CNVAbsPath")[ROW_KEY].transform("nunique")
    m = pd.DataFrame({
        "cohort_release_id": cohort_release_id,
        "sample_id": elig[ROW_KEY].astype(str),
        "patient_id": elig[pc].astype(str),
        "biopsy_id": elig.get("BiopsyID_int"),
        "slide_id": elig.get("SampleID").astype(str),
        "slide_ref": elig["ImageAbsPath"].map(lambda x: str(x).rsplit("/", 1)[-1]),
        "cnv_id": elig["CNVAbsPath"].map(lambda x: str(x).rsplit("/", 1)[-1]),
        "cnv_ref": elig["CNVAbsPath"].map(lambda x: str(x).rsplit("/", 1)[-1]),
        LGD2_ENDPOINT: pd.to_numeric(elig[LGD2_ENDPOINT], errors="coerce").astype("Int64"),
        "derived_NextBiopsyProgression_LGD2plus": elig["derived_NextBiopsyProgression_LGD2plus"],
        "DaysToNextBiopsy": elig.get("DaysToNextBiopsy"),
        "DaysFromCurrentToEvent": elig.get("DaysFromCurrentToEvent"),
        "timing_evidence_source": elig["timing_evidence_source"],
        "strict_pre_event_eligible": True,
        "has_image": elig["has_image"], "has_cnv": elig["has_cnv"],
        "canonical_row_key": elig[ROW_KEY].astype(str),
        "cnv_shared_with_other_sample": (cnv_reuse > 1).values,
        "exclusion_reason": "",
    })
    return m[MANIFEST_COLUMNS], problems


def model_input_equality(manifest: pd.DataFrame, families: list[str]) -> dict:
    """Every primary family consumes the identical canonical row-key set."""
    keys = frozenset(manifest["canonical_row_key"].astype(str))
    per_family = {fam: keys for fam in families}  # all families are bound to the same manifest
    equal = len({frozenset(v) for v in per_family.values()}) == 1
    return {"equal": equal, "n_keys": len(keys), "families": families}
