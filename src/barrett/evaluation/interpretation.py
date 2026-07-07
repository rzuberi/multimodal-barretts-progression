"""Helpers for lightweight LGD2+ interpretation case summaries."""

from __future__ import annotations

import pandas as pd

DEFAULT_CATEGORY_COUNTS = {
    "A_true_positive_early": 2,
    "B_false_negative": 1,
    "C_false_positive": 1,
    "E_cnv_rescue": 1,
    "F_histology_rescue": 1,
    "G_fusion_hurt": 1,
    "I_modality_disagreement": 1,
}


def modality_correct(prob: float, true_label: int, threshold: float = 0.5) -> bool:
    return int(prob >= threshold) == int(true_label)


def case_priority(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    required = ["cnv_only_prob", "image_only_prob", "early_fusion_prob"]
    out["all_probs_available"] = out[required].notna().all(axis=1)
    out["has_slide_cnv_ids"] = out[["slide_id", "cnv_id"]].notna().all(axis=1)
    out["is_early_prediction"] = out["analysis_set"].eq("early_prediction_only")
    out["is_pre_event"] = out["case_timing"].eq("pre_event")
    out["not_at_event"] = out["days_from_current_to_event"].ne(0)
    out["confidence"] = (
        (out["cnv_only_prob"] - 0.5).abs()
        + (out["image_only_prob"] - 0.5).abs()
        + (out["early_fusion_prob"] - 0.5).abs()
    )
    return out


def select_final_case_subset(
    cases: pd.DataFrame,
    category_counts: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Select a small, category-balanced thesis-figure subset."""
    counts = category_counts or DEFAULT_CATEGORY_COUNTS
    scored = case_priority(cases)
    selected = []
    used_patients: set[str] = set()
    for category, n_cases in counts.items():
        subset = scored[scored["case_category"].eq(category)].copy()
        subset = subset.sort_values(
            ["is_early_prediction", "not_at_event", "is_pre_event", "all_probs_available", "has_slide_cnv_ids", "confidence"],
            ascending=[False, False, False, False, False, False],
        )
        picked = []
        for _, row in subset.iterrows():
            if len(picked) >= n_cases:
                break
            patient = str(row.get("patient_id", ""))
            if patient in used_patients and len(subset) > n_cases:
                continue
            picked.append(row)
            used_patients.add(patient)
        if len(picked) < n_cases:
            picked_ids = {p["case_id"] for p in picked}
            for _, row in subset.iterrows():
                if len(picked) >= n_cases:
                    break
                if row["case_id"] not in picked_ids:
                    picked.append(row)
        selected.extend(picked)
    out = pd.DataFrame(selected).copy()
    if out.empty:
        return out
    out["category"] = out["case_category"]
    out["cnv_correct"] = out.apply(lambda r: modality_correct(r["cnv_only_prob"], r["true_lgd2_label"]), axis=1)
    out["image_correct"] = out.apply(lambda r: modality_correct(r["image_only_prob"], r["true_lgd2_label"]), axis=1)
    out["early_fusion_correct"] = out.apply(lambda r: modality_correct(r["early_fusion_prob"], r["true_lgd2_label"]), axis=1)
    out["reason_selected"] = out["reason_selected"].astype(str) + "; final thesis-figure subset"
    return out


def dominant_modality_hint(row: pd.Series) -> str:
    cnv = float(row["cnv_prob"])
    image = float(row["image_prob"])
    fusion = float(row["fusion_prob"])
    if abs(cnv - image) < 0.10:
        return "modalities_similar"
    closer_to_cnv = abs(fusion - cnv) < abs(fusion - image)
    return "fusion_closer_to_cnv" if closer_to_cnv else "fusion_closer_to_image"


def summarize_modality_cases(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in cases.iterrows():
        true_label = int(row["true_lgd2_label"] if "true_lgd2_label" in row else row["true_label"])
        cnv = float(row["cnv_only_prob"] if "cnv_only_prob" in row else row["CNV_probability"])
        image = float(row["image_only_prob"] if "image_only_prob" in row else row["image_probability"])
        fusion = float(row["early_fusion_prob"] if "early_fusion_prob" in row else row["early_fusion_probability"])
        cnv_correct = modality_correct(cnv, true_label)
        image_correct = modality_correct(image, true_label)
        fusion_correct = modality_correct(fusion, true_label)
        fusion_helped = bool(fusion_correct and not (cnv_correct and image_correct))
        fusion_hurt = bool((cnv_correct or image_correct) and not fusion_correct)
        all_agree = int(cnv >= 0.5) == int(image >= 0.5) == int(fusion >= 0.5)
        summary = {
            "case_id": row["case_id"],
            "category": row.get("category", row.get("case_category")),
            "patient_id": row["patient_id"],
            "cnv_prob": cnv,
            "image_prob": image,
            "fusion_prob": fusion,
            "fusion_minus_cnv": fusion - cnv,
            "fusion_minus_image": fusion - image,
            "abs_cnv_image_disagreement": abs(cnv - image),
            "dominant_modality_hint": "",
            "fusion_helped": fusion_helped,
            "fusion_hurt": fusion_hurt,
            "all_modalities_agree": bool(all_agree),
            "case_interpretation_sentence": "",
        }
        summary["dominant_modality_hint"] = dominant_modality_hint(pd.Series(summary))
        if fusion_helped:
            sentence = "Fusion is correct where at least one unimodal model is wrong."
        elif fusion_hurt:
            sentence = "Fusion is wrong despite at least one correct unimodal model."
        elif all_agree:
            sentence = "All modalities agree on the risk class."
        else:
            sentence = "CNV and histology disagree; fusion arbitrates between them."
        summary["case_interpretation_sentence"] = sentence
        rows.append(summary)
    return pd.DataFrame(rows)
