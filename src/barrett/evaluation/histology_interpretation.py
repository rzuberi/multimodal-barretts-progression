from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Iterable

import pandas as pd


IMAGE_MODEL = "abmil"
FUSION_MODEL = "early_mean_mlp"
FEATURE_MODEL = "uni2"
EXTERNAL_HISTOLOGY_ROOT = "analysis/lgd2_interpretation_regeneration_20260707/histology"


def resolve_external_path(path: str, external_root: str | Path = "..") -> Path:
    p = Path(str(path))
    if p.exists():
        return p
    root_path = Path(external_root) / str(path)
    return root_path


def compact_external_ref(path: str | Path) -> str:
    """Return a non-mounted external reference for sensitive absolute paths."""
    s = str(path)
    if not s or s.lower() == "nan":
        return ""
    marker = "foundation_outputs/"
    if marker in s:
        return s.split(marker, 1)[1]
    marker = "foundation_grid_runs/"
    if marker in s:
        return "foundation_grid_runs/" + s.split(marker, 1)[1]
    marker = "SWGCohort/"
    if marker in s:
        return "SWGCohort/" + s.split(marker, 1)[1]
    parts = Path(s).parts
    if len(parts) >= 3 and Path(s).suffix:
        return "/".join(parts[-3:])
    return Path(s).name


def slide_basename(slide_id: str) -> str:
    return Path(str(slide_id)).name


def load_manifest_row(manifest: pd.DataFrame, result_id: str) -> pd.Series | None:
    rows = manifest[manifest["result_id"].astype(str) == str(result_id)]
    if rows.empty:
        return None
    return rows.iloc[0]


def expand_brace_pattern(pattern: str) -> list[str]:
    s = str(pattern)
    if "{1..5}" in s:
        return [s.replace("{1..5}", str(i)) for i in range(1, 6)]
    return [s]


def find_prediction_rows(
    prediction_pattern: str,
    sample_ids: Iterable[str],
    external_root: str | Path = "..",
    model_name: str | None = None,
) -> pd.DataFrame:
    sample_set = {str(x) for x in sample_ids}
    rows = []
    for pattern in expand_brace_pattern(prediction_pattern):
        for path in sorted(glob.glob(str(resolve_external_path(pattern, external_root)))):
            try:
                df = pd.read_csv(path, low_memory=False)
            except Exception:
                continue
            if "sample_id" not in df.columns:
                continue
            sub = df[df["sample_id"].astype(str).isin(sample_set)].copy()
            if model_name and "model_name" in sub.columns:
                sub = sub[sub["model_name"].astype(str) == str(model_name)].copy()
            if sub.empty:
                continue
            sub["prediction_file_ref"] = compact_external_ref(path)
            sub["prediction_file_path"] = str(path)
            metric_path = str(path).replace("/predictions_", "/metrics_").replace(".csv", ".json")
            sub["metrics_json_ref"] = compact_external_ref(metric_path)
            sub["metrics_json_path"] = metric_path if os.path.exists(metric_path) else ""
            rows.append(sub)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    return out.drop_duplicates(subset=["sample_id", "fold", "model_name"], keep="first")


def load_feature_index(index_csv: str | Path) -> pd.DataFrame:
    if not str(index_csv):
        return pd.DataFrame()
    p = Path(index_csv)
    if (not p.exists()) or p.is_dir():
        return pd.DataFrame()
    cols = pd.read_csv(p, nrows=0).columns.tolist()
    use = [c for c in ["sample_id", "npz_path", "status", "n_instances", "feat_dim", "image_basename"] if c in cols]
    if not use:
        return pd.DataFrame()
    return pd.read_csv(p, usecols=use, low_memory=False)


def find_checkpoint(cv_dir: str | Path, model_name: str, fold: int, task: str, variant_token: str = "") -> str:
    cv = Path(cv_dir)
    if not cv.exists():
        return ""
    if variant_token:
        pattern = f"*all_samples_{model_name}_{variant_token}_{task}*rep01_fold{int(fold)}_best.pt"
    else:
        pattern = f"*all_samples_{model_name}_{task}_rep01_fold{int(fold)}_best.pt"
    hits = sorted(cv.glob(pattern))
    return str(hits[0]) if hits else ""


