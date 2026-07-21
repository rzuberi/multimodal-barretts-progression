"""End-to-end Mixture-of-Experts over image / CNV / multimodal experts.

Three experts each emit a logit for the binary endpoint; a gating network emits
per-sample softmax weights over the experts and the final logit is the weighted
sum. Trained jointly from scratch (see ``moe_training.fit_moe``) with a
load-balancing auxiliary loss. The image experts reuse the exact gated-attention
MIL pooling of ``barrett.models.AttentionMIL`` so the image branch is comparable
to the frozen ABMIL baseline.

Deliberately small (low hidden dims, high dropout, load-balancing) because the
cohorts are ~150 patients / ~50 progressors — an over-parameterised temporal /
gated model does not pay for itself at this n (Chapter-2 finding).
"""

from __future__ import annotations

from typing import Iterable

import torch
from torch import nn


class GatedAttentionPool(nn.Module):
    """Gated-attention MIL pooling; mirrors barrett.models.AttentionMIL."""

    def __init__(self, in_dim: int, hidden_dim: int, attn_dim: int, dropout: float) -> None:
        super().__init__()
        self.embed = nn.Sequential(nn.Linear(in_dim, hidden_dim), nn.ReLU(inplace=True), nn.Dropout(dropout))
        self.attn_a = nn.Linear(hidden_dim, attn_dim)
        self.attn_b = nn.Linear(hidden_dim, attn_dim)
        self.attn_c = nn.Linear(attn_dim, 1)

    def attention_weights(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        return torch.softmax(score, dim=0)

    def forward_bag(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        weight = torch.softmax(score, dim=0)
        return torch.sum(h * weight.unsqueeze(-1), dim=0)

    def forward(self, bags: Iterable[torch.Tensor]) -> torch.Tensor:
        return torch.stack([self.forward_bag(bag) for bag in bags], dim=0)


EXPERT_NAMES = ("image", "cnv", "multimodal")


class MixtureOfExperts(nn.Module):
    """Gated mixture of an image-only, a CNV-only, and a multimodal expert."""

    def __init__(
        self,
        image_dim: int,
        cnv_dim: int,
        img_hidden: int = 128,
        cnv_hidden: int = 64,
        attn_dim: int = 128,
        fusion_hidden: int = 128,
        dropout: float = 0.3,
        gate_hidden: int = 32,
        gate_temperature: float = 1.0,
        out_dim: int = 1,
    ) -> None:
        super().__init__()
        if out_dim != 1:
            raise ValueError("MixtureOfExperts currently supports binary output only")
        self.n_experts = len(EXPERT_NAMES)
        self.gate_temperature = float(gate_temperature)

        # Image expert.
        self.img_pool = GatedAttentionPool(image_dim, img_hidden, attn_dim, dropout)
        self.image_head = nn.Sequential(
            nn.Linear(img_hidden, img_hidden), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(img_hidden, 1),
        )
        # CNV expert.
        self.cnv_branch = nn.Sequential(
            nn.Linear(cnv_dim, cnv_hidden), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(cnv_hidden, cnv_hidden), nn.ReLU(inplace=True),
        )
        self.cnv_head = nn.Linear(cnv_hidden, 1)
        # Multimodal expert (independent image pool + CNV branch, then fuse).
        self.mm_img_pool = GatedAttentionPool(image_dim, img_hidden, attn_dim, dropout)
        self.mm_cnv_branch = nn.Sequential(
            nn.Linear(cnv_dim, cnv_hidden), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(cnv_hidden, cnv_hidden), nn.ReLU(inplace=True),
        )
        self.mm_fusion = nn.Sequential(
            nn.Linear(img_hidden + cnv_hidden, fusion_hidden), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(fusion_hidden, 1),
        )
        # Gate: reuses the image-expert pooled feature and CNV-expert feature.
        self.gate = nn.Sequential(
            nn.Linear(img_hidden + cnv_hidden, gate_hidden), nn.ReLU(inplace=True),
            nn.Dropout(dropout), nn.Linear(gate_hidden, self.n_experts),
        )

    def forward_full(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor):
        """Return (final_logit, gate_weights[B,3], expert_logits[B,3])."""
        img_feat = self.img_pool(bags)
        logit_img = self.image_head(img_feat).squeeze(-1)
        cnv_feat = self.cnv_branch(cnv)
        logit_cnv = self.cnv_head(cnv_feat).squeeze(-1)
        mm_img = self.mm_img_pool(bags)
        mm_cnv = self.mm_cnv_branch(cnv)
        logit_mm = self.mm_fusion(torch.cat([mm_img, mm_cnv], dim=1)).squeeze(-1)
        expert_logits = torch.stack([logit_img, logit_cnv, logit_mm], dim=1)

        gate_in = torch.cat([img_feat, cnv_feat], dim=1)
        gate_logits = self.gate(gate_in) / self.gate_temperature
        gate_weights = torch.softmax(gate_logits, dim=1)
        final_logit = (gate_weights * expert_logits).sum(dim=1)
        return final_logit, gate_weights, expert_logits

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> torch.Tensor:
        final_logit, _, _ = self.forward_full(bags, cnv)
        return final_logit


def load_balance_loss(gate_weights: torch.Tensor) -> torch.Tensor:
    """Encourage balanced expert usage across a batch (min at uniform routing)."""
    mean_prob = gate_weights.mean(dim=0)
    n_experts = gate_weights.shape[1]
    return n_experts * (mean_prob * mean_prob).sum()
