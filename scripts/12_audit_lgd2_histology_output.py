#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd
from PIL import Image

EXPECTED_FILES = [
    "top_tiles_grid.png",
    "bottom_tiles_grid.png",
    "heatmap_overlay.png",
    "heatmap_overlay_shuffle.png",
    "tile_scores.csv",
    "metadata.json",
]


def _safe_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def audit_output_dir(case_id: str, output_dir: Path) -> tuple[pd.DataFrame, dict[str, object], pd.DataFrame]:
    rows = []
    details: dict[str, object] = {
        "case_id": case_id,
        "output_dir": str(output_dir),
        "metadata_valid": False,
        "tile_scores_valid": False,
        "n_tiles_scored": 0,
        "top_score_min": "",
        "top_score_max": "",
        "scores_nonconstant": False,
        "images_openable": False,
        "structurally_valid": False,
        "warnings": [],
    }
    tile_df = pd.DataFrame()

    for name in EXPECTED_FILES:
        path = output_dir / name
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        parse_status = "not_parsed"
        key_fields = ""
        status = "PASS" if exists and size > 0 else "FAIL"
        warning = "" if status == "PASS" else "missing_or_empty"
        if exists and size > 0 and name == "metadata.json":
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
                parse_status = "parsed"
                key_fields = "; ".join(
                    f"{k}={meta.get(k, '')}"
                    for k in ["sample_id", "patient_id", "model", "model_prob_explain", "n_tiles_used", "attribution_method"]
                    if k in meta
                )
                details["metadata_valid"] = True
            except Exception as exc:
                parse_status = f"parse_error:{type(exc).__name__}"
                status = "FAIL"
                warning = str(exc)[:200]
        elif exists and size > 0 and name == "tile_scores.csv":
            try:
                tile_df = pd.read_csv(path)
                parse_status = "parsed"
                key_fields = ",".join(tile_df.columns.astype(str).tolist())
                score_col = _score_column(tile_df)
                details["n_tiles_scored"] = int(len(tile_df))
                if score_col:
                    scores = _safe_float_series(tile_df[score_col]).dropna()
                    if len(scores):
                        top = scores.sort_values(ascending=False).head(5)
                        details["top_score_min"] = float(top.min())
                        details["top_score_max"] = float(top.max())
                        details["scores_nonconstant"] = bool(scores.nunique() > 1)
                details["tile_scores_valid"] = bool(len(tile_df) > 0 and score_col)
                if not details["tile_scores_valid"]:
                    status = "FAIL"
                    warning = "missing score column or empty tile table"
            except Exception as exc:
                parse_status = f"parse_error:{type(exc).__name__}"
                status = "FAIL"
                warning = str(exc)[:200]
        elif exists and size > 0 and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            try:
                with Image.open(path) as img:
                    img.verify()
                with Image.open(path) as img:
                    key_fields = f"dimensions={img.size[0]}x{img.size[1]}"
                parse_status = "image_opened"
            except Exception as exc:
                parse_status = f"image_error:{type(exc).__name__}"
                status = "FAIL"
                warning = str(exc)[:200]
        rows.append(
            {
                "case_id": case_id,
                "output_file": name,
                "exists": exists,
                "size_bytes": size,
                "parse_status": parse_status,
                "key_fields": key_fields,
                "status": status,
                "warning": warning,
            }
        )

    audit = pd.DataFrame(rows)
    image_rows = audit[audit["output_file"].str.endswith(".png")]
    details["images_openable"] = bool((image_rows["status"] == "PASS").all() and not image_rows.empty)
    details["structurally_valid"] = bool(
        (audit["status"] == "PASS").all()
        and details["metadata_valid"]
        and details["tile_scores_valid"]
        and details["scores_nonconstant"]
        and details["images_openable"]
    )
    if not details["scores_nonconstant"]:
        details["warnings"].append("tile scores are constant or unavailable")
    if not details["structurally_valid"]:
        details["warnings"].append("one or more required outputs failed validation")
    return audit, details, tile_df


def _score_column(df: pd.DataFrame) -> str:
    for col in ["score_raw", "score_norm", "score", "attention", "attention_score", "tile_score"]:
        if col in df.columns:
            return col
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    return numeric[-1] if numeric else ""