def build_wsi_case_manifest(
    cases: pd.DataFrame,
    final_manifest: pd.DataFrame,
    external_root: str | Path = "..",
    feature_index_csv: str = "",
    external_output_root: str = EXTERNAL_HISTOLOGY_ROOT,
) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    out = cases.copy()
    out["case_category"] = out.get("category", "")
    out["slide_basename"] = out["slide_id"].map(slide_basename)
    out["feature_model"] = FEATURE_MODEL
    out["image_model"] = IMAGE_MODEL
    out["fusion_model"] = FUSION_MODEL
    out["case_timing"] = out["DaysFromCurrentToEvent"].map(lambda x: "early_prediction_only" if pd.to_numeric(x, errors="coerce") != 0 else "at_event")
    out["is_at_event"] = pd.to_numeric(out["DaysFromCurrentToEvent"], errors="coerce").fillna(-1).eq(0)
    out["is_early_prediction_only"] = ~out["is_at_event"]

    image_row = load_manifest_row(final_manifest, "lgd2_image_uni2")
    fusion_row = load_manifest_row(final_manifest, "lgd2_early_fusion_uni2")
    if image_row is None:
        warnings.append("Manifest row missing: lgd2_image_uni2")
    if fusion_row is None:
        warnings.append("Manifest row missing: lgd2_early_fusion_uni2")

    image_pred = find_prediction_rows(
        "" if image_row is None else str(image_row["prediction_file"]),
        out["sample_id"].astype(str),
        external_root=external_root,
        model_name=IMAGE_MODEL,
    )
    fusion_pred = find_prediction_rows(
        "" if fusion_row is None else str(fusion_row["prediction_file"]),
        out["sample_id"].astype(str),
        external_root=external_root,
        model_name=FUSION_MODEL,
    )

    if image_pred.empty:
        warnings.append("No selected cases found in lgd2_image_uni2 abmil prediction files.")
    if fusion_pred.empty:
        warnings.append("No selected cases found in lgd2_early_fusion_uni2 early_mean_mlp prediction files.")

    if not feature_index_csv and not image_pred.empty:
        metric_paths = [p for p in image_pred["metrics_json_path"].astype(str).tolist() if p]
        if metric_paths:
            try:
                import json

                metric = json.load(open(metric_paths[0]))
                feature_index_csv = str(metric.get("index_csv", ""))
            except Exception:
                feature_index_csv = ""
    feature_index_path = resolve_external_path(feature_index_csv, external_root) if feature_index_csv else Path("")
    idx = load_feature_index(feature_index_path)
    if idx.empty:
        warnings.append("Feature index missing or unreadable.")

    rows = []
    for _, r in out.iterrows():
        sid = str(r["sample_id"])
        warns = []
        idx_row = idx[idx["sample_id"].astype(str) == sid].head(1) if not idx.empty else pd.DataFrame()
        feat_ref = ""
        tile_ref = ""
        if idx_row.empty:
            warns.append("feature_index_row_missing")
        else:
            npz_path = str(idx_row.iloc[0].get("npz_path", ""))
            feat_ref = compact_external_ref(npz_path)
            tile_ref = "coords in " + feat_ref if feat_ref else ""
            if str(idx_row.iloc[0].get("status", "")).lower() != "ok":
                warns.append("feature_index_status_not_ok")

        img = image_pred[image_pred["sample_id"].astype(str) == sid].head(1) if not image_pred.empty else pd.DataFrame()
        fus = fusion_pred[fusion_pred["sample_id"].astype(str) == sid].head(1) if not fusion_pred.empty else pd.DataFrame()
        fold = ""
        img_ckpt_ref = ""
        fus_ckpt_ref = ""
        if img.empty:
            warns.append("image_prediction_row_missing")
        else:
            fold = int(img.iloc[0].get("fold", 0))
            img_cv = Path(str(img.iloc[0].get("prediction_file_path", ""))).parent
            img_ckpt = find_checkpoint(img_cv, IMAGE_MODEL, fold, "NextBiopsyProgression_LGD2plus")
            img_ckpt_ref = compact_external_ref(img_ckpt)
            if not img_ckpt:
                warns.append("image_checkpoint_missing")
        if fus.empty:
            warns.append("fusion_prediction_row_missing")
        else:
            fold = fold or int(fus.iloc[0].get("fold", 0))
            fus_cv = Path(str(fus.iloc[0].get("prediction_file_path", ""))).parent
            fus_ckpt = find_checkpoint(
                fus_cv,
                FUSION_MODEL,
                int(fus.iloc[0].get("fold", 0)),
                "NextBiopsyProgression_LGD2plus",
                variant_token="windows_armdiff_plus_arms_plus_cx",
            )
            fus_ckpt_ref = compact_external_ref(fus_ckpt)
            if not fus_ckpt:
                warns.append("fusion_checkpoint_missing")

        rows.append(
            {
                "case_id": r["case_id"],
                "case_category": r["case_category"],
                "patient_id": r["patient_id"],
                "biopsy_id": r.get("biopsy_id", ""),
                "sample_id": sid,
                "slide_id": r["slide_id"],
                "slide_basename": r["slide_basename"],
                "feature_model": FEATURE_MODEL,
                "feature_path_ref": feat_ref,
                "tile_coords_ref": tile_ref,
                "attention_source_ref": "MISSING_LGD2_TILE_SCORES",
                "image_model": IMAGE_MODEL,
                "fusion_model": FUSION_MODEL,
                "fold": fold,
                "image_checkpoint_ref": img_ckpt_ref,
                "fusion_checkpoint_ref": fus_ckpt_ref,
                "true_label": r["true_label"],
                "image_probability": r["image_probability"],
                "fusion_probability": r["early_fusion_probability"],
                "case_timing": r["case_timing"],
                "is_early_prediction_only": bool(r["is_early_prediction_only"]),
                "is_at_event": bool(r["is_at_event"]),
                "recommended_histology_output_type": "top_patches; tile_scores; heatmap_overlay; attention_spread",
                "external_output_ref": f"{external_output_root.rstrip('/')}/{r['case_id']}/",
                "warnings": "; ".join(warns),
            }
        )
    return pd.DataFrame(rows), warnings


