"""Attention-MIL plus CNV-branch intermediate fusion."""

from __future__ import annotations

from typing import Iterable

import torch
from torch import nn


class IntermediateABMILCNV(nn.Module):
    def __init__(
        self,
        image_dim: int,
        cnv_dim: int,
        img_hidden: int = 256,
        cnv_hidden: int = 128,
        attn_dim: int = 128,
        fusion_hidden: int = 256,
        dropout: float = 0.2,
        out_dim: int = 1,
    ) -> None:
        super().__init__()
        self.img_embed = nn.Sequential(nn.Linear(image_dim, img_hidden), nn.ReLU(inplace=True), nn.Dropout(dropout))
        self.attn_a = nn.Linear(img_hidden, attn_dim)
        self.attn_b = nn.Linear(img_hidden, attn_dim)
        self.attn_c = nn.Linear(attn_dim, 1)
        self.cnv_branch = nn.Sequential(
            nn.Linear(cnv_dim, cnv_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(cnv_hidden, cnv_hidden),
            nn.ReLU(inplace=True),
        )
        self.fusion = nn.Sequential(
            nn.Linear(img_hidden + cnv_hidden, fusion_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden, out_dim),
        )

    def attention_weights(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.img_embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        return torch.softmax(score, dim=0)

    def _attend(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.img_embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        weight = torch.softmax(score, dim=0)
        return torch.sum(h * weight.unsqueeze(-1), dim=0)

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> torch.Tensor:
        image = torch.stack([self._attend(bag) for bag in bags], dim=0)
        return self.fusion(torch.cat([image, self.cnv_branch(cnv)], dim=1))
