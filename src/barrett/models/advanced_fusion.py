"""Compact experimental fusion architectures for the strict LGD2+ comparison."""

from __future__ import annotations

import math
from typing import Iterable

import torch
from torch import nn


class GatedBagEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden: int, attn_dim: int, dropout: float) -> None:
        super().__init__()
        self.embed = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.attn_a = nn.Linear(hidden, attn_dim)
        self.attn_b = nn.Linear(hidden, attn_dim)
        self.attn_c = nn.Linear(attn_dim, 1)

    def forward_bag(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        return torch.sum(h * torch.softmax(score, dim=0).unsqueeze(-1), dim=0)

    def forward(self, bags: Iterable[torch.Tensor]) -> torch.Tensor:
        return torch.stack([self.forward_bag(bag) for bag in bags], dim=0)


class CNVEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden: int, dropout: float) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.network(values)


class ReliabilityGatedResidualFusion(nn.Module):
    """Convex unimodal logit mixture with a bounded interaction residual."""

    def __init__(self, image_dim: int, cnv_dim: int, hidden: int = 128, dropout: float = 0.2,
                 residual_scale: float = 0.1) -> None:
        super().__init__()
        self.image = GatedBagEncoder(image_dim, hidden, hidden // 2, dropout)
        self.cnv = CNVEncoder(cnv_dim, hidden, dropout)
        self.image_head = nn.Linear(hidden, 1)
        self.cnv_head = nn.Linear(hidden, 1)
        self.gate = nn.Sequential(nn.Linear(hidden * 2 + 2, hidden // 2), nn.ReLU(), nn.Linear(hidden // 2, 1))
        self.interaction = nn.Sequential(nn.Linear(hidden * 2, hidden // 2), nn.Tanh(), nn.Linear(hidden // 2, 1))
        self.residual_scale = float(residual_scale)

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        image = self.image(bags)
        molecular = self.cnv(cnv)
        image_logit = self.image_head(image).squeeze(-1)
        cnv_logit = self.cnv_head(molecular).squeeze(-1)
        gate = torch.sigmoid(self.gate(torch.cat([image, molecular, image_logit[:, None], cnv_logit[:, None]], 1))).squeeze(-1)
        base = gate * cnv_logit + (1.0 - gate) * image_logit
        residual = self.residual_scale * self.interaction(torch.cat([image, molecular], 1)).squeeze(-1)
        return {"logits": base + residual, "aux_logits": torch.stack([image_logit, cnv_logit], dim=1), "gate": gate}


class LowRankBilinearFusion(nn.Module):
    def __init__(self, image_dim: int, cnv_dim: int, hidden: int = 128, rank: int = 16,
                 dropout: float = 0.2) -> None:
        super().__init__()
        self.image = GatedBagEncoder(image_dim, hidden, hidden // 2, dropout)
        self.cnv = CNVEncoder(cnv_dim, hidden, dropout)
        self.image_factor = nn.Linear(hidden, rank)
        self.cnv_factor = nn.Linear(hidden, rank)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2 + rank, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1)
        )

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        image = self.image(bags)
        molecular = self.cnv(cnv)
        interaction = self.image_factor(image) * self.cnv_factor(molecular)
        return {"logits": self.head(torch.cat([image, molecular, interaction], 1)).squeeze(-1)}


class ChromosomeTokenizer(nn.Module):
    def __init__(self, group_ids: list[int], token_dim: int) -> None:
        super().__init__()
        groups = torch.tensor(group_ids, dtype=torch.long)
        self.register_buffer("group_ids", groups)
        self.n_groups = int(groups.max().item()) + 1
        self.value = nn.Linear(1, token_dim)
        self.position = nn.Parameter(torch.randn(self.n_groups, token_dim) * 0.02)

    def forward(self, cnv: torch.Tensor) -> torch.Tensor:
        values = self.value(cnv.unsqueeze(-1))
        tokens = []
        for group in range(self.n_groups):
            tokens.append(values[:, self.group_ids.eq(group)].mean(dim=1))
        return torch.stack(tokens, dim=1) + self.position.unsqueeze(0)


class CNVTokenCrossAttentionFusion(nn.Module):
    def __init__(self, image_dim: int, cnv_group_ids: list[int], token_dim: int = 64,
                 n_heads: int = 4, dropout: float = 0.2) -> None:
        super().__init__()
        self.image_proj = nn.Linear(image_dim, token_dim)
        self.cnv_tokens = ChromosomeTokenizer(cnv_group_ids, token_dim)
        self.cnv_to_image = nn.MultiheadAttention(token_dim, n_heads, dropout=dropout, batch_first=True)
        self.image_to_cnv = nn.MultiheadAttention(token_dim, n_heads, dropout=dropout, batch_first=True)
        self.head = nn.Sequential(nn.Linear(token_dim * 2, token_dim), nn.ReLU(), nn.Dropout(dropout), nn.Linear(token_dim, 1))

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        cnv_tokens = self.cnv_tokens(cnv)
        pooled = []
        for index, bag in enumerate(bags):
            image = self.image_proj(bag).unsqueeze(0)
            molecular = cnv_tokens[index:index + 1]
            c_context, _ = self.cnv_to_image(molecular, image, image, need_weights=False)
            i_context, _ = self.image_to_cnv(image, molecular, molecular, need_weights=False)
            pooled.append(torch.cat([c_context.mean(1), i_context.mean(1)], dim=1).squeeze(0))
        return {"logits": self.head(torch.stack(pooled)).squeeze(-1)}


class MultiTaskTemporalFusion(nn.Module):
    """Fusion model regularised by unimodal progression and event-time heads."""

    def __init__(self, image_dim: int, cnv_dim: int, hidden: int = 128, dropout: float = 0.2) -> None:
        super().__init__()
        self.image = GatedBagEncoder(image_dim, hidden, hidden // 2, dropout)
        self.cnv = CNVEncoder(cnv_dim, hidden, dropout)
        self.image_head = nn.Linear(hidden, 1)
        self.cnv_head = nn.Linear(hidden, 1)
        self.shared = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.main_head = nn.Linear(hidden, 1)
        self.time_head = nn.Linear(hidden, 1)

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        image = self.image(bags)
        molecular = self.cnv(cnv)
        shared = self.shared(torch.cat([image, molecular], 1))
        return {
            "logits": self.main_head(shared).squeeze(-1),
            "aux_logits": torch.cat([self.image_head(image), self.cnv_head(molecular)], dim=1),
            "time_prediction": self.time_head(shared).squeeze(-1),
        }


class OptimalTransportFusion(nn.Module):
    """Entropy-regularised transport between chromosome and histology tokens."""

    def __init__(self, image_dim: int, cnv_group_ids: list[int], token_dim: int = 64,
                 epsilon: float = 0.1, sinkhorn_iters: int = 8, dropout: float = 0.2) -> None:
        super().__init__()
        self.image_proj = nn.Linear(image_dim, token_dim)
        self.cnv_tokens = ChromosomeTokenizer(cnv_group_ids, token_dim)
        self.epsilon = float(epsilon)
        self.sinkhorn_iters = int(sinkhorn_iters)
        self.head = nn.Sequential(nn.Linear(token_dim * 3, token_dim), nn.ReLU(), nn.Dropout(dropout), nn.Linear(token_dim, 1))

    def _transport(self, image: torch.Tensor, molecular: torch.Tensor) -> torch.Tensor:
        image = torch.nn.functional.normalize(image, dim=1)
        molecular = torch.nn.functional.normalize(molecular, dim=1)
        kernel = torch.exp(-(1.0 - image @ molecular.T) / self.epsilon).clamp_min(1e-8)
        a = torch.full((image.shape[0],), 1.0 / image.shape[0], device=image.device)
        b = torch.full((molecular.shape[0],), 1.0 / molecular.shape[0], device=image.device)
        u, v = torch.ones_like(a), torch.ones_like(b)
        for _ in range(self.sinkhorn_iters):
            u = a / (kernel @ v).clamp_min(1e-8)
            v = b / (kernel.T @ u).clamp_min(1e-8)
        plan = u[:, None] * kernel * v[None, :]
        interaction = (plan[:, :, None] * image[:, None, :] * molecular[None, :, :]).sum((0, 1))
        return torch.cat([image.mean(0), molecular.mean(0), interaction], dim=0)

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        cnv_tokens = self.cnv_tokens(cnv)
        rows = [self._transport(self.image_proj(bag), cnv_tokens[index]) for index, bag in enumerate(bags)]
        return {"logits": self.head(torch.stack(rows)).squeeze(-1)}


class FoundationEnsembleFusion(nn.Module):
    def __init__(self, image_dims: dict[str, int], cnv_dim: int, hidden: int = 128,
                 dropout: float = 0.2, learned_gate: bool = True) -> None:
        super().__init__()
        self.names = tuple(sorted(image_dims))
        self.encoders = nn.ModuleDict({
            name: GatedBagEncoder(image_dims[name], hidden, hidden // 2, dropout) for name in self.names
        })
        self.cnv = CNVEncoder(cnv_dim, hidden, dropout)
        self.expert_heads = nn.ModuleList([nn.Linear(hidden, 1) for _ in range(len(self.names) + 1)])
        self.learned_gate = bool(learned_gate)
        self.gate = nn.Sequential(nn.Linear(hidden * (len(self.names) + 1), hidden), nn.ReLU(), nn.Linear(hidden, len(self.names) + 1))

    def forward(self, foundation_bags: dict[str, Iterable[torch.Tensor]], cnv: torch.Tensor) -> dict[str, torch.Tensor]:
        embeddings = [self.encoders[name](foundation_bags[name]) for name in self.names]
        embeddings.append(self.cnv(cnv))
        expert_logits = torch.cat([head(value) for head, value in zip(self.expert_heads, embeddings)], dim=1)
        if self.learned_gate:
            weights = torch.softmax(self.gate(torch.cat(embeddings, dim=1)), dim=1)
        else:
            weights = torch.full_like(expert_logits, 1.0 / expert_logits.shape[1])
        return {"logits": (weights * expert_logits).sum(dim=1), "aux_logits": expert_logits, "gate": weights}


class HierarchicalPatientFusion(nn.Module):
    """Slides to biopsies to patient, with safe relative collection-time encoding."""

    def __init__(self, image_dim: int, cnv_dim: int, hidden: int = 128, dropout: float = 0.2) -> None:
        super().__init__()
        self.image = GatedBagEncoder(image_dim, hidden, hidden // 2, dropout)
        self.cnv = CNVEncoder(cnv_dim, hidden, dropout)
        self.row = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.time = nn.Sequential(nn.Linear(1, hidden), nn.Tanh())
        self.attention = nn.Sequential(nn.Linear(hidden, hidden // 2), nn.Tanh(), nn.Linear(hidden // 2, 1))
        self.head = nn.Linear(hidden, 1)

    def forward(self, patients: list[dict[str, object]]) -> dict[str, torch.Tensor]:
        patient_embeddings = []
        for patient in patients:
            rows = self.row(torch.cat([self.image(patient["bags"]), self.cnv(patient["cnv"])], dim=1))
            biopsy_vectors = []
            biopsy_ids = patient["biopsy_ids"]
            relative_days = patient["relative_days"]
            for biopsy in dict.fromkeys(biopsy_ids):
                indices = [i for i, value in enumerate(biopsy_ids) if value == biopsy]
                vector = rows[indices].mean(dim=0)
                day = relative_days[indices].mean().reshape(1, 1)
                biopsy_vectors.append(vector + self.time(torch.log1p(day) / math.log(3651.0)).squeeze(0))
            biopsies = torch.stack(biopsy_vectors)
            weights = torch.softmax(self.attention(biopsies).squeeze(-1), dim=0)
            patient_embeddings.append(torch.sum(biopsies * weights[:, None], dim=0))
        return {"logits": self.head(torch.stack(patient_embeddings)).squeeze(-1)}