def histology_sentence(row: pd.Series, has_outputs: bool) -> str:
    cid = str(row.get("case_id", "case"))
    img = row.get("image_probability", "")
    fus = row.get("fusion_probability", "")
    if not has_outputs:
        return f"{cid}: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities ({img}, {fus})."
    top = str(row.get("top_patch_refs", "") or "top patches")
    return f"{cid}: regenerated histology outputs highlight {top}; compare image probability {img} with fusion probability {fus}."


def summarize_histology_outputs(
    manifest: pd.DataFrame,
    output_dir: str | Path,
    top_patch_csv: str | Path | None = None,
    attention_csv: str | Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    out_dir = Path(output_dir)
    if not out_dir.exists():
        warnings.append(f"External histology output directory not found: {output_dir}")

    top_df = pd.DataFrame()
    att_df = pd.DataFrame()
    if top_patch_csv:
        if Path(top_patch_csv).exists():
            top_df = pd.read_csv(top_patch_csv, low_memory=False)
        else:
            warnings.append(f"Top-patch CSV not found: {top_patch_csv}")
    if attention_csv:
        if Path(attention_csv).exists():
            att_df = pd.read_csv(attention_csv, low_memory=False)
        else:
            warnings.append(f"Attention summary CSV not found: {attention_csv}")

    rows = []
    for _, r in manifest.iterrows():
        cid = str(r["case_id"])
        case_warn = []
        top_refs = ""
        attention_summary = ""
        attention_spread = ""
        number_of_top_patches = ""
        number_of_tiles_scored = ""
        case_dir = out_dir / cid
        case_files = []
        case_dirs = []
        if case_dir.exists():
            case_dirs = [case_dir]
            case_files = [str(p) for p in case_dir.glob("**/*") if p.is_file()]
        else:
            sample_id = str(r.get("sample_id", ""))
            if sample_id:
                meta_hits = sorted(out_dir.glob(f"**/*__{sample_id}__fold*/metadata.json"))
                case_dirs = sorted({p.parent for p in meta_hits})
                for d in case_dirs:
                    case_files.extend([str(p) for p in d.glob("*") if p.is_file()])
        names = [Path(p).name.lower() for p in case_files]

        if not top_df.empty and "case_id" in top_df.columns:
            sub = top_df[top_df["case_id"].astype(str) == cid]
            if not sub.empty:
                cols = [c for c in ["top_patch_refs", "patch_ref", "tile_ref", "top_tiles_grid_png"] if c in sub.columns]
                if cols:
                    top_refs = "; ".join(sub[cols[0]].astype(str).head(5).tolist())
        if not att_df.empty and "case_id" in att_df.columns:
            sub = att_df[att_df["case_id"].astype(str) == cid]
            if not sub.empty:
                if "attention_summary" in sub.columns:
                    attention_summary = str(sub.iloc[0]["attention_summary"])
                if "attention_spread" in sub.columns:
                    attention_spread = str(sub.iloc[0]["attention_spread"])

        if not top_refs and case_files:
            hits = [compact_external_ref(p) for p in case_files if "top" in Path(p).name.lower()][:5]
            top_refs = "; ".join(hits)
        top_patches_generated = bool(top_refs)
        tile_score_paths = [Path(p) for p in case_files if Path(p).name.lower() == "tile_scores.csv" or "tile_score" in Path(p).name.lower()]
        heatmap_paths = [Path(p) for p in case_files if "heatmap" in Path(p).name.lower() and Path(p).suffix.lower() in {".png", ".jpg", ".jpeg"}]
        overlay_paths = [Path(p) for p in case_files if "overlay" in Path(p).name.lower() and Path(p).suffix.lower() in {".png", ".jpg", ".jpeg"}]
        attention_tile_scores_generated = bool(tile_score_paths) or bool(attention_summary)
        heatmaps_overlays_generated = bool(heatmap_paths or overlay_paths)
        metadata_paths = [Path(p) for p in case_files if Path(p).name.lower() == "metadata.json"]
        command_run = bool(case_files)
        command_success = bool(metadata_paths and tile_score_paths and (heatmap_paths or overlay_paths))
        if tile_score_paths:
            try:
                number_of_tiles_scored = str(max(0, sum(1 for _ in open(tile_score_paths[0], encoding="utf-8")) - 1))
            except Exception:
                number_of_tiles_scored = ""
        if metadata_paths:
            try:
                import json

                meta = json.load(open(metadata_paths[0], encoding="utf-8"))
                if not number_of_tiles_scored and meta.get("n_tiles_used", "") != "":
                    number_of_tiles_scored = str(meta.get("n_tiles_used", ""))
            except Exception:
                pass
        if top_refs:
            number_of_top_patches = str(len([x for x in top_refs.split(";") if x.strip()]))
        if not top_refs and not attention_summary:
            case_warn.append("Missing external histology interpretation outputs for this case.")

        row = {
            "case_id": cid,
            "case_category": r.get("case_category", ""),
            "patient_id": r.get("patient_id", ""),
            "slide_id": r.get("slide_id", ""),
            "true_label": r.get("true_label", ""),
            "image_probability": r.get("image_probability", ""),
            "fusion_probability": r.get("fusion_probability", ""),
            "command_run": command_run,
            "command_success": command_success,
            "top_patch_refs": top_refs or "MISSING",
            "top_patches_generated": top_patches_generated,
            "tile_scores_generated": bool(tile_score_paths),
            "attention_scores_generated": attention_tile_scores_generated,
            "heatmap_generated": bool(heatmap_paths),
            "overlay_generated": bool(overlay_paths),
            "attention_tile_scores_generated": attention_tile_scores_generated,
            "heatmaps_overlays_generated": heatmaps_overlays_generated,
            "number_of_top_patches": number_of_top_patches,
            "number_of_tiles_scored": number_of_tiles_scored,
            "attention_summary": attention_summary or "MISSING",
            "attention_spread": attention_spread or "MISSING",
            "external_histology_output_ref": "; ".join(str(d) for d in case_dirs) if case_dirs else str(case_dir),
            "warnings": "; ".join(case_warn),
        }
        row["histology_interpretation_sentence"] = histology_sentence(pd.Series(row), has_outputs=not case_warn)
        row["interpretation_readiness_sentence"] = (
            "Ready for thesis review: top patches, tile scores, and heatmap/overlay outputs were found."
            if (top_patches_generated and attention_tile_scores_generated and heatmaps_overlays_generated)
            else "Not ready for thesis figure selection: regenerated histology outputs are missing or incomplete."
        )
        rows.append(row)
    return pd.DataFrame(rows), warnings
