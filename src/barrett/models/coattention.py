"""CNV-conditioned attention pooling over histology tile embeddings."""

from __future__ import annotations

from typing import Iterable

import torch
from torch import nn


class CoAttentionABMILCNV(nn.Module):
    """Use the CNV embedding as a query over histology tile embeddings."""

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
        self.img_embed = nn.Sequential(
            nn.Linear(image_dim, img_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )
        self.key_proj = nn.Linear(img_hidden, attn_dim)
        self.value_proj = nn.Linear(img_hidden, img_hidden)
        self.cnv_embed = nn.Sequential(
            nn.Linear(cnv_dim, cnv_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(cnv_hidden, cnv_hidden),
            nn.ReLU(inplace=True),
        )
        self.query_proj = nn.Linear(cnv_hidden, attn_dim)
        self.fusion = nn.Sequential(
            nn.Linear(img_hidden + cnv_hidden, fusion_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden, out_dim),
        )

    def attention_weights(self, bag: torch.Tensor, cnv_embedding: torch.Tensor) -> torch.Tensor:
        h = self.img_embed(bag)
        keys = self.key_proj(h)
        query = self.query_proj(cnv_embedding)
        scores = torch.matmul(keys, query.unsqueeze(-1)).squeeze(-1) / (keys.shape[1] ** 0.5)
        return torch.softmax(scores, dim=0)

    def _coattention_pool(self, bag: torch.Tensor, query: torch.Tensor) -> torch.Tensor:
        h = self.img_embed(bag)
        keys = self.key_proj(h)
        values = self.value_proj(h)
        scores = torch.matmul(keys, query.unsqueeze(-1)).squeeze(-1) / (keys.shape[1] ** 0.5)
        weights = torch.softmax(scores, dim=0)
        return torch.sum(values * weights.unsqueeze(-1), dim=0)

    def forward(self, bags: Iterable[torch.Tensor], cnv: torch.Tensor) -> torch.Tensor:
        cnv_embedding = self.cnv_embed(cnv)
        queries = self.query_proj(cnv_embedding)
        image_embedding = torch.stack(
            [self._coattention_pool(bag, query) for bag, query in zip(bags, queries)],
            dim=0,
        )
        return self.fusion(torch.cat([image_embedding, cnv_embedding], dim=1))
