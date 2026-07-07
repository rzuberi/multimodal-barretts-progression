from __future__ import annotations

from pathlib import Path
from typing import Any


def _simple_yaml_config(text: str) -> dict[str, Any]:
    config: dict[str, Any] = {"remaps": [], "candidate_roots": []}
    section = ""
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped == "remaps:":
            section = "remaps"
            continue
        if stripped == "candidate_roots:":
            if current:
                config["remaps"].append(current)
                current = None
            section = "candidate_roots"
            continue
        if section == "remaps":
            if stripped.startswith("- "):
                if current:
                    config["remaps"].append(current)
                current = {}
                rest = stripped[2:].strip()
                if rest.startswith("from:"):
                    current["from"] = _clean_yaml_value(rest.split(":", 1)[1])
            elif ":" in stripped and current is not None:
                key, val = stripped.split(":", 1)
                current[key.strip()] = _clean_yaml_value(val)
        elif section == "candidate_roots":
            if stripped.startswith("- "):
                config["candidate_roots"].append(_clean_yaml_value(stripped[2:]))
    if current:
        config["remaps"].append(current)
    return config


def _clean_yaml_value(value: str) -> str:
    s = value.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def load_path_remap_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"remaps": [], "candidate_roots": []}
    text = p.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text) or {}
    except Exception:
        loaded = _simple_yaml_config(text)
    return {
        "remaps": list(loaded.get("remaps") or []),
        "candidate_roots": list(loaded.get("candidate_roots") or []),
    }


def apply_path_remaps(path: str | Path, remap_rules: list[dict[str, str]] | None = None) -> list[tuple[str, str]]:
    s = str(path)
    if not s or s.lower() == "nan":
        return []
    out: list[tuple[str, str]] = [(s, "original")]
    for rule in remap_rules or []:
        src = str(rule.get("from", ""))
        dst = str(rule.get("to", ""))
        if src and s.startswith(src):
            out.append((dst + s[len(src) :], f"{src}->{dst}"))
    return out


def _candidate_paths(path: str | Path, candidate_roots: list[str | Path] | None = None) -> list[tuple[str, str]]:
    s = str(path)
    if not s or s.lower() == "nan":
        return []
    out: list[tuple[str, str]] = []
    p = Path(s)
    if not p.is_absolute():
        out.append((s, "relative"))
        for root in candidate_roots or []:
            out.append((str(Path(root) / s), f"candidate_root:{root}"))
    return out


def resolve_existing_path(
    path: str | Path,
    remap_rules: list[dict[str, str]] | None = None,
    candidate_roots: list[str | Path] | None = None,
) -> tuple[str, bool, str]:
    checked: list[tuple[str, str]] = []
    checked.extend(apply_path_remaps(path, remap_rules))
    checked.extend(_candidate_paths(path, candidate_roots))
    seen = set()
    for candidate, rule in checked:
        if candidate in seen:
            continue
        seen.add(candidate)
        if Path(candidate).exists():
            return candidate, True, rule
    if checked:
        return checked[0][0], False, checked[0][1]
    return str(path), False, "empty"


def path_exists_after_remap(
    path: str | Path,
    remap_rules: list[dict[str, str]] | None = None,
    candidate_roots: list[str | Path] | None = None,
) -> bool:
    return resolve_existing_path(path, remap_rules, candidate_roots)[1]


def redact_or_basename(path: str | Path) -> str:
    s = str(path)
    if not s or s.lower() == "nan":
        return ""
    markers = [
        "foundation_grid_runs/",
        "foundation_outputs/",
        "SWGCohort/",
        "analysis/",
        "data/",
    ]
    for marker in markers:
        if marker in s:
            return marker + s.split(marker, 1)[1]
    return Path(s).name
