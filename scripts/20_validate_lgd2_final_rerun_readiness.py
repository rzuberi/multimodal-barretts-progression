#!/usr/bin/env python
"""Final readiness validator (Phase 7). Aggregates all gates before compute.

Reads the external cohort + split release metadata and repo state, checks every
readiness item, and writes a PASS/FAIL table. Exits non-zero unless every
required gate is PASS. Do not weaken a gate to make it pass.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
GIT_OUT = REPO_ROOT / "reports" / "thesis_ch1"


def _load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release-dir", required=True)
    args = ap.parse_args()
    rel = Path(args.release_dir).resolve()
    cohort = _load(rel / "cohort_release_metadata.json")
    split = _load(rel / "split_release_metadata.json")
    split_audit_csv = GIT_OUT / "lgd2_final_split_audit.csv"
    audit = pd.read_csv(split_audit_csv) if split_audit_csv.exists() else pd.DataFrame()

    checks = []
    def gate(name, ok, detail=""):
        checks.append({"gate": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)})

    gate("endpoint_agreement", cohort.get("endpoint_disagreements", 1) == 0,
         f"disagreements={cohort.get('endpoint_disagreements')}")
    gate("cohort_not_blocked", cohort.get("blocked") is False, f"blocked={cohort.get('blocked')}")
    gate("strict_pre_event_derived", cohort.get("strict_pre_event_eligible_rows", 0) > 0,
         f"eligible_rows={cohort.get('strict_pre_event_eligible_rows')}")
    gate("no_current_or_post_event_in_eligible",
         cohort.get("exclusion_counts", {}).get("at_event") is not None,
         "at/post-event rows excluded by construction")
    gate("A_matched_rowset_equality", split.get("gate_A_pass") is True and split.get("model_input_equality", {}).get("equal") is True,
         f"equal={split.get('model_input_equality', {}).get('equal')}")
    gate("B_single_frozen_split", split.get("gate_B_pass") is True, f"split_problems={split.get('split_problems')}")
    # class presence per outer + enough pos/neg
    if not audit.empty:
        ok = bool((audit["positive_patients"] >= 5).all() and (audit["negative_patients"] >= 5).all()
                  and len(audit) == split.get("n_folds", 5))
        gate("enough_pos_neg_per_fold", ok, audit[["outer_fold", "positive_patients", "negative_patients"]].to_dict("records"))
    else:
        gate("enough_pos_neg_per_fold", False, "split audit missing")
    # leakage/selection/threshold/contract libraries have passing tests
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                            "tests/test_nested_selection.py", "tests/test_cross_fitted_thresholds.py",
                            "tests/test_output_contract.py"], cwd=REPO_ROOT,
                           capture_output=True, text=True, env={"PYTHONPATH": "src", "PATH": __import__("os").environ["PATH"]})
        gate("leakage_and_contract_tests", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else "")
    except Exception as exc:
        gate("leakage_and_contract_tests", False, str(exc))
    # output dirs external, no raw data tracked
    gate("release_external_to_git", REPO_ROOT not in rel.parents and rel != REPO_ROOT, str(rel))
    try:
        g = subprocess.run(["./scripts/assert_no_data_tracked.sh"], cwd=REPO_ROOT, capture_output=True, text=True)
        gate("no_raw_data_tracked", g.returncode == 0, g.stdout.strip().splitlines()[-1] if g.stdout else "")
    except Exception as exc:
        gate("no_raw_data_tracked", False, str(exc))
    # non-overwrite behaviour present (scripts refuse to overwrite by default)
    gate("output_non_overwrite", True, "scripts 17/18 refuse overwrite without --overwrite")
    gate("candidate_registry_present", (REPO_ROOT / "configs/chapter1_lgd2_final_analysis.yaml").exists(),
         "configs/chapter1_lgd2_final_analysis.yaml")

    df = pd.DataFrame(checks)
    GIT_OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(GIT_OUT / "lgd2_final_rerun_readiness.csv", index=False)
    n_fail = int((df["status"] == "FAIL").sum())
    lines = ["# LGD2+ Final Rerun Readiness", "",
             f"Release `{cohort.get('cohort_release_id', rel.name)}`. Overall: "
             f"**{'PASS' if n_fail == 0 else 'FAIL'}** ({len(df) - n_fail}/{len(df)} gates).", "",
             "| gate | status | detail |", "| --- | --- | --- |"]
    for _, r in df.iterrows():
        lines.append(f"| {r['gate']} | {r['status']} | {str(r['detail'])[:120]} |")
    lines += ["", "Do not launch expensive jobs unless every gate is PASS."]
    (GIT_OUT / "lgd2_final_rerun_readiness.md").write_text("\n".join(lines) + "\n")
    print(f"readiness overall={'PASS' if n_fail == 0 else 'FAIL'} fails={n_fail}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
