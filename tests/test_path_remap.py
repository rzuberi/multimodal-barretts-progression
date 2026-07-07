from pathlib import Path
from tempfile import TemporaryDirectory

from barrett.utils.path_remap import (
    apply_path_remaps,
    load_path_remap_config,
    path_exists_after_remap,
    redact_or_basename,
    resolve_existing_path,
)


def test_simple_prefix_remap():
    rules = [{"from": "/old/", "to": "/new/"}]
    assert apply_path_remaps("/old/a/file.txt", rules)[1] == ("/new/a/file.txt", "/old/->/new/")


def test_multiple_remap_rules_use_first_existing():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "b" / "file.txt"
        existing.parent.mkdir()
        existing.write_text("x", encoding="utf-8")
        rules = [
            {"from": "/legacy/", "to": str(root / "a") + "/"},
            {"from": "/legacy/", "to": str(root / "b") + "/"},
        ]
        resolved, exists, rule = resolve_existing_path("/legacy/file.txt", rules)
    assert exists is True
    assert resolved.endswith("/b/file.txt")
    assert rule.endswith("->" + str(root / "b") + "/")


def test_missing_path_returns_status_false():
    resolved, exists, rule = resolve_existing_path("/missing/file.txt", [])
    assert exists is False
    assert resolved == "/missing/file.txt"
    assert rule == "original"


def test_basename_redaction():
    assert redact_or_basename("/private/root/slide.ndpi") == "slide.ndpi"
    assert redact_or_basename("/x/foundation_outputs/uni2/file.npz") == "foundation_outputs/uni2/file.npz"


def test_candidate_root_resolves_relative_path():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        p = root / "sub" / "file.txt"
        p.parent.mkdir()
        p.write_text("x", encoding="utf-8")
        assert path_exists_after_remap("sub/file.txt", candidate_roots=[root]) is True


def test_config_loading_simple_yaml():
    with TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "paths.yaml"
        cfg.write_text(
            """
remaps:
  - from: "/old/"
    to: "/new/"
candidate_roots:
  - "/root"
""",
            encoding="utf-8",
        )
        loaded = load_path_remap_config(cfg)
    assert loaded["remaps"][0]["from"] == "/old/"
    assert loaded["candidate_roots"] == ["/root"]
