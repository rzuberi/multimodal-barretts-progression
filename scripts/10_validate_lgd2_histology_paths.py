#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from barrett.utils.path_remap import (  # noqa: E402
    load_path_remap_config,
    redact_or_basename,
    resolve_existing_path,
)


DEFAULT_MASTER = "data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv"
DEFAULT_INDEX = (
    "data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/"
    "core_lvl2/uni2/runs/image/all_samples/core_gpu/index/virchow2_index.csv"
)


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = [str(row.get(c, "")).replace("\n", " ").replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _resolve_ref(path: str, remaps: list[dict[str, str]], roots: list[str]) -> tuple[str, bool, str]:
    return resolve_existing_path(path, remap_rules=remaps, candidate_roots=roots)


def _load_optional_table(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    if columns:
        available = pd.read_csv(path, nrows=0).columns.tolist()
        use = [c for c in columns if c in available]
        return pd.read_csv(path, usecols=use, low_memory=False)
    return pd.read_csv(path, low_memory=False)


def _status(exists: bool, required: bool) -> str:
    if exists:
        return "RESOLVED"
    if required:
        return "MISSING_REQUIRED"
    return "MISSING_OPTIONAL"


def _add_row(rows: list[dict[str, object]], case: pd.Series, field: str, original_ref: str, resolved: str, exists: bool, rule: str, required: bool, warning: str = "") -> None:
    rows.append(
        {
            "case_id": case.get("case_id", ""),
            "case_category": case.get("case_category", ""),
            "patient_id": case.get("patient_id", ""),
            "slide_basename": case.get("slide_basename", case.get("slide_id", "")),
            "field": field,
            "original_ref": redact_or_basename(original_ref),
            "resolved_ref": redact_or_basename(resolved),
            "exists": bool(exists),
            "remap_rule_used": rule,
            "required_for_dry_run": bool(required),
            "status": _status(bool(exists), bool(required)),
            "warning": warning,
        }
    )


def _pick_cases(args: argparse.Namespace) -> pd.DataFrame:
    all_cases = pd.read_csv(args.wsi_case_manifest)
    dry_path = Path(args.cases_csv)
    if args.check_all_8:
        return all_cases.copy()
    if args.dry_run_only or dry_path.exists():
        dry = pd.read_csv(dry_path)
        ids = set(dry["case_id"].astype(str))
        return all_cases[all_cases["case_id"].astype(str).isin(ids)].copy()
    return all_cases.copy()


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, list[str], dict[str, object]]:
    config_path = Path(args.path_remap_config)
    config_source = str(config_path)
    if not config_path.exists() and Path(args.template_remap_config).exists():
        config_path = Path(args.template_remap_config)
        config_source = str(config_path) + " (template fallback)"
    config = load_path_remap_config(config_path)
    remaps = list(config.get("remaps") or [])
    roots = list(config.get("candidate_roots") or [])
    roots.extend([str(REPO_ROOT.parent), str(REPO_ROOT.parent / "data")])

    cases = _pick_cases(args)
    sample_ids = set(cases["sample_id"].astype(str)) if "sample_id" in cases.columns else set()

    master_path, master_exists, master_rule = _resolve_ref(args.master_csv, remaps, roots)
    index_path, index_exists, index_rule = _resolve_ref(args.feature_index_csv, remaps, roots)
    master = _load_optional_table(Path(master_path), ["CNVAbsPath", "ImageAbsPath", "SampleID", "PatientID"])
    index = _load_optional_table(Path(index_path), ["sample_id", "npz_path", "status", "image_basename"])

    rows: list[dict[str, object]] = []
    warnings: list[str] = []
    if not master_exists:
        warnings.append(f"Master cohort table not resolved: {args.master_csv}")
    if not index_exists:
        warnings.append(f"Feature index not resolved: {args.feature_index_csv}")

    for _, case in cases.iterrows():
        sid = str(case.get("sample_id", ""))
        dry_required = True
        master_row = pd.DataFrame()
        if not master.empty and "CNVAbsPath" in master.columns:
            master_row = master[master["CNVAbsPath"].astype(str).str.endswith(sid)].head(1)
        index_row = pd.DataFrame()
        if not index.empty and "sample_id" in index.columns:
            index_row = index[index["sample_id"].astype(str).eq(sid)].head(1)

        slide_ref = ""
        if not master_row.empty and "ImageAbsPath" in master_row.columns:
            slide_ref = str(master_row.iloc[0]["ImageAbsPath"])
        elif "slide_id" in case:
            slide_ref = str(case.get("slide_id", ""))
        resolved, exists, rule = _resolve_ref(slide_ref, remaps, roots)
        warning = "" if exists else "raw_slide_unresolved"
        _add_row(rows, case, "raw_slide_path", slide_ref, resolved, exists, rule, dry_required, warning)

        basename = str(case.get("slide_basename", case.get("slide_id", "")))
        resolved, exists, rule = _resolve_ref(basename, remaps, roots)
        _add_row(rows, case, "slide_basename", basename, resolved, exists, rule, False, "" if exists else "basename_only_not_resolved")

        feature_ref = str(case.get("feature_path_ref", ""))
        if not index_row.empty and "npz_path" in index_row.columns:
            feature_ref = str(index_row.iloc[0]["npz_path"])
        resolved, exists, rule = _resolve_ref(feature_ref, remaps, roots)
        _add_row(rows, case, "uni2_feature_npz", feature_ref, resolved, exists, rule, dry_required, "" if exists else "feature_npz_unresolved")

        tile_ref = str(case.get("tile_coords_ref", ""))
        if tile_ref.startswith("coords in "):
            tile_ref = feature_ref
        resolved, exists, rule = _resolve_ref(tile_ref, remaps, roots)
        _add_row(rows, case, "tile_coordinates", tile_ref, resolved, exists, rule, dry_required, "" if exists else "tile_coordinates_unresolved")

        for field, out_field in [
            ("image_checkpoint_ref", "abmil_checkpoint"),
            ("fusion_checkpoint_ref", "early_mean_mlp_checkpoint"),
        ]:
            ckpt_ref = str(case.get(field, ""))
            resolved, exists, rule = _resolve_ref(ckpt_ref, remaps, roots)
            _add_row(rows, case, out_field, ckpt_ref, resolved, exists, rule, dry_required, "" if exists else f"{out_field}_unresolved")

        output_ref = str(case.get("external_output_ref", "analysis/lgd2_interpretation_regeneration_20260707/histology/"))
        parent_ref = str(Path(output_ref).parent)
        resolved, exists, rule = _resolve_ref(parent_ref, remaps, roots)
        _add_row(rows, case, "external_output_parent", parent_ref, resolved, exists, rule, False, "" if exists else "output_parent_missing")

    audit = pd.DataFrame(rows)
    meta = {
        "config_source": config_source,
        "remap_rules": remaps,
        "candidate_roots": roots,
        "cases_checked": int(len(cases)),
        "sample_ids": sorted(sample_ids),
        "master_resolved": bool(master_exists),
        "feature_index_resolved": bool(index_exists),
        "master_rule": master_rule,
        "feature_index_rule": index_rule,
    }
    return audit, warnings, meta


def _write_reports(audit: pd.DataFrame, warnings: list[str], meta: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = out_dir / "lgd2_histology_path_remap_audit.csv"
    audit_md = out_dir / "lgd2_histology_path_remap_audit.md"
    warn_md = out_dir / "lgd2_histology_path_remap_warnings.md"
    audit.to_csv(audit_csv, index=False)

    required = audit[audit["required_for_dry_run"].astype(bool)].copy()
    fully = 0
    for _, group in required.groupby("case_id"):
        if bool(group["exists"].all()):
            fully += 1
    missing = required[~required["exists"].astype(bool)]
    missing_by_field = missing["field"].value_counts().to_dict()
    can_proceed = bool(not required.empty and required["exists"].all())

    lines = [
        "# LGD2+ Histology Path Remap Audit",
        "",
        f"- Cases checked: {meta['cases_checked']}",
        f"- Fully resolvable cases: {fully}",
        f"- Dry-run can proceed in this shell: `{can_proceed}`",
        f"- Config source: `{meta['config_source']}`",
        f"- Master table resolved: `{meta['master_resolved']}` via `{meta['master_rule']}`",
        f"- Feature index resolved: `{meta['feature_index_resolved']}` via `{meta['feature_index_rule']}`",
        "",
        "## Missing Required Fields",
        "",
    ]
    if missing_by_field:
        lines.extend([f"- `{k}`: {v}" for k, v in sorted(missing_by_field.items())])
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Remap Rules Attempted",
            "",
        ]
    )
    rules = meta.get("remap_rules") or []
    if rules:
        for rule in rules:
            lines.append(f"- `{rule.get('from', '')}` -> `{rule.get('to', '')}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Candidate Roots", ""])
    for root in meta.get("candidate_roots") or []:
        lines.append(f"- `{root}`")
    lines.extend(
        [
            "",
            "## Required Missing Rows",
            "",
            _markdown_table(missing[["case_id", "field", "original_ref", "resolved_ref", "remap_rule_used", "warning"]].head(50)),
            "",
            "## Next Action",
            "",
        ]
    )
    if can_proceed:
        lines.append("Path validation passed for required dry-run fields. A case-level WSI dry run can be attempted externally.")
    else:
        lines.append(
            "Do not run WSI explainability in this shell. Resolve the missing WSI/feature/checkpoint paths with `configs/path_remap.local.yaml` "
            "or run from a node/session where the required mounts exist."
        )
    audit_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    warn_lines = ["# LGD2+ Histology Path Remap Warnings", ""]
    warn_lines.extend([f"- {w}" for w in warnings] or ["- No table-level warnings."])
    if not missing.empty:
        warn_lines.extend(["", "## Missing Required References", ""])
        for _, r in missing.iterrows():
            warn_lines.append(f"- `{r.case_id}` `{r.field}`: {r.warning} (`{r.original_ref}`)")
    warn_md.write_text("\n".join(warn_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate LGD2+ histology dry-run paths with optional remapping.")
    p.add_argument("--wsi-case-manifest", default="reports/thesis_ch1/lgd2_wsi_case_manifest.csv")
    p.add_argument("--cases-csv", default="reports/thesis_ch1/lgd2_histology_dry_run_cases.csv")
    p.add_argument("--path-remap-config", default="configs/path_remap.local.yaml")
    p.add_argument("--template-remap-config", default="configs/path_remap.template.yaml")
    p.add_argument("--master-csv", default=DEFAULT_MASTER)
    p.add_argument("--feature-index-csv", default=DEFAULT_INDEX)
    p.add_argument("--check-all-8", action="store_true")
    p.add_argument("--dry-run-only", action="store_true")
    p.add_argument("--output-dir", default="reports/thesis_ch1")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    audit, warnings, meta = build_audit(args)
    _write_reports(audit, warnings, meta, Path(args.output_dir))
    checked = int(meta["cases_checked"])
    full = audit[audit["required_for_dry_run"].astype(bool)].groupby("case_id")["exists"].all().sum()
    print(f"Wrote path audit for {checked} cases; fully_resolvable={int(full)}")


if __name__ == "__main__":
    main()
