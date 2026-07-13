"""Reproducible LGD2+ current-event and next-biopsy endpoint derivation.

Locked rules (see docs/final_analysis_foundation_implementation_plan.md):

- A biopsy is an LGD2+ event at the current timepoint when
  ``CurrentGradeInt >= 3`` (HGD/IMC/OAC) OR it completes two consecutive LGD
  biopsies (``CurrentGradeInt == 2`` and ``LGDStreakSoFar >= 2``).
- The next-biopsy endpoint is positive when the next biopsy is HGD/IMC/OAC
  (``NextBiopsyLabel >= 3``) OR it completes two consecutive LGD biopsies
  (``NextBiopsyLabel == 2`` and the current streak is already >= 1).

Grade integer convention (``CurrentGradeInt``/``NextBiopsyLabel``): 0/1 = ND/IND,
2 = LGD, 3+ = HGD/IMC/OAC.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HGD_PLUS = 3
LGD = 2


def _num(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


def current_grade_is_event(current_grade_int, lgd_streak) -> pd.Series:
    """Vectorized current-timepoint LGD2+ event flag. NaN grade -> False."""
    cgi = _num(current_grade_int)
    streak = _num(lgd_streak)
    return ((cgi >= HGD_PLUS) | ((cgi == LGD) & (streak >= 2))).fillna(False)


def derive_next_biopsy_lgd2plus(next_biopsy_label, lgd_streak) -> pd.Series:
    """Vectorized next-biopsy LGD2+ endpoint. Returns 1.0/0.0, NaN when label unknown.

    ``next_biopsy_label == 2`` (next is LGD) is positive only when the current
    streak is already >= 1, i.e. the next biopsy completes two consecutive LGD.
    """
    nbl = _num(next_biopsy_label)
    streak = _num(lgd_streak)
    pos = (nbl >= HGD_PLUS) | ((nbl == LGD) & (streak >= 1))
    out = pos.astype(float)
    out[nbl.isna()] = np.nan
    return out
