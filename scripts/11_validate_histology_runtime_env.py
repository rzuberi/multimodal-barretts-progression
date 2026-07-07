#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import platform
from pathlib import Path
import sys
from typing import Callable

import pandas as pd


REQUIRED_DEPENDENCIES = ["torch", "numpy", "pandas", "PIL", "openslide"]


def _get_version(module: object, name: str) -> str:
    if name == "PIL":
        try:
            from PIL import Image

            return str(getattr(Image, "__version__", ""))
        except Exception:
            return str(getattr(module, "__version__", ""))
    if name == "openslide":
        return str(getattr(module, "__version__", ""))
    return str(getattr(module, "__version__", ""))


def check_dependency(name: str, importer: Callable[[str], object] = importlib.import_module) -> dict[str, object]:
    try:
        module = importer(name)
        version = _get_version(module, name)
        return {
            "dependency": name,
            "required": True,
            "import_success": True,
            "version": version,
            "error": "",
            "status": "PASS",
        }
    except Exception as exc:
        return {
            "dependency": name,
            "required": True,
            "import_success": False,
            "version": "",
            "error": f"{type(exc).__name__}: {exc}",
            "status": "FAIL",
        }


def run_import_checks(importer: Callable[[str], object] = importlib.import_module) -> pd.DataFrame:
    return pd.DataFrame([check_dependency(dep, importer=importer) for dep in REQUIRED_DEPENDENCIES])


def collect_runtime_context(checks: pd.DataFrame) -> dict[str, object]:
    ctx: dict[str, object] = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "sys_path_head": sys.path[:5],
        "suitable": bool(checks["import_success"].all()),
        "torch_cuda_available": "",
        "torch_version": "",
        "openslide_version": "",
    }
    if bool(checks.loc[checks["dependency"] == "torch", "import_success"].any()):
        try:
            import torch

            ctx["torch_version"] = str(getattr(torch, "__version__", ""))
            ctx["torch_cuda_available"] = str(bool(torch.cuda.is_available()))
        except Exception as exc:
            ctx["torch_cuda_available"] = f"error: {type(exc).__name__}: {exc}"
    if bool(checks.loc[checks["dependency"] == "openslide", "import_success"].any()):
        try:
            import openslide

            ctx["openslide_version"] = str(getattr(openslide, "__version__", ""))
        except Exception:
            pass
    return ctx


def markdown_summary(checks: pd.DataFrame, context: dict[str, object]) -> str:
    missing = checks[~checks["import_success"].astype(bool)]["dependency"].astype(str).tolist()
    lines = [
        "# LGD2+ Histology Runtime Environment Audit",
        "",
        f"- Pass: `{bool(context['suitable'])}`",
        f"- Python executable: `{context['python_executable']}`",
        f"- Python version: `{context['python_version']}`",
        f"- Torch version: `{context.get('torch_version', '')}`",
        f"- Torch CUDA available: `{context.get('torch_cuda_available', '')}`",
        f"- OpenSlide Python version: `{context.get('openslide_version', '')}`",
        "",
        "## sys.path Head",
        "",
    ]
    for entry in context.get("sys_path_head", []):
        lines.append(f"- `{entry}`")
    lines.extend(["", "## Dependencies", "", "| dependency | required | import_success | version | status | error |", "| --- | --- | --- | --- | --- | --- |"])
    for _, row in checks.iterrows():
        vals = [
            str(row["dependency"]),
            str(row["required"]),
            str(row["import_success"]),
            str(row["version"]),
            str(row["status"]),
            str(row["error"]).replace("|", "\\|"),
        ]
        lines.append("| " + " | ".join(vals) + " |")
    lines.extend(["", "## Recommendation", ""])
    if missing:
        lines.append(
            "Do not rerun WSI explainability from this environment. Missing imports: "
            + ", ".join(f"`{m}`" for m in missing)
            + "."
        )
    else:
        lines.append(
            "Runtime imports pass. Re-run path preflight, then attempt only `row_idx 0` before any second case or all-case run."
        )
    return "\n".join(lines) + "\n"


def warnings_markdown(checks: pd.DataFrame, context: dict[str, object]) -> str:
    lines = ["# LGD2+ Histology Runtime Environment Warnings", ""]
    failed = checks[~checks["import_success"].astype(bool)]
    if failed.empty:
        lines.append("- No missing required imports.")
    else:
        for _, row in failed.iterrows():
            lines.append(f"- `{row['dependency']}` failed: {row['error']}")
    if not bool(context["suitable"]):
        lines.append("- Do not rerun `run_wsi_explainability_case.py` until this audit passes.")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate imports needed by LGD2+ WSI explainability runtime.")
    p.add_argument("--output-dir", default="reports/thesis_ch1")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = run_import_checks()
    context = collect_runtime_context(checks)
    checks.to_csv(out_dir / "lgd2_histology_runtime_env_audit.csv", index=False)
    (out_dir / "lgd2_histology_runtime_env_audit.md").write_text(markdown_summary(checks, context), encoding="utf-8")
    (out_dir / "lgd2_histology_runtime_env_warnings.md").write_text(warnings_markdown(checks, context), encoding="utf-8")
    print(f"runtime_env_pass={bool(context['suitable'])} python={sys.executable}")


if __name__ == "__main__":
    main()
