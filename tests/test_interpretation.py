import pandas as pd

from barrett.evaluation.interpretation import select_final_case_subset, summarize_modality_cases


def toy_cases():
    rows = []
    for category in [
        "A_true_positive_early",
        "B_false_negative",
        "C_false_positive",
        "E_cnv_rescue",
        "F_histology_rescue",
        "G_fusion_hurt",
        "I_modality_disagreement",
    ]:
        rows.append(
            {
                "case_id": category + "_1",
                "case_category": category,
                "patient_id": category,
                "slide_id": "slide",
                "cnv_id": "cnv",
                "analysis_set": "early_prediction_only",
                "case_timing": "pre_event",
                "days_from_current_to_event": 100,
                "true_lgd2_label": 1 if category != "C_false_positive" else 0,
                "cnv_only_prob": 0.7,
                "image_only_prob": 0.2,
                "early_fusion_prob": 0.8 if category != "G_fusion_hurt" else 0.3,
                "reason_selected": "toy",
            }
        )
    rows.append({**rows[0], "case_id": "late_case", "patient_id": "late", "analysis_set": "all_samples"})
    return pd.DataFrame(rows)


def test_selects_required_categories_and_prefers_early():
    selected = select_final_case_subset(toy_cases(), {"A_true_positive_early": 1, "B_false_negative": 1})
    assert set(selected["case_category"]) == {"A_true_positive_early", "B_false_negative"}
    assert selected["analysis_set"].eq("early_prediction_only").all()


def test_modality_summary_identifies_help_and_hurt():
    selected = select_final_case_subset(toy_cases(), {"E_cnv_rescue": 1, "G_fusion_hurt": 1})
    summary = summarize_modality_cases(selected)
    assert summary.loc[summary["category"].eq("E_cnv_rescue"), "fusion_helped"].iloc[0]
    assert summary.loc[summary["category"].eq("G_fusion_hurt"), "fusion_hurt"].iloc[0]
    assert summary["case_interpretation_sentence"].str.len().gt(0).all()

