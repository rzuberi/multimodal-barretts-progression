"""Mean-pooling early fusion used by the developmental headline model."""

from __future__ import annotations

from typing import Iterable

import torch
from torch import nn


class EarlyFusionMLP(nn.Module):
    def __init__(
        self,
        image_dim: int,
        cnv_dim: int,
        hidden_dim: int = 512,
        dropout: float = 0.2,
        out_dim: int = 1,
    ) -> None:
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(image_dim + cnv_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim),
        )

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> torch.Tensor:
        image = torch.stack([bag.mean(dim=0) for bag in bags], dim=0)
        return self.classifier(torch.cat([image, cnv], dim=1))
