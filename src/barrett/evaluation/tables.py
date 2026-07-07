"""Model table selection and Markdown helpers."""

from __future__ import annotations

import pandas as pd

RANK_COLUMNS = [
    "auprc",
    "roc_auc",
    "sensitivity",
    "progressors_detected",
    "false_positives_per_detected_progressor",
]


def rank_models(df: pd.DataFrame) -> pd.DataFrame:
    """Rank models by AUPRC, AUC, sensitivity, then lower false-positive burden."""
    ranked = df.copy()
    for col in RANK_COLUMNS:
        if col not in ranked.columns:
            ranked[col] = pd.NA
    ranked = ranked.sort_values(
        ["auprc", "roc_auc", "sensitivity", "progressors_detected", "false_positives_per_detected_progressor"],
        ascending=[False, False, False, False, True],
        na_position="last",
    )
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked


def best_row(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = rank_models(df).head(1).copy()
    out.insert(0, "comparison_slot", label)
    return out


def select_representative_models(metrics: pd.DataFrame) -> pd.DataFrame:
    """Select thesis-facing representative rows from patient_max metrics."""
    patient = metrics[metrics["aggregation"].eq("patient_max")].copy()
    selected = []
    selected.append(best_row(patient[patient["model_family"].eq("CNV-only")], "cnv_only"))
    selected.append(best_row(patient[patient["model_family"].eq("histology-only")], "best_image_only"))
    selected.append(best_row(patient[patient["fusion_type"].eq("early_fusion")], "best_early_fusion"))
    selected.append(best_row(patient[patient["fusion_type"].eq("intermediate_fusion")], "best_intermediate_fusion"))
    selected.append(best_row(patient[patient["fusion_type"].eq("coattention")], "best_coattention"))
    selected.append(best_row(patient[patient["model_family"].eq("multimodal")], "best_multimodal_overall"))
    out = pd.concat([x for x in selected if not x.empty], ignore_index=True)
    if out.empty:
        return out
    return rank_models(out.drop(columns=["rank"], errors="ignore"))


def format_value(value: object, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value)
    try:
        number = float(value)
    except Exception:
        return str(value)
    if number.is_integer() and abs(number) >= 1:
        return str(int(number))
    return f"{number:.{digits}f}"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    """Render a compact Markdown table."""
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)

