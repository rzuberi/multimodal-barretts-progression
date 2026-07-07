"""Lightweight CNV interpretation summary helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


WINDOW_HINTS = ["window", "bin", "region", "feature", "chromosome", "chr", "arm"]
GENE_HINTS = ["gene", "gene_name", "symbol"]
IMPORTANCE_HINTS = ["importance", "contribution", "coef", "shap", "score", "rank"]


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def find_case_output_files(output_dir: Path, case_id: str) -> dict[str, list[Path]]:
    """Find likely lightweight top-window/top-gene files for a case."""
    if not output_dir.exists():
        return {"windows": [], "genes": []}
    candidates = list(output_dir.glob(f"**/*{case_id}*.csv")) + list((output_dir / case_id).glob("**/*.csv"))
    windows = [p for p in candidates if any(token in p.name.lower() for token in ["window", "bin", "region"])]
    genes = [p for p in candidates if "gene" in p.name.lower()]
    return {"windows": sorted(set(windows)), "genes": sorted(set(genes))}


def _best_column(df: pd.DataFrame, hints: list[str]) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for hint in hints:
        for low, original in lower.items():
            if hint in low:
                return original
    return None


def _top_values(files: list[Path], hints: list[str], n: int = 5) -> tuple[str, str]:
    values: list[str] = []
    source = ""
    for path in files:
        df = _read_optional_csv(path)
        if df.empty:
            continue
        col = _best_column(df, hints)
        if col is None:
            continue
        if not source:
            source = path.name
        values.extend(df[col].dropna().astype(str).head(n).tolist())
        if len(values) >= n:
            break
    return "; ".join(values[:n]), source


def _top_chromosomes(window_text: str) -> str:
    pieces: list[str] = []
    for token in window_text.replace(";", " ").replace(",", " ").split():
        if token.lower().startswith("chr") or token.lower() in {"x", "y"}:
            pieces.append(token)
    seen = []
    for piece in pieces:
        if piece not in seen:
            seen.append(piece)
    return "; ".join(seen[:5])


def interpretation_sentence(row: pd.Series, has_outputs: bool) -> str:
    if not has_outputs:
        return "CNV interpretation outputs are not available yet for this selected case."
    if row["cnv_prediction_correct"] == "correct" and row["fusion_prediction_correct"] == "correct":
        return "CNV and fusion both support the true label; inspect recurrent windows/genes for shared signal."
    if row["cnv_prediction_correct"] == "correct":
        return "CNV-only prediction is correct; inspect top windows/genes as a potential molecular rescue signal."
    if row["fusion_prediction_correct"] == "correct":
        return "Fusion is correct despite CNV-only error; CNV regions should be interpreted as supporting or conflicting evidence."
    return "CNV-only and fusion are both wrong; use this as a limitation case if regions are biologically plausible."


def summarize_cnv_interpretation(
    cases: pd.DataFrame,
    output_dir: Path,
    top_windows_csv: Path | None = None,
    top_genes_csv: Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Summarize case-level CNV interpretation outputs if they exist."""
    warnings: list[str] = []
    global_windows = _read_optional_csv(top_windows_csv) if top_windows_csv else pd.DataFrame()
    global_genes = _read_optional_csv(top_genes_csv) if top_genes_csv else pd.DataFrame()
    if not output_dir.exists():
        warnings.append(f"External CNV interpretation output directory not found: {output_dir}")
    rows = []
    for _, case in cases.iterrows():
        case_id = str(case["case_id"])
        found = find_case_output_files(output_dir, case_id)
        window_text, window_source = _top_values(found["windows"], WINDOW_HINTS)
        gene_text, gene_source = _top_values(found["genes"], GENE_HINTS)
        if not window_text and not global_windows.empty and "case_id" in global_windows.columns:
            sub = global_windows[global_windows["case_id"].astype(str).eq(case_id)]
            if not sub.empty:
                col = _best_column(sub, WINDOW_HINTS)
                if col:
                    window_text = "; ".join(sub[col].dropna().astype(str).head(5))
                    window_source = top_windows_csv.name if top_windows_csv else "global_top_windows"
        if not gene_text and not global_genes.empty and "case_id" in global_genes.columns:
            sub = global_genes[global_genes["case_id"].astype(str).eq(case_id)]
            if not sub.empty:
                col = _best_column(sub, GENE_HINTS)
                if col:
                    gene_text = "; ".join(sub[col].dropna().astype(str).head(5))
                    gene_source = top_genes_csv.name if top_genes_csv else "global_top_genes"
        has_outputs = bool(window_text or gene_text)
        row = {
            "case_id": case_id,
            "case_category": case["category"],
            "patient_id": case["patient_id"],
            "cnv_id": case["cnv_id"],
            "true_label": case["true_label"],
            "cnv_probability": case["CNV_probability"],
            "fusion_probability": case["early_fusion_probability"],
            "cnv_prediction_correct": case["prediction_correctness_cnv"],
            "fusion_prediction_correct": case["prediction_correctness_early_fusion"],
            "top_cnv_windows": window_text or "MISSING",
            "top_genes": gene_text or "MISSING",
            "top_chromosomes_or_arms": _top_chromosomes(window_text) or "MISSING",
            "importance_source": "; ".join(x for x in [window_source, gene_source] if x) or "MISSING",
            "external_cnv_output_ref": str((output_dir / case_id).as_posix()),
            "warnings": "" if has_outputs else "Missing external CNV interpretation outputs for this case.",
        }
        row["cnv_interpretation_sentence"] = interpretation_sentence(pd.Series(row), has_outputs)
        rows.append(row)
    return pd.DataFrame(rows), warnings

