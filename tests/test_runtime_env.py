import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "11_validate_histology_runtime_env.py"
spec = importlib.util.spec_from_file_location("runtime_env", SCRIPT)
runtime_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_env)


def test_missing_dependency_recorded_as_fail():
    def importer(name):
        raise ModuleNotFoundError("missing")

    row = runtime_env.check_dependency("torch", importer=importer)
    assert row["status"] == "FAIL"
    assert row["import_success"] is False
    assert "ModuleNotFoundError" in row["error"]


def test_successful_dependency_recorded_as_pass():
    def importer(name):
        return SimpleNamespace(__version__="1.2.3")

    row = runtime_env.check_dependency("numpy", importer=importer)
    assert row["status"] == "PASS"
    assert row["import_success"] is True
    assert row["version"] == "1.2.3"


def test_runtime_check_csv_columns():
    def importer(name):
        return SimpleNamespace(__version__="ok")

    df = runtime_env.run_import_checks(importer=importer)
    assert list(df.columns) == ["dependency", "required", "import_success", "version", "error", "status"]
    assert df["import_success"].all()


def test_markdown_summary_renders_failure():
    def importer(name):
        if name == "torch":
            raise ModuleNotFoundError("missing")
        return SimpleNamespace(__version__="ok")

    df = runtime_env.run_import_checks(importer=importer)
    context = {"suitable": False, "python_executable": "/x/python", "python_version": "3", "sys_path_head": []}
    md = runtime_env.markdown_summary(df, context)
    assert "Missing imports" in md
    assert "`torch`" in md
