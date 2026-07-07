#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


THRESHOLD = 0.5
SELECTED_CASE_IDS = ["A_true_positive_early_02", "B_false_negative_07", "E_cnv_rescue_19"]
EXPECTED_HISTOLOGY_FILES = [
    "top_tiles_grid.png",
    "bottom_tiles_grid.png",
    "heatmap_overlay.png",
    "heatmap_overlay_shuffle.png",
    "tile_scores.csv",
    "metadata.json",
]


def prediction(prob: float, threshold: float = THRESHOLD) -> int:
    return int(float(prob) >= threshold)


def is_correct(prob: float, true_label: int, threshold: float = THRESHOLD) -> bool:
    return prediction(prob, threshold) == int(true_label)


def fusion_help_hurt_label(cnv_correct: bool, image_correct: bool, fusion_correct: bool, probs: dict[str, float]) -> str:
    near = all(abs(float(probs[k]) - THRESHOLD) <= 0.1 for k in ["cnv", "image", "fusion"])
    if cnv_correct and image_correct and fusion_correct:
        return "all_correct_low_margin" if near else "fusion_confirms_both"
    if (not cnv_correct) and image_correct and fusion_correct:
        return "fusion_rescues_cnv"
    if cnv_correct and (not image_correct) and fusion_correct:
        return "fusion_rescues_image"
    if (cnv_correct or image_correct) and not fusion_correct:
        return "fusion_hurts"
    if not cnv_correct and not image_correct and not fusion_correct:
        return "all_fail"
    return "ambiguous"


def fold_from_ref(ref: str) -> str:
    match = re.search(r"__fold(\d+)(?:/|$)", str(ref))
    return f"fold{match.group(1)}" if match else ""


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def choose_cases(case_df: pd.DataFrame, hist_df: pd.DataFrame) -> list[str]:
    available = set(hist_df.loc[hist_df["interpretation_readiness_status"].eq("READY_FOR_MANUAL_REVIEW"), "case_id"])
    chosen = [cid for cid in SELECTED_CASE_IDS if cid in available and cid in set(case_df["case_id"])]
    if len(chosen) < 3:
        raise RuntimeError(f"Expected 3 selected cases, found {chosen}")
    return chosen


def build_selection(case_df: pd.DataFrame, hist_df: pd.DataFrame, cnv_df: pd.DataFrame, selected_ids: list[str]) -> pd.DataFrame:
    rows = []
    hist_by_case = hist_df.set_index("case_id")
    cnv_by_case = cnv_df.set_index("case_id") if "case_id" in cnv_df.columns else {}
    priority = {cid: idx + 1 for idx, cid in enumerate(selected_ids)}
    reasons = {
        "A_true_positive_early_02": "Strong early true-positive with complete histology outputs and high image/fusion probabilities.",
        "B_false_negative_07": "Required missed-progressor case; CNV is positive but image and fusion are below threshold.",
        "E_cnv_rescue_19": "Rescue case: CNV and fusion are positive while image-only is below threshold.",
    }
    for cid in selected_ids:
        case = case_df.loc[case_df["case_id"].eq(cid)].iloc[0]
        hist = hist_by_case.loc[cid]
        cnv = cnv_by_case.loc[cid] if cid in cnv_by_case.index else pd.Series(dtype=object)
        rows.append(
            {
                "case_id": cid,
                "case_category": case["category"],
                "patient_id": case["patient_id"],
                "sample_id": case["sample_id"],
                "slide_id": case["slide_id"],
                "slide_basename": case["slide_id"],
                "true_label": int(case["true_label"]),
                "cnv_probability": float(case["CNV_probability"]),
                "image_probability": float(case["image_probability"]),
                "fusion_probability": float(case["early_fusion_probability"]),
                "cnv_correct": str(case["prediction_correctness_cnv"]).lower() == "correct",
                "image_correct": str(case["prediction_correctness_image"]).lower() == "correct",
                "fusion_correct": str(case["prediction_correctness_early_fusion"]).lower() == "correct",
                "selected_for_case_pack": True,
                "selection_priority": priority[cid],
                "reason_selected": reasons.get(cid, case.get("reason_selected", "")),
                "histology_output_ref": hist["output_directory_external_ref"],
                "cnv_output_ref": cnv.get("external_cnv_output_ref", "MISSING"),
                "warnings": "" if pd.isna(cnv.get("warnings", "")) else cnv.get("warnings", ""),
            }
        )
    return pd.DataFrame(rows)