def interpretation_summary(case_row: pd.Series, details: dict[str, object], tile_df: pd.DataFrame) -> pd.DataFrame:
    score_col = _score_column(tile_df) if not tile_df.empty else ""
    coord_cols = [c for c in ["x", "y", "coord_x", "coord_y", "tile_x", "tile_y"] if c in tile_df.columns]
    top_refs = []
    bottom_refs = []
    top_scores = []
    bottom_scores = []
    if score_col:
        tmp = tile_df.copy()
        tmp[score_col] = _safe_float_series(tmp[score_col])
        tmp = tmp.dropna(subset=[score_col])
        top = tmp.sort_values(score_col, ascending=False).head(5)
        bottom = tmp.sort_values(score_col, ascending=True).head(5)
        top_scores = [str(float(x)) for x in top[score_col].tolist()]
        bottom_scores = [str(float(x)) for x in bottom[score_col].tolist()]
        top_refs = [_tile_ref(r, coord_cols) for _, r in top.iterrows()]
        bottom_refs = [_tile_ref(r, coord_cols) for _, r in bottom.iterrows()]
    return pd.DataFrame(
        [
            {
                "case_id": case_row.get("case_id", details["case_id"]),
                "case_category": case_row.get("case_category", ""),
                "patient_id": case_row.get("patient_id", ""),
                "sample_id": case_row.get("sample_id", ""),
                "slide_id": case_row.get("slide_id", ""),
                "true_label": case_row.get("true_label", ""),
                "image_probability": case_row.get("image_probability", ""),
                "fusion_probability": case_row.get("fusion_probability", ""),
                "number_of_tiles_scored": details["n_tiles_scored"],
                "top_5_tile_refs": "; ".join(top_refs),
                "top_5_scores": "; ".join(top_scores),
                "bottom_5_tile_refs": "; ".join(bottom_refs),
                "bottom_5_scores": "; ".join(bottom_scores),
                "output_directory_external_ref": details["output_dir"],
                "interpretation_readiness_status": "READY_FOR_MANUAL_REVIEW" if details["structurally_valid"] else "NOT_READY",
                "warnings": "; ".join(details["warnings"]),
            }
        ]
    )


def _tile_ref(row: pd.Series, coord_cols: list[str]) -> str:
    if coord_cols:
        return ",".join(f"{c}={row.get(c, '')}" for c in coord_cols)
    if "tile_idx" in row:
        return f"tile_idx={row.get('tile_idx')}"
    if "rank" in row:
        return f"rank={row.get('rank')}"
    return f"row={row.name}"


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = [str(row.get(c, "")).replace("\n", " ").replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_reports(prefix: str, case_row: pd.Series, output_dir: Path, report_dir: Path) -> bool:
    audit, details, tile_df = audit_output_dir(str(case_row.get("case_id", "")), output_dir)
    interp = interpretation_summary(case_row, details, tile_df)
    report_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(report_dir / f"{prefix}_output_audit.csv", index=False)
    interp.to_csv(report_dir / f"{prefix}_interpretation_summary.csv", index=False)

    audit_lines = [
        f"# {prefix.replace('_', ' ').title()} Output Audit",
        "",
        f"- All expected outputs exist: `{bool(audit['exists'].all())}`",
        f"- Metadata valid: `{details['metadata_valid']}`",
        f"- Tile scores valid: `{details['tile_scores_valid']}`",
        f"- Number of tiles scored: `{details['n_tiles_scored']}`",
        f"- Top score range: `{details['top_score_min']}` to `{details['top_score_max']}`",
        f"- Images openable: `{details['images_openable']}`",
        f"- Structurally valid: `{details['structurally_valid']}`",
        "",
        "## Files",
        "",
        _markdown_table(audit),
    ]
    (report_dir / f"{prefix}_output_audit.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    interp_lines = [
        f"# {prefix.replace('_', ' ').title()} Interpretation Summary",
        "",
        _markdown_table(interp),
    ]
    (report_dir / f"{prefix}_interpretation_summary.md").write_text("\n".join(interp_lines) + "\n", encoding="utf-8")
    return bool(details["structurally_valid"])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit one LGD2+ histology dry-run output directory.")
    p.add_argument("--case-csv", default="reports/thesis_ch1/lgd2_histology_dry_run_cases.csv")
    p.add_argument("--case-id", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--report-dir", default="reports/thesis_ch1")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cases = pd.read_csv(args.case_csv)
    sub = cases[cases["case_id"].astype(str) == str(args.case_id)]
    if sub.empty:
        raise SystemExit(f"case_id not found: {args.case_id}")
    ok = write_reports(args.prefix, sub.iloc[0], Path(args.output_dir), Path(args.report_dir))
    print(f"{args.case_id} structurally_valid={ok}")
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
