#!/usr/bin/env python
"""Freeze the matched comparison set (Phase 2) and the immutable outer splits (Phase 3).

Reads an external strict pre-event cohort release, builds the matched sample manifest
(one canonical row per SampleID, shared by every primary model) and a deterministic
five-fold patient-disjoint outer split, writes them to the EXTERNAL release with
hashes, and emits lightweight Git audit summaries. No heavy data enters Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.matched_cohort import build_matched_manifest, model_input_equality  # noqa: E402
from barrett.data.splits import (  # noqa: E402
    assign_rows_to_folds, make_patient_folds, patient_labels, split_audit, validate_splits, N_FOLDS, SEED,
)

GIT_OUT = REPO_ROOT / "reports" / "thesis_ch1"
PRIMARY_FAMILIES = ["cnv_only", "image_uni2_abmil", "early_fusion", "intermediate_fusion", "late_fusion"]


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _atomic(df: pd.DataFrame, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".tmp"); df.to_csv(tmp, index=False); tmp.replace(dest)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release-dir", required=True, help="External cohort release dir (contains pre_event_cohort.csv).")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    release = Path(args.release_dir).resolve()
    if release == REPO_ROOT or REPO_ROOT in release.parents:
        raise SystemExit("release dir must be external to the clean repo")
    cohort_csv = release / "pre_event_cohort.csv"
    if not cohort_csv.exists():
        raise SystemExit(f"cohort not found: {cohort_csv} (run script 17 first)")
    meta_path = release / "cohort_release_metadata.json"
    release_id = json.loads(meta_path.read_text())["cohort_release_id"] if meta_path.exists() else release.name

    flagged = pd.read_csv(cohort_csv, low_memory=False)
    manifest, mproblems = build_matched_manifest(flagged, release_id)
    eq = model_input_equality(manifest, PRIMARY_FAMILIES)

    labels = patient_labels(manifest)
    folds = make_patient_folds(labels, n_folds=N_FOLDS, seed=SEED)
    rows_fold = assign_rows_to_folds(manifest, folds)
    sproblems = validate_splits(rows_fold, folds)
    audit = split_audit(folds, rows_fold)

    man_csv = release / "matched_manifest.csv"
    split_csv = release / "patient_splits.csv"
    if (man_csv.exists() or split_csv.exists()) and not args.overwrite:
        raise SystemExit("manifest/splits exist; pass --overwrite")
    _atomic(manifest, man_csv)
    _atomic(folds, split_csv)
    _atomic(rows_fold[["canonical_row_key", "patient_id", "outer_fold"]], release / "row_to_fold.csv")

    meta = {
        "cohort_release_id": release_id,
        "matched_manifest_sha256": _hash(man_csv),
        "patient_splits_sha256": _hash(split_csv),
        "n_units": int(len(manifest)), "n_patients": int(manifest["patient_id"].nunique()),
        "n_folds": N_FOLDS, "split_seed": SEED,
        "model_input_equality": eq,
        "matched_problems": mproblems, "split_problems": sproblems,
        "cnv_shared_units": int(manifest["cnv_shared_with_other_sample"].sum()),
        "gate_A_pass": bool(not mproblems and eq["equal"]),
        "gate_B_pass": bool(not sproblems),
    }
    (release / "split_release_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    GIT_OUT.mkdir(parents=True, exist_ok=True)
    _atomic(audit, GIT_OUT / "lgd2_final_split_audit.csv")
    (GIT_OUT / "lgd2_final_split_audit.md").write_text(
        f"# LGD2+ Final Outer Split Audit\n\nRelease `{release_id}`, seed {SEED}, {N_FOLDS}-fold patient-disjoint.\n\n"
        + _md(audit) + "\n")
    (GIT_OUT / "lgd2_final_split_warnings.md").write_text(
        "# LGD2+ Final Split Warnings\n\n" + ("\n".join(f"- {p}" for p in sproblems) or "- None.") + "\n")
    matched_audit = pd.DataFrame([{
        "n_units": meta["n_units"], "n_patients": meta["n_patients"],
        "cnv_shared_units": meta["cnv_shared_units"], "problems": "; ".join(mproblems) or "none"}])
    _atomic(matched_audit, GIT_OUT / "lgd2_final_matched_cohort_audit.csv")
    (GIT_OUT / "lgd2_final_matched_cohort_audit.md").write_text(
        f"# LGD2+ Final Matched Cohort Audit\n\nRelease `{release_id}`.\n\n" + _md(matched_audit) + "\n")
    (GIT_OUT / "lgd2_final_model_input_equality.md").write_text(
        f"# LGD2+ Model Input Equality\n\nAll primary families consume the identical canonical row-key set.\n\n"
        f"- Equal: `{eq['equal']}`\n- Keys: {eq['n_keys']}\n- Families: {', '.join(eq['families'])}\n")

    print(f"gate_A={meta['gate_A_pass']} gate_B={meta['gate_B_pass']} units={meta['n_units']} "
          f"patients={meta['n_patients']} matched_problems={mproblems} split_problems={sproblems}")
    return 0 if (meta["gate_A_pass"] and meta["gate_B_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