def build_fusion(selection: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in selection.iterrows():
        true_label = int(row["true_label"])
        probs = {
            "cnv": float(row["cnv_probability"]),
            "image": float(row["image_probability"]),
            "fusion": float(row["fusion_probability"]),
        }
        cnv_pred = prediction(probs["cnv"])
        image_pred = prediction(probs["image"])
        fusion_pred = prediction(probs["fusion"])
        cnv_correct = cnv_pred == true_label
        image_correct = image_pred == true_label
        fusion_correct = fusion_pred == true_label
        label = fusion_help_hurt_label(cnv_correct, image_correct, fusion_correct, probs)
        sentence = fusion_sentence(row, cnv_pred, image_pred, fusion_pred, label)
        rows.append(
            {
                "case_id": row["case_id"],
                "case_category": row["case_category"],
                "patient_id": row["patient_id"],
                "true_label": true_label,
                "cnv_probability": probs["cnv"],
                "image_probability": probs["image"],
                "fusion_probability": probs["fusion"],
                "cnv_prediction": cnv_pred,
                "image_prediction": image_pred,
                "fusion_prediction": fusion_pred,
                "cnv_correct": cnv_correct,
                "image_correct": image_correct,
                "fusion_correct": fusion_correct,
                "fusion_delta_vs_cnv": probs["fusion"] - probs["cnv"],
                "fusion_delta_vs_image": probs["fusion"] - probs["image"],
                "fusion_help_hurt_label": label,
                "interpretation_sentence": sentence,
                "warnings": "",
            }
        )
    return pd.DataFrame(rows)


def fusion_sentence(row: pd.Series, cnv_pred: int, image_pred: int, fusion_pred: int, label: str) -> str:
    return (
        f"{row['case_id']} is a {row['case_category']} case with true label {int(row['true_label'])}. "
        f"CNV/image/fusion predictions are {cnv_pred}/{image_pred}/{fusion_pred}; "
        f"fusion label: {label}."
    )


def build_histology_inventory(selection: pd.DataFrame, audit_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in selection.iterrows():
        case_audit = audit_df[audit_df["case_id"].eq(row["case_id"])]
        file_status = {}
        warnings = []
        for name in EXPECTED_HISTOLOGY_FILES:
            found = case_audit[case_audit["output_file"].eq(name)]
            ok = bool(len(found) and found.iloc[0]["exists"] and found.iloc[0]["status"] == "PASS")
            file_status[name] = ok
            if not ok:
                warnings.append(f"{name} missing_or_failed")
        rows.append(
            {
                "case_id": row["case_id"],
                "top_tiles_grid": file_status["top_tiles_grid.png"],
                "bottom_tiles_grid": file_status["bottom_tiles_grid.png"],
                "heatmap_overlay": file_status["heatmap_overlay.png"],
                "heatmap_overlay_shuffle": file_status["heatmap_overlay_shuffle.png"],
                "tile_scores": file_status["tile_scores.csv"],
                "metadata_json": file_status["metadata.json"],
                "histology_panel_ready": all(file_status.values()),
                "external_output_ref": row["histology_output_ref"],
                "warnings": "; ".join(warnings),
            }
        )
    return pd.DataFrame(rows)


def build_cnv_status(selection: pd.DataFrame, case_df: pd.DataFrame) -> pd.DataFrame:
    case_by_id = case_df.set_index("case_id")
    rows = []
    for _, row in selection.iterrows():
        case = case_by_id.loc[row["case_id"]]
        blocker = (
            "LGD2+ selected-case CNV feature matrix/model/importances/window-to-gene map not validated; "
            "existing CNV summaries are missing or legacy only."
        )
        rows.append(
            {
                "case_id": row["case_id"],
                "cnv_profile_ref": case["cnv_id"],
                "cnv_model_ref": "lgd2_cnv_core/cnv_random_forest (prediction probability available; estimator path not validated)",
                "fold": fold_from_ref(row["histology_output_ref"]),
                "feature_importance_ref": "MISSING",
                "window_gene_map_ref": "MISSING",
                "can_generate_cnv_summary_now": False,
                "blocker": blocker,
                "recommended_next_command": "Validate LGD2+ CNV feature matrix, saved estimator/worklist, and gene map before running cnv_feature_importance.py.",
                "warnings": "Do not use LGD3+/legacy CNV top-window outputs as primary LGD2+ evidence.",
            }
        )
    return pd.DataFrame(rows)


def blocked_cnv_top_windows(selection: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in selection.iterrows():
        rows.append(
            {
                "case_id": row["case_id"],
                "rank": "",
                "chromosome": "BLOCKED",
                "start": "",
                "end": "",
                "importance_or_score": "",
                "copy_number_value_if_available": "",
                "overlapping_genes": "MISSING",
                "interpretation_note": "CNV top-window summary not generated; required LGD2+ CNV interpretation inputs are not validated.",
                "source_ref": row["cnv_output_ref"],
                "warnings": row["warnings"] or "Missing external CNV interpretation outputs.",
            }
        )
    return pd.DataFrame(rows)


def write_markdown_tables(report_dir: Path, selection: pd.DataFrame, fusion: pd.DataFrame, hist: pd.DataFrame, cnv: pd.DataFrame, top: pd.DataFrame) -> None:
    write_selection_md(report_dir / "lgd2_multimodal_case_pack_selection.md", selection)
    write_fusion_md(report_dir / "lgd2_fusion_case_interpretation.md", fusion)
    write_storyboard_md(report_dir / "lgd2_case_storyboard_first3.md", selection, fusion, hist, cnv)
    write_histology_md(report_dir / "lgd2_case_pack_histology_panel_inventory.md", hist)
    write_cnv_status_md(report_dir / "lgd2_case_pack_cnv_input_status.md", cnv)
    write_cnv_top_md(report_dir / "lgd2_case_pack_cnv_top_windows.md", top)
    write_figure_plan_md(report_dir / "lgd2_multimodal_case_figure_plan_first3.md", selection, fusion, hist, cnv)


def write_selection_md(path: Path, df: pd.DataFrame) -> None:
    lines = ["# LGD2+ Multimodal Case-Pack Selection", ""]
    lines.append("Selected first case-study packs: one strong true-positive early case, the required false-negative case, and one rescue case.")
    lines.append("")
    lines.append("| priority | case_id | category | patient_id | reason |")
    lines.append("| ---: | --- | --- | --- | --- |")
    for _, r in df.iterrows():
        lines.append(f"| {int(r.selection_priority)} | `{r.case_id}` | `{r.case_category}` | `{r.patient_id}` | {r.reason_selected} |")
    lines.append("")
    lines.append("Histology outputs are complete for all selected cases. CNV output refs are planned/missing unless the CNV status report says otherwise.")
    path.write_text("\n".join(lines) + "\n")


def write_fusion_md(path: Path, df: pd.DataFrame) -> None:
    lines = ["# LGD2+ Fusion Case Interpretation", ""]
    lines.append("| case_id | true | cnv | image | fusion | label | sentence |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
    for _, r in df.iterrows():
        lines.append(
            f"| `{r.case_id}` | `{int(r.true_label)}` | `{r.cnv_probability:.3f}` | `{r.image_probability:.3f}` | "
            f"`{r.fusion_probability:.3f}` | `{r.fusion_help_hurt_label}` | {r.interpretation_sentence} |"
        )
    lines.append("")
    lines.append("Threshold: 0.5. Labels are probability-level summaries and should be interpreted with the histology/CNV panels.")
    path.write_text("\n".join(lines) + "\n")


def write_storyboard_md(path: Path, selection: pd.DataFrame, fusion: pd.DataFrame, hist: pd.DataFrame, cnv: pd.DataFrame) -> None:
    fusion_by_id = fusion.set_index("case_id")
    hist_by_id = hist.set_index("case_id")
    cnv_by_id = cnv.set_index("case_id")
    lines = ["# LGD2+ Case Storyboard - First 3", ""]
    for _, r in selection.iterrows():
        f = fusion_by_id.loc[r.case_id]
        h = hist_by_id.loc[r.case_id]
        c = cnv_by_id.loc[r.case_id]
        lines.append(f"## {r.case_id}")
        lines.append("")
        lines.append(
            f"{r.case_id} is a `{r.case_category}` case with true LGD2+ label `{int(r.true_label)}`. "
            f"CNV-only probability is `{r.cnv_probability:.3f}`, histology-only ABMIL probability is `{r.image_probability:.3f}`, "
            f"and early-fusion probability is `{r.fusion_probability:.3f}`. The probability-level fusion summary is `{f.fusion_help_hurt_label}`. "
            f"Histology outputs are available externally and include top/bottom tile grids, heatmap overlay, shuffled overlay, tile scores, and metadata. "
            f"CNV interpretation remains pending: {c.blocker} "
            f"This case can support a figure panel with timeline/outcome, histology attention outputs, modality probability bar, and a placeholder CNV panel until validated CNV windows/genes are generated."
        )
        lines.append("")
        lines.append(f"Histology external output: `{h.external_output_ref}`")
        lines.append("")
    path.write_text("\n".join(lines))


def write_histology_md(path: Path, df: pd.DataFrame) -> None:
    lines = ["# LGD2+ Case-Pack Histology Panel Inventory", ""]
    lines.append("All selected first case-pack cases have complete ABMIL histology panel outputs available externally.")
    lines.append("")
    lines.append("| case_id | top grid | bottom grid | heatmap | shuffled heatmap | tile scores | metadata | ready |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for _, r in df.iterrows():
        lines.append(f"| `{r.case_id}` | `{r.top_tiles_grid}` | `{r.bottom_tiles_grid}` | `{r.heatmap_overlay}` | `{r.heatmap_overlay_shuffle}` | `{r.tile_scores}` | `{r.metadata_json}` | `{r.histology_panel_ready}` |")
    lines.append("")
    lines.append("Images and tile-score dumps remain external; this file records availability only.")
    path.write_text("\n".join(lines) + "\n")


def write_cnv_status_md(path: Path, df: pd.DataFrame) -> None:
    lines = ["# LGD2+ Case-Pack CNV Input Status", ""]
    lines.append("CNV interpretation is not ready for the first case-pack cases because LGD2+ feature importance and gene-map inputs have not been validated.")
    lines.append("")
    lines.append("| case_id | cnv_profile_ref | fold | can_generate_now | blocker |")
    lines.append("| --- | --- | --- | --- | --- |")
    for _, r in df.iterrows():
        lines.append(f"| `{r.case_id}` | `{r.cnv_profile_ref}` | `{r.fold}` | `{r.can_generate_cnv_summary_now}` | {r.blocker} |")
    lines.append("")
    lines.append("Exact next step: validate LGD2+ CNV feature matrix, saved estimator/worklist, and window-to-gene map, then run the CNV command templates in `lgd2_cnv_interpretation_commands.md` into the external analysis root.")
    path.write_text("\n".join(lines) + "\n")


def write_cnv_top_md(path: Path, df: pd.DataFrame) -> None:
    lines = ["# LGD2+ Case-Pack CNV Top Windows", ""]
    lines.append("No LGD2+ CNV top-window summaries were generated. Rows below are explicit blocked placeholders, not biological results.")
    lines.append("")
    lines.append("| case_id | status | note |")
    lines.append("| --- | --- | --- |")
    for _, r in df.iterrows():
        lines.append(f"| `{r.case_id}` | `BLOCKED` | {r.interpretation_note} |")
    path.write_text("\n".join(lines) + "\n")


def write_figure_plan_md(path: Path, selection: pd.DataFrame, fusion: pd.DataFrame, hist: pd.DataFrame, cnv: pd.DataFrame) -> None:
    fusion_by_id = fusion.set_index("case_id")
    cnv_by_id = cnv.set_index("case_id")
    lines = ["# LGD2+ Multimodal Case Figure Plan - First 3", ""]
    for _, r in selection.iterrows():
        f = fusion_by_id.loc[r.case_id]
        c = cnv_by_id.loc[r.case_id]
        lines.append(f"## Case: {r.case_id}")
        lines.append("")
        lines.append("- A. Timeline / outcome label: ready now from selected-case metadata.")
        lines.append("- B. CNV probability and top CNV windows: probability ready; top windows/genes need CNV regeneration.")
        lines.append("- C. Histology top-tile grid: available externally.")
        lines.append("- D. Histology heatmap overlay: available externally.")
        lines.append(f"- E. CNV vs histology vs fusion probability bar: ready now; fusion summary `{f.fusion_help_hurt_label}`.")
        lines.append("- F. One-sentence interpretation: draft-ready with cautious language; biological interpretation waits for manual review and CNV windows/genes.")
        lines.append(f"- CNV blocker: {c.blocker}")
        lines.append("")
    path.write_text("\n".join(lines))


def update_interpretation_summary(path: Path, selected_ids: list[str]) -> None:
    text = path.read_text()
    section = (
        "\n## First multimodal case-study packs\n\n"
        "The first lightweight LGD2+ multimodal case-study packs have been assembled for:\n\n"
        + "\n".join(f"- `{cid}`" for cid in selected_ids)
        + "\n\nFusion probability interpretation is complete for these cases using existing CNV-only, ABMIL image-only, and early-fusion probabilities. "
        "Histology panels are available externally for all selected cases and include top/bottom tile grids, heatmap overlays, shuffled overlays, tile-score tables, and metadata JSON.\n\n"
        "CNV region/gene interpretation was not generated in this stage. The selected cases have CNV probabilities and CNV IDs, but LGD2+ feature-importance, feature-matrix/model, and window-to-gene-map inputs remain unvalidated. "
        "The case packs are therefore ready for thesis drafting at the probability-plus-histology level, with CNV panels marked as pending.\n\n"
        "New lightweight files:\n\n"
        "- `lgd2_multimodal_case_pack_selection.csv` / `.md`\n"
        "- `lgd2_fusion_case_interpretation.csv` / `.md`\n"
        "- `lgd2_case_storyboard_first3.md`\n"
        "- `lgd2_case_pack_histology_panel_inventory.csv` / `.md`\n"
        "- `lgd2_case_pack_cnv_input_status.csv` / `.md`\n"
        "- `lgd2_case_pack_cnv_top_windows.csv` / `.md`\n"
        "- `lgd2_multimodal_case_figure_plan_first3.md`\n"
    )
    marker = "\n## Which model to interpret first\n"
    if "## First multimodal case-study packs" in text:
        text = re.sub(r"\n## First multimodal case-study packs\n.*?(?=\n## Which model to interpret first\n)", section + "\n", text, flags=re.S)
    else:
        text = text.replace(marker, section + marker)
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build lightweight LGD2+ multimodal case-study packs.")
    parser.add_argument("--report-dir", default="reports/thesis_ch1")
    args = parser.parse_args()

    report_dir = Path(args.report_dir)
    case_df = read_csv(report_dir / "lgd2_final_interpretation_case_subset.csv")
    hist_df = read_csv(report_dir / "lgd2_histology_all8_interpretation_summary.csv")
    hist_audit = read_csv(report_dir / "lgd2_histology_all8_output_audit.csv")
    cnv_df = read_csv(report_dir / "lgd2_cnv_interpretation_summary.csv")

    selected_ids = choose_cases(case_df, hist_df)
    selection = build_selection(case_df, hist_df, cnv_df, selected_ids)
    fusion = build_fusion(selection)
    hist = build_histology_inventory(selection, hist_audit)
    cnv = build_cnv_status(selection, case_df)
    top = blocked_cnv_top_windows(selection)

    outputs = {
        "lgd2_multimodal_case_pack_selection.csv": selection,
        "lgd2_fusion_case_interpretation.csv": fusion,
        "lgd2_case_pack_histology_panel_inventory.csv": hist,
        "lgd2_case_pack_cnv_input_status.csv": cnv,
        "lgd2_case_pack_cnv_top_windows.csv": top,
    }
    for name, df in outputs.items():
        df.to_csv(report_dir / name, index=False)
    write_markdown_tables(report_dir, selection, fusion, hist, cnv, top)
    update_interpretation_summary(report_dir / "lgd2_interpretation_summary.md", selected_ids)
    print(f"Wrote LGD2+ multimodal case packs for {len(selected_ids)} cases to {report_dir}")


if __name__ == "__main__":
    main()
