from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.feature_views import canonical_cnv_view, canonical_uni2_index, feature_view_audit  # noqa: E402


def _matched() -> pd.DataFrame:
    return pd.DataFrame({
        "canonical_row_key": ["1", "2", "3"],
        "patient_id": ["P1", "P1", "P2"],
        "cnv_id": ["C1", "C1", "C2"],
        "slide_ref": ["A.ndpi", "B.ndpi", "C.ndpi"],
    })


def test_cnv_view_preserves_shared_profile_rows():
    source = pd.DataFrame({"sample_id": ["C1", "C2"], "f1": [1.0, 2.0]})
    out = canonical_cnv_view(_matched(), source)
    assert out["sample_id"].tolist() == ["1", "2", "3"]
    assert out["source_cnv_feature_id"].tolist() == ["C1", "C1", "C2"]
    assert out["f1"].tolist() == [1.0, 1.0, 2.0]


def test_cnv_view_fails_missing_source():
    source = pd.DataFrame({"sample_id": ["C1"], "f1": [1.0]})
    with pytest.raises(ValueError, match="missing"):
        canonical_cnv_view(_matched(), source)


def test_uni2_index_maps_pair_and_remaps_paths(tmp_path):
    paths = []
    rows = []
    for cnv, slide in [("C1", "A.ndpi"), ("C1", "B.ndpi"), ("C2", "C.ndpi")]:
        path = tmp_path / f"{slide}.npz"
        path.touch()
        paths.append(path)
        rows.append({"sample_id": cnv, "image_basename": slide, "npz_path": str(path), "status": "ok"})
    out = canonical_uni2_index(_matched(), pd.DataFrame(rows))
    assert out["sample_id"].tolist() == ["1", "2", "3"]
    assert out["path_exists"].all()


def test_uni2_index_rejects_ambiguous_pair(tmp_path):
    path = tmp_path / "a.npz"
    path.touch()
    source = pd.DataFrame([
        {"sample_id": "C1", "image_basename": "A.ndpi", "npz_path": str(path)},
        {"sample_id": "C1", "image_basename": "A.ndpi", "npz_path": str(path)},
    ])
    with pytest.raises(ValueError, match="ambiguous"):
        canonical_uni2_index(_matched(), source)


def test_feature_audit_exact_sets(tmp_path):
    cnv = canonical_cnv_view(_matched(), pd.DataFrame({"sample_id": ["C1", "C2"], "f1": [1, 2]}))
    idx_rows = []
    for cnv_id, slide in [("C1", "A.ndpi"), ("C1", "B.ndpi"), ("C2", "C.ndpi")]:
        path = tmp_path / f"{slide}.npz"
        path.touch()
        idx_rows.append({"sample_id": cnv_id, "image_basename": slide, "npz_path": str(path)})
    uni2 = canonical_uni2_index(_matched(), pd.DataFrame(idx_rows))
    audit = feature_view_audit(_matched(), {"cnv": cnv}, uni2)
    assert audit["status"].eq("PASS").all()
