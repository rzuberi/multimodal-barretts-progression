"""Gated attention MIL used by the developmental UNI2 baseline."""

from __future__ import annotations

from typing import Iterable

import torch
from torch import nn


class AttentionMIL(nn.Module):
    def __init__(
        self,
        in_dim: int,
        hidden_dim: int = 256,
        attn_dim: int = 128,
        dropout: float = 0.1,
        out_dim: int = 1,
    ) -> None:
        super().__init__()
        self.embed = nn.Sequential(nn.Linear(in_dim, hidden_dim), nn.ReLU(inplace=True), nn.Dropout(dropout))
        self.attn_a = nn.Linear(hidden_dim, attn_dim)
        self.attn_b = nn.Linear(hidden_dim, attn_dim)
        self.attn_c = nn.Linear(attn_dim, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, out_dim),
        )

    def attention_weights(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        return torch.softmax(score, dim=0)

    def forward_bag(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        weight = torch.softmax(score, dim=0)
        return self.classifier(torch.sum(h * weight.unsqueeze(-1), dim=0))

    def forward(self, bags: Iterable[torch.Tensor]) -> torch.Tensor:
        return torch.stack([self.forward_bag(bag) for bag in bags], dim=0)
