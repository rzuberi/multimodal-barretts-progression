from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from barrett.evaluation.cnv_interpretation import interpretation_sentence, summarize_cnv_interpretation


def toy_cases():
    return pd.DataFrame(
        {
            "case_id": ["case_1"],
            "category": ["E_cnv_rescue"],
            "patient_id": ["P1"],
            "cnv_id": ["CNV1"],
            "true_label": [1],
            "CNV_probability": [0.8],
            "early_fusion_probability": [0.9],
            "prediction_correctness_cnv": ["correct"],
            "prediction_correctness_early_fusion": ["correct"],
        }
    )


def test_missing_external_output_warns():
    with TemporaryDirectory() as tmp:
        summary, warnings = summarize_cnv_interpretation(toy_cases(), Path(tmp) / "missing")
        assert warnings
        assert summary.loc[0, "top_cnv_windows"] == "MISSING"
        assert "Missing external" in summary.loc[0, "warnings"]


def test_loads_fake_top_window_and_gene_csv():
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        case_dir = tmp_path / "case_1"
        case_dir.mkdir()
        pd.DataFrame({"window": ["chr1:1-2", "chr2:3-4"], "importance": [0.9, 0.8]}).to_csv(
            case_dir / "case_1_top_windows.csv", index=False
        )
        pd.DataFrame({"gene": ["TP53", "CDKN2A"], "importance": [0.5, 0.4]}).to_csv(
            case_dir / "case_1_top_genes.csv", index=False
        )
        summary, warnings = summarize_cnv_interpretation(toy_cases(), tmp_path)
        assert not warnings
        assert "chr1" in summary.loc[0, "top_cnv_windows"]
        assert "TP53" in summary.loc[0, "top_genes"]
        assert "chr1:1-2" in summary.loc[0, "top_chromosomes_or_arms"]


def test_interpretation_sentence():
    row = pd.Series({"cnv_prediction_correct": "correct", "fusion_prediction_correct": "correct"})
    assert "CNV and fusion" in interpretation_sentence(row, has_outputs=True)
