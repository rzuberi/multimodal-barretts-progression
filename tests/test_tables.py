import pandas as pd

from barrett.evaluation.tables import markdown_table, rank_models, select_representative_models


def toy_metrics():
    return pd.DataFrame(
        {
            "aggregation": ["patient_max"] * 4,
            "result_id": ["cnv", "img1", "img2", "mm"],
            "model_family": ["CNV-only", "histology-only", "histology-only", "multimodal"],
            "fusion_type": ["none", "none", "none", "early_fusion"],
            "auprc": [0.5, 0.7, 0.65, 0.8],
            "roc_auc": [0.6, 0.75, 0.8, 0.82],
            "sensitivity": [0.4, 0.5, 0.6, 0.7],
            "progressors_detected": [4, 5, 6, 7],
            "false_positives_per_detected_progressor": [0.1, 1.0, 0.5, 0.8],
        }
    )


def test_rank_models_prefers_auprc_then_auc():
    ranked = rank_models(toy_metrics())
    assert ranked.iloc[0]["result_id"] == "mm"
    assert ranked.iloc[1]["result_id"] == "img1"


def test_select_representative_models_gets_best_image():
    selected = select_representative_models(toy_metrics())
    image = selected[selected["comparison_slot"].eq("best_image_only")]
    assert image.iloc[0]["result_id"] == "img1"


def test_markdown_table_contains_headers():
    text = markdown_table(toy_metrics().head(1), ["result_id", "auprc"])
    assert "| result_id | auprc |" in text
    assert "cnv" in text

