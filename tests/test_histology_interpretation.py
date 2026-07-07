from tempfile import TemporaryDirectory
from pathlib import Path

import pandas as pd

from barrett.evaluation.histology_interpretation import (
    build_wsi_case_manifest,
    histology_sentence,
    summarize_histology_outputs,
)


def toy_cases():
    return pd.DataFrame(
        [
            {
                "case_id": "A_true_positive_early_01",
                "category": "A_true_positive_early",
                "patient_id": "P1",
                "biopsy_id": "B1",
                "sample_id": "S1",
                "slide_id": "slide1.ndpi",
                "true_label": 1,
                "image_probability": 0.9,
                "early_fusion_probability": 0.95,
                "DaysFromCurrentToEvent": 365,
            },
            {
                "case_id": "C_false_positive_12",
                "category": "C_false_positive",
                "patient_id": "P2",
                "biopsy_id": "B2",
                "sample_id": "S2",
                "slide_id": "slide2.ndpi",
                "true_label": 0,
                "image_probability": 0.8,
                "early_fusion_probability": 0.7,
                "DaysFromCurrentToEvent": 0,
            },
        ]
    )


def toy_manifest():
    return pd.DataFrame(
        [
            {
                "result_id": "lgd2_image_uni2",
                "prediction_file": "predictions_image_fold{1..5}.csv",
            },
            {
                "result_id": "lgd2_early_fusion_uni2",
                "prediction_file": "predictions_fusion_fold{1..5}.csv",
            },
        ]
    )


def test_wsi_manifest_preserves_early_and_at_event_flags():
    df, warnings = build_wsi_case_manifest(toy_cases(), toy_manifest(), external_root="/missing")
    assert len(df) == 2
    assert bool(df.loc[df["case_id"] == "A_true_positive_early_01", "is_early_prediction_only"].iloc[0]) is True
    assert bool(df.loc[df["case_id"] == "C_false_positive_12", "is_at_event"].iloc[0]) is True
    assert any("prediction files" in w for w in warnings)


def test_wsi_manifest_warns_when_feature_paths_missing():
    df, _ = build_wsi_case_manifest(toy_cases(), toy_manifest(), external_root="/missing")
    assert "feature_index_row_missing" in df["warnings"].iloc[0]


def test_histology_summary_missing_output_safe():
    manifest = pd.DataFrame(
        [
            {
                "case_id": "A_true_positive_early_01",
                "case_category": "A",
                "patient_id": "P1",
                "slide_id": "slide1.ndpi",
                "true_label": 1,
                "image_probability": 0.9,
                "fusion_probability": 0.95,
            }
        ]
    )
    with TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing"
        df, warnings = summarize_histology_outputs(manifest, missing)
    assert len(df) == 1
    assert df["top_patch_refs"].iloc[0] == "MISSING"
    assert any("not found" in w for w in warnings)


def test_histology_summary_loads_fake_top_patch_csv():
    manifest = pd.DataFrame(
        [
            {
                "case_id": "A_true_positive_early_01",
                "case_category": "A",
                "patient_id": "P1",
                "slide_id": "slide1.ndpi",
                "true_label": 1,
                "image_probability": 0.9,
                "fusion_probability": 0.95,
            }
        ]
    )
    with TemporaryDirectory() as tmp:
        top_csv = Path(tmp) / "top.csv"
        pd.DataFrame(
            [{"case_id": "A_true_positive_early_01", "top_patch_refs": "patch_001;patch_002"}]
        ).to_csv(top_csv, index=False)
        df, warnings = summarize_histology_outputs(manifest, Path(tmp), top_patch_csv=top_csv)
    assert df["top_patch_refs"].iloc[0] == "patch_001;patch_002"
    assert "not found" not in " ".join(warnings)


def test_histology_sentence_mentions_missing_outputs():
    row = pd.Series({"case_id": "case1", "image_probability": 0.1, "fusion_probability": 0.2})
    assert "not regenerated" in histology_sentence(row, has_outputs=False)
