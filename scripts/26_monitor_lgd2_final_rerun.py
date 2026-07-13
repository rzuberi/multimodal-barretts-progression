#!/usr/bin/env python
"""Report fold completion state for an external LGD2+ rerun root."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


FAMILIES = (
    "cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.output_root).resolve()
    rows = []
    for family in FAMILIES:
        for fold in range(1, 6):
            directory = root / family / f"fold{fold}"
            completion = directory / "fold_completion.json"
            status = "NOT_STARTED"
            detail = ""
            if completion.exists():
                try:
                    payload = json.loads(completion.read_text(encoding="utf-8"))
                    status = str(payload.get("status", "UNKNOWN"))
                    detail = str(payload.get("selected_configuration_id", ""))
                except json.JSONDecodeError as exc:
                    status, detail = "INVALID", str(exc)
            elif directory.exists() and any(directory.iterdir()):
                status = "PARTIAL"
            rows.append((family, fold, status, detail))
    print("family\tfold\tstatus\tdetail")
    for row in rows:
        print("\t".join(map(str, row)))
    try:
        queue = subprocess.run(
            ["squeue", "-u", str(Path.home().name), "-h", "-o", "%i|%P|%j|%T|%M|%R"],
            check=False, capture_output=True, text=True,
        ).stdout.strip()
        if queue:
            print("\nactive_jobs")
            print(queue)
    except OSError:
        pass
    complete = sum(status == "PASS" for _, _, status, _ in rows)
    print(f"\ncomplete={complete}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
