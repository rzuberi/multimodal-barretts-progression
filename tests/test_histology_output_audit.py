import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "12_audit_lgd2_histology_output.py"
spec = importlib.util.spec_from_file_location("histology_output_audit", SCRIPT)
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def _make_valid_output(root: Path) -> None:
    for name in ["top_tiles_grid.png", "bottom_tiles_grid.png", "heatmap_overlay.png", "heatmap_overlay_shuffle.png"]:
        Image.new("RGB", (10, 10), (255, 0, 0)).save(root / name)
    pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "score_raw": [0.9, 0.4, 0.1]}).to_csv(
        root / "tile_scores.csv", index=False
    )
    (root / "metadata.json").write_text(
        json.dumps({"sample_id": "S1", "patient_id": "P1", "model": "abmil", "n_tiles_used": 3}),
        encoding="utf-8",
    )


def test_valid_output_audit_passes():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_valid_output(root)
        audit, details, tile_df = audit_mod.audit_output_dir("case1", root)
    assert bool(details["structurally_valid"]) is True
    assert int(details["n_tiles_scored"]) == 3
    assert len(audit) == 6
    assert len(tile_df) == 3


def test_missing_output_detection_fails():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_valid_output(root)
        (root / "heatmap_overlay.png").unlink()
        audit, details, _ = audit_mod.audit_output_dir("case1", root)
    assert bool(details["structurally_valid"]) is False
    assert "missing_or_empty" in audit["warning"].astype(str).tolist()


def test_interpretation_summary_has_top_and_bottom_refs():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_valid_output(root)
        _, details, tile_df = audit_mod.audit_output_dir("case1", root)
        case = pd.Series({"case_id": "case1", "patient_id": "P1", "sample_id": "S1"})
        summary = audit_mod.interpretation_summary(case, details, tile_df)
    assert "x=1" in summary["top_5_tile_refs"].iloc[0]
    assert "x=3" in summary["bottom_5_tile_refs"].iloc[0]
