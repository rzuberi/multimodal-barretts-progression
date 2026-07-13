#!/usr/bin/env python
"""Build the strict pre-event LGD2+ cohort release (Phase 1).

Derives current-event/next-biopsy endpoint from source columns under the locked
two-consecutive-LGD rule, validates stored-vs-derived endpoint agreement, derives
temporal eligibility from the full per-patient timeline (NOT the canonical
EventDate, which uses an LGDx3 rule), and writes a versioned EXTERNAL cohort
release plus lightweight Git summaries. No heavy data enters Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.pre_event import (  # noqa: E402
    add_derived_labels, build_pre_event_flags, cohort_flow, patient_col, validate_event_dates,
)
from barrett.labels.endpoints import LGD2_ENDPOINT  # noqa: E402

DEFAULT_MASTER = "data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv"
GIT_OUT = REPO_ROOT / "reports" / "thesis_ch1"


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment-root", default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"))
    ap.add_argument("--master", default=DEFAULT_MASTER, help="Master CSV, relative to experiment root.")
    ap.add_argument("--release-root", default="", help="External release dir. Default: analysis/chapter1_lgd2_final_pre_event_<ts>.")
    ap.add_argument("--timestamp", default="", help="Override release timestamp (for determinism).")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    root = Path(args.experiment_root).resolve() if args.experiment_root else REPO_ROOT.parent.resolve()
    master_path = (root / args.master) if not Path(args.master).is_absolute() else Path(args.master)
    if not master_path.exists():
        raise SystemExit(f"master not found: {master_path}")

    ts = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    release = Path(args.release_root) if args.release_root else (root / f"analysis/chapter1_lgd2_final_pre_event_{ts}")
    if release.resolve() == REPO_ROOT or REPO_ROOT in release.resolve().parents:
        raise SystemExit(f"Refusing to write cohort release inside the clean repo: {release}")
    cohort_csv = release / "pre_event_cohort.csv"
    if cohort_csv.exists() and not args.overwrite:
        raise SystemExit(f"{cohort_csv} exists; pass --overwrite to replace.")
    release.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(master_path, low_memory=False)
    pc = patient_col(df)
    flagged = build_pre_event_flags(df)

    # endpoint agreement gate
    agr = add_derived_labels(df)["endpoint_agrees"].dropna()
    disagree = int((agr == 0).sum())
    ev_val = validate_event_dates(flagged)

    # external cohort release (atomic)
    tmp = cohort_csv.with_suffix(".tmp")
    flagged.to_csv(tmp, index=False)
    tmp.replace(cohort_csv)

    flow = cohort_flow(flagged)
    warnings = []
    if disagree:
        warnings.append(f"BLOCK: {disagree} rows disagree between stored and derived endpoint.")
    if ev_val["disagree"]:
        warnings.append(
            f"Canonical EventDate disagrees with the locked two-LGD timeline for {ev_val['disagree']}/"
            f"{ev_val['patients_compared']} event patients (max {ev_val['max_abs_days']} days). "
            "Canonical EventDate uses an LGDx3 rule and is NOT used for eligibility; the event boundary "
            "is derived from the full timeline under the locked two-consecutive-LGD rule."
        )

    meta = {
        "cohort_release_id": f"chapter1_lgd2_final_pre_event_{ts}",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generation_command": "scripts/17_build_lgd2_pre_event_cohort.py",
        "code_git_commit": _git_commit(),
        "source_master": str(master_path),
        "source_master_sha256": _hash(master_path),
        "lgd2_module_sha256": _hash(REPO_ROOT / "src/barrett/labels/lgd2.py"),
        "pre_event_module_sha256": _hash(REPO_ROOT / "src/barrett/data/pre_event.py"),
        "rows": int(len(flagged)),
        "patients": int(flagged[pc].nunique()),
        "endpoint": LGD2_ENDPOINT,
        "endpoint_evaluable_rows": int(flagged["endpoint_evaluable"].sum()),
        "endpoint_disagreements": disagree,
        "eventdate_validation": ev_val,
        "strict_pre_event_eligible_rows": int(flagged["strict_pre_event_eligible"].sum()),
        "strict_pre_event_eligible_patients": int(flagged.loc[flagged["strict_pre_event_eligible"], pc].nunique()),
        "exclusion_counts": flagged["exclusion_reason"].value_counts().to_dict(),
        "warnings": warnings,
        "blocked": bool(disagree),
    }
    (release / "cohort_release_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # lightweight Git summaries
    GIT_OUT.mkdir(parents=True, exist_ok=True)
    flow.to_csv(GIT_OUT / "lgd2_final_pre_event_cohort_flow.csv", index=False)
    (GIT_OUT / "lgd2_final_pre_event_cohort_flow.md").write_text(
        f"# LGD2+ Strict Pre-Event Cohort Flow\n\nRelease `{meta['cohort_release_id']}`. "
        f"Endpoint `{LGD2_ENDPOINT}`, locked two-consecutive-LGD rule.\n\n" + _md_table(flow) + "\n"
    )
    (GIT_OUT / "lgd2_final_pre_event_timing_audit.md").write_text(
        "# LGD2+ Pre-Event Timing Audit\n\n"
        f"- Endpoint evaluable rows: {meta['endpoint_evaluable_rows']}\n"
        f"- Stored-vs-derived endpoint disagreements: {disagree}\n"
        f"- EventDate vs locked-timeline validation: {json.dumps(ev_val)}\n"
        f"- Eligible rows: {meta['strict_pre_event_eligible_rows']}; "
        f"patients: {meta['strict_pre_event_eligible_patients']}\n"
        "- Canonical EventDate uses an LGDx3 rule; eligibility uses timeline-derived two-LGD event dates.\n"
    )
    (GIT_OUT / "lgd2_final_pre_event_warnings.md").write_text(
        "# LGD2+ Pre-Event Cohort Warnings\n\n" + ("\n".join(f"- {w}" for w in warnings) or "- None.") + "\n"
    )

    print(f"cohort_release={meta['cohort_release_id']} eligible_rows={meta['strict_pre_event_eligible_rows']} "
          f"eligible_patients={meta['strict_pre_event_eligible_patients']} blocked={meta['blocked']}")
    return 1 if meta["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
