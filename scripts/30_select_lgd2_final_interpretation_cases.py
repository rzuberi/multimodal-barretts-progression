#!/usr/bin/env python
"""Reselect lightweight interpretation cases from final strict pre-event OOF predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


FAMILIES = (
    "cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion", "late_mean",
)
TARGETS = (
    ("A_true_positive_early", 2),
    ("B_false_negative", 1),
    ("C_false_positive", 1),
    ("E_cnv_rescue", 1),
    ("F_histology_rescue", 1),
    ("G_fusion_hurt", 1),
    ("I_modality_disagreement", 1),
)


def _thresholds(output: Path, family: str) -> dict[int, float]:
    values = {}
    for fold in range(1, 6):
        metadata = json.loads(
            (output / family / f"fold{fold}/fold_metadata.json").read_text(encoding="utf-8")
        )
        values[fold] = float(metadata["validation_threshold"]["threshold"])
    return values


def _merge_predictions(output: Path) -> pd.DataFrame:
    merged = None
    identity = ["row_key", "patient_id", "outer_fold", "y_true"]
    for family in FAMILIES:
        frame = pd.read_csv(
            output / f"oof/{family}_oof_predictions.csv",
            dtype={"row_key": str, "sample_id": str},
        )
        part = frame[identity + ["y_prob", "checkpoint_ref"]].rename(columns={
            "y_prob": f"{family}_probability", "checkpoint_ref": f"{family}_checkpoint_ref",
        })
        merged = part if merged is None else merged.merge(
            part, on=identity, how="outer", validate="one_to_one", indicator=True
        )
        if "_merge" in merged:
            if set(merged["_merge"]) != {"both"}:
                raise ValueError(f"{family} row set differs during case merge")
            merged = merged.drop(columns="_merge")
    return merged


def _category(frame: pd.DataFrame, name: str) -> pd.Series:
    y = frame["y_true"].astype(int)
    c, i, e, l = (frame[f"{family}_prediction"] for family in ("cnv_only", "image_only", "early_fusion", "late_mean"))
    if name == "A_true_positive_early":
        return (y == 1) & (e == 1) & (l == 1)
    if name == "B_false_negative":
        return (y == 1) & (l == 0)
    if name == "C_false_positive":
        return (y == 0) & (l == 1)
    if name == "E_cnv_rescue":
        return (y == 1) & (c == 1) & (i == 0) & (l == 1)
    if name == "F_histology_rescue":
        return (y == 1) & (c == 0) & (i == 1) & (l == 1)
    if name == "G_fusion_hurt":
        return ((c == y) | (i == y)) & (l != y)
    if name == "I_modality_disagreement":
        return c != i
    raise ValueError(name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--reports-dir", default="reports/thesis_ch1")
    args = parser.parse_args()
    release = Path(args.release_root).resolve()
    output = Path(args.output_root).resolve()
    reports = Path(args.reports_dir)
    frame = _merge_predictions(output)
    manifest = pd.read_csv(release / "training_manifest_v2.csv", dtype={"sample_id": str})
    metadata = manifest.rename(columns={"sample_id": "row_key"})[[
        "row_key", "biopsy_id", "slide_id", "slide_ref", "cnv_id", "DaysToNextBiopsy",
    ]]
    frame = frame.merge(metadata, on="row_key", how="left", validate="one_to_one")
    for family in FAMILIES:
        mapping = _thresholds(output, family)
        frame[f"{family}_threshold"] = frame["outer_fold"].map(mapping)
        frame[f"{family}_prediction"] = (
            frame[f"{family}_probability"] >= frame[f"{family}_threshold"]
        ).astype(int)
        frame[f"{family}_correct"] = frame[f"{family}_prediction"].eq(frame["y_true"])
    frame["selection_margin"] = (
        frame["late_mean_probability"] - frame["late_mean_threshold"]
    ).abs()

    chosen, used_patients, warnings = [], set(), []
    for category, count in TARGETS:
        candidates = frame[_category(frame, category)].copy()
        candidates = candidates[~candidates["patient_id"].isin(used_patients)]
        candidates = candidates.sort_values(
            ["selection_margin", "DaysToNextBiopsy"], ascending=[False, False]
        )
        take = candidates.head(count)
        if len(take) < count:
            warnings.append(f"{category}: requested {count}, found {len(take)} unique-patient cases")
        for index, row in enumerate(take.itertuples(index=False), start=1):
            record = row._asdict()
            record["case_category"] = category
            record["case_id"] = f"FINAL_{category}_{index:02d}"
            record["selection_reason"] = (
                "Final strict pre-event OOF category using fold-specific inner-validation thresholds; "
                "high margin and later next-biopsy interval prioritised."
            )
            chosen.append(record)
            used_patients.add(str(record["patient_id"]))
    selected = pd.DataFrame(chosen)
    ordered = [
        "case_id", "case_category", "patient_id", "row_key", "biopsy_id", "slide_id", "slide_ref", "cnv_id",
        "outer_fold", "DaysToNextBiopsy", "y_true",
    ]
    for family in FAMILIES:
        ordered.extend([
            f"{family}_probability", f"{family}_threshold", f"{family}_prediction",
            f"{family}_correct", f"{family}_checkpoint_ref",
        ])
    ordered.extend(["selection_margin", "selection_reason"])
    selected = selected[[column for column in ordered if column in selected.columns]]
    reports.mkdir(parents=True, exist_ok=True)
    selected.to_csv(reports / "lgd2_final_pre_event_interpretation_cases.csv", index=False)
    lines = [
        "# LGD2+ Final Pre-event Interpretation Cases", "",
        f"Selected {len(selected)} cases from final strict pre-event OOF predictions.", "",
        "These replace developmental TP/FN/rescue labels for future final-model interpretation. Heavy attention/CNV outputs remain external and must be regenerated from the recorded fold checkpoints.", "",
        "| Case | Category | Patient | Fold | Label | CNV | Image | Early | Late mean |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected.itertuples(index=False):
        lines.append(
            f"| {row.case_id} | {row.case_category} | {row.patient_id} | {row.outer_fold} | {row.y_true} | "
            f"{row.cnv_only_probability:.3f} | {row.image_only_probability:.3f} | "
            f"{row.early_fusion_probability:.3f} | {row.late_mean_probability:.3f} |"
        )
    (reports / "lgd2_final_pre_event_interpretation_cases.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    warning_text = "# LGD2+ Final Pre-event Interpretation Case Warnings\n\n"
    warning_text += "\n".join(f"- {value}" for value in warnings) if warnings else "None."
    (reports / "lgd2_final_pre_event_interpretation_case_warnings.md").write_text(
        warning_text + "\n", encoding="utf-8"
    )
    print(f"selected {len(selected)} final interpretation cases; warnings={len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
