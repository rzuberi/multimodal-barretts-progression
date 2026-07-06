import pandas as pd


def test_final_results_manifest_schema():
    expected = [
        "result_id",
        "status",
        "endpoint",
        "clinical_definition",
        "task",
        "analysis_set",
        "evaluation_design",
        "reporting_level",
        "model_family",
        "model_name",
        "fusion_type",
        "feature_model",
        "cohort_source",
        "external_result_path",
        "summary_file",
        "prediction_file",
        "has_patient_ids",
        "has_fold_ids",
        "metrics_existing",
        "metrics_missing",
        "needs_early_prediction_filter",
        "needs_patient_aggregation",
        "needs_interpretability_regeneration",
        "thesis_use",
        "planned_table_or_figure",
        "notes",
    ]
    allowed = {
        "FINAL_CANDIDATE",
        "NEEDS_RECOMPUTE",
        "SUPPLEMENTARY",
        "LEGACY",
        "EXPLORATORY",
        "MISSING",
        "REVIEW_MANUALLY",
    }
    df = pd.read_csv("docs/final_results_manifest.csv")
    assert list(df.columns) == expected
    assert not df["result_id"].duplicated().any()
    assert set(df["status"]) <= allowed

