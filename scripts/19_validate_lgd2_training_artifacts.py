#!/usr/bin/env python
"""Validate a run's outer-test predictions + completeness manifest against the
analysis-ready artifact contract (Phase 5).

Importing this module requires no real data. All I/O happens in main().

Example:
    python scripts/19_validate_lgd2_training_artifacts.py \
        --predictions run/outer_test_predictions.csv \
        --manifest run/completeness_manifest.json \
        --expected-folds 5 \
        --out run/artifact_validation_report.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as a plain script without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from barrett.evaluation.output_contract import (  # noqa: E402
    validate_predictions,
    validate_run_completeness,
)


def run(predictions_path: str, manifest_path: str, expected_folds: int) -> list:
    import pandas as pd

    problems = []
    df = pd.read_csv(predictions_path)
    problems.extend(validate_predictions(df, expected_folds=expected_folds))

    with open(manifest_path) as fh:
        manifest = json.load(fh)
    problems.extend(validate_run_completeness(manifest))
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, help="outer-test predictions CSV")
    parser.add_argument("--manifest", required=True, help="completeness manifest JSON")
    parser.add_argument("--expected-folds", type=int, default=5)
    parser.add_argument("--out", default=None, help="optional report output path")
    args = parser.parse_args(argv)

    problems = run(args.predictions, args.manifest, args.expected_folds)
    status = "PASS" if not problems else "FAIL"

    lines = [f"{status}", f"problems: {len(problems)}"]
    lines += [f"  - {p}" for p in problems]
    report = "\n".join(lines)

    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
