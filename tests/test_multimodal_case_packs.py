import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT = Path("scripts/13_build_lgd2_multimodal_case_packs.py")
spec = importlib.util.spec_from_file_location("case_packs", SCRIPT)
case_packs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case_packs)


def test_fusion_help_hurt_labels():
    assert case_packs.fusion_help_hurt_label(False, True, True, {"cnv": 0.4, "image": 0.9, "fusion": 0.8}) == "fusion_rescues_cnv"
    assert case_packs.fusion_help_hurt_label(True, False, True, {"cnv": 0.8, "image": 0.4, "fusion": 0.9}) == "fusion_rescues_image"
    assert case_packs.fusion_help_hurt_label(True, False, False, {"cnv": 0.8, "image": 0.4, "fusion": 0.3}) == "fusion_hurts"
    assert case_packs.fusion_help_hurt_label(False, False, False, {"cnv": 0.2, "image": 0.3, "fusion": 0.1}) == "all_fail"


def test_histology_inventory_detects_missing_panel():
    selection = pd.DataFrame(
        [
            {
                "case_id": "case_a",
                "histology_output_ref": "external/case_a",
            }
        ]
    )
    audit = pd.DataFrame(
        [
            {"case_id": "case_a", "output_file": "top_tiles_grid.png", "exists": True, "status": "PASS"},
            {"case_id": "case_a", "output_file": "bottom_tiles_grid.png", "exists": True, "status": "PASS"},
            {"case_id": "case_a", "output_file": "heatmap_overlay.png", "exists": True, "status": "PASS"},
            {"case_id": "case_a", "output_file": "heatmap_overlay_shuffle.png", "exists": False, "status": "FAIL"},
            {"case_id": "case_a", "output_file": "tile_scores.csv", "exists": True, "status": "PASS"},
            {"case_id": "case_a", "output_file": "metadata.json", "exists": True, "status": "PASS"},
        ]
    )
    out = case_packs.build_histology_inventory(selection, audit)
    assert bool(out.loc[0, "histology_panel_ready"]) is False
    assert "heatmap_overlay_shuffle.png" in out.loc[0, "warnings"]


def test_blocked_cnv_top_windows_marks_missing():
    selection = pd.DataFrame(
        [
            {
                "case_id": "case_a",
                "cnv_output_ref": "external/cnv/case_a",
                "warnings": "missing cnv",
            }
        ]
    )
    out = case_packs.blocked_cnv_top_windows(selection)
    assert out.loc[0, "chromosome"] == "BLOCKED"
    assert "not generated" in out.loc[0, "interpretation_note"]
