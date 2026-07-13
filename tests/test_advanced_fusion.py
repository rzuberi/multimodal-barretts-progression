from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from barrett.models.advanced_fusion import (
    CNVTokenCrossAttentionFusion,
    FoundationEnsembleFusion,
    HierarchicalPatientFusion,
    LowRankBilinearFusion,
    MultiTaskTemporalFusion,
    OptimalTransportFusion,
    ReliabilityGatedResidualFusion,
)
from barrett.training.advanced import AdvancedFeatureStore, chromosome_group_ids, fit_advanced


def bags(dim: int = 8) -> list[torch.Tensor]:
    return [torch.randn(6, dim), torch.randn(4, dim)]


def test_row_level_advanced_models_return_binary_logits() -> None:
    cnv = torch.randn(2, 6)
    groups = [0, 0, 1, 1, 2, 2]
    models = [
        ReliabilityGatedResidualFusion(8, 6, hidden=8, dropout=0.0),
        LowRankBilinearFusion(8, 6, hidden=8, rank=4, dropout=0.0),
        CNVTokenCrossAttentionFusion(8, groups, token_dim=8, n_heads=2, dropout=0.0),
        MultiTaskTemporalFusion(8, 6, hidden=8, dropout=0.0),
        OptimalTransportFusion(8, groups, token_dim=8, epsilon=0.2, sinkhorn_iters=3, dropout=0.0),
    ]
    for model in models:
        output = model(bags(), cnv)
        assert output["logits"].shape == (2,)
        assert torch.isfinite(output["logits"]).all()


def test_foundation_ensemble_returns_expert_outputs() -> None:
    model = FoundationEnsembleFusion({"gigapath": 6, "uni2": 8, "virchow2": 10}, 5, hidden=8, dropout=0.0)
    output = model({"gigapath": bags(6), "uni2": bags(8), "virchow2": bags(10)}, torch.randn(2, 5))
    assert output["logits"].shape == (2,)
    assert output["aux_logits"].shape == (2, 4)
    torch.testing.assert_close(output["gate"].sum(1), torch.ones(2))


def test_hierarchical_model_consumes_slide_biopsy_patient_structure() -> None:
    model = HierarchicalPatientFusion(8, 6, hidden=8, dropout=0.0)
    patients = [{
        "bags": bags(8), "cnv": torch.randn(2, 6), "biopsy_ids": ["B1", "B2"],
        "relative_days": torch.tensor([0.0, 120.0]),
    }]
    output = model(patients)
    assert output["logits"].shape == (1,)


def test_chromosome_groups_merge_windows_and_arms() -> None:
    ids = chromosome_group_ids(["chr1:1-5000000", "chr1p", "chr2q", "cx"])
    assert ids[0] == ids[1]
    assert len(set(ids)) == 3


def test_advanced_fit_runs_on_toy_data(tmp_path) -> None:
    sample_ids = [str(i) for i in range(8)]
    paths = {}
    for sample_id in sample_ids:
        path = tmp_path / f"{sample_id}.npz"
        np.savez(path, embeddings=np.full((4, 8), int(sample_id) / 10, dtype=np.float32))
        paths[sample_id] = str(path)
    index = pd.DataFrame({"sample_id": sample_ids, "npz_path": [paths[value] for value in sample_ids]})
    cnv = pd.DataFrame({"sample_id": sample_ids, "chr1:1-5": np.arange(8), "chr2p": np.arange(8) / 2})
    store = AdvancedFeatureStore({"uni2": index}, cnv, ["chr1:1-5", "chr2p"])
    frame = pd.DataFrame({
        "sample_id": sample_ids, "patient_id": [f"P{i}" for i in range(8)],
        "biopsy_id": [f"B{i}" for i in range(8)], "Date": pd.date_range("2020-01-01", periods=8),
        "DaysFromCurrentToEvent": [10, np.nan] * 4, "y_progressor": [1, 0] * 4,
    })
    fit = fit_advanced(
        "reliability_gated_fusion", frame.iloc[:6], frame.iloc[6:], store,
        {"hidden": 8, "dropout": 0.0, "residual_scale": 0.0, "batch_size": 2,
         "max_epochs": 1, "patience": 1}, torch.device("cpu"), seed=3,
    )
    assert fit.validation_predictions is not None
    assert len(fit.validation_predictions) == 2
