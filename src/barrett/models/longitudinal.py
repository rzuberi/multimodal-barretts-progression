"""Landmarking longitudinal model for LGD2+ progression.

Each *landmark* is one biopsy ``t`` of a patient, together with the ordered
history of that patient's biopsies up to and including ``t`` (never the future).
The model encodes every biopsy in the history with a shared per-biopsy encoder
(attention-MIL over the UNI2 tile bag, concatenated with a CNV branch), then
aggregates the ordered per-biopsy embeddings with a temporal module (GRU by
default) and classifies the landmark against the Chapter 1 endpoint
``NextBiopsyProgression_LGD2plus``.

The prediction target and evaluation rows are identical to the frozen
single-timepoint baseline, so "does history help?" is a clean paired test on the
same rows and patient-disjoint folds. The single-timepoint case falls out as the
degenerate history of length one.

Architecture:
    per biopsy i:
        img_i  = attention_pool(img_embed(bag_i))         # [img_hidden]
        cnv_i  = cnv_branch(cnv_i)                          # [cnv_hidden]
        e_i    = [img_i ; cnv_i ; time_feat_i]              # per-biopsy embedding
    sequence e_1..e_t  ->  temporal aggregator  ->  h_t
        classifier(h_t) -> logit for landmark t

``time_feat_i`` is a scalar log-scaled inter-biopsy gap (days since previous
biopsy), which lets the model see the irregular spacing of the timeline.
"""

from __future__ import annotations

from typing import Sequence

import torch
from torch import nn


class BiopsyEncoder(nn.Module):
    """Shared per-biopsy encoder: gated attention-MIL image branch + CNV branch.

    Mirrors the encoder path of ``IntermediateABMILCNV`` so a longitudinal model
    trained from scratch is directly comparable to the single-timepoint fusion
    baseline. Produces one fixed-width embedding per biopsy.
    """

    def __init__(
        self,
        image_dim: int,
        cnv_dim: int,
        img_hidden: int = 256,
        cnv_hidden: int = 128,
        attn_dim: int = 128,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.img_embed = nn.Sequential(
            nn.Linear(image_dim, img_hidden), nn.ReLU(inplace=True), nn.Dropout(dropout)
        )
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
        self.out_dim = img_hidden + cnv_hidden

    def attention_weights(self, bag: torch.Tensor) -> torch.Tensor:
        """Gated attention weights over the tiles of a single bag."""
        h = self.img_embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        return torch.softmax(score, dim=0)

    def _attend(self, bag: torch.Tensor) -> torch.Tensor:
        h = self.img_embed(bag)
        score = self.attn_c(torch.tanh(self.attn_a(h)) * torch.sigmoid(self.attn_b(h))).squeeze(-1)
        weight = torch.softmax(score, dim=0)
        return torch.sum(h * weight.unsqueeze(-1), dim=0)

    def forward(self, bag: torch.Tensor, cnv: torch.Tensor) -> torch.Tensor:
        """Encode one biopsy. ``bag`` is [n_tiles, image_dim]; ``cnv`` is [cnv_dim]."""
        image = self._attend(bag)
        cnv_embedding = self.cnv_branch(cnv)
        return torch.cat([image, cnv_embedding], dim=-1)


class LongitudinalABMILCNV(nn.Module):
    """Landmarking temporal model over a patient's biopsy history.

    A single forward call processes one landmark: the ordered list of biopsy
    (bag, cnv, time_feat) tuples for that patient up to time ``t``. The
    per-biopsy embeddings are aggregated by the chosen temporal module and the
    aggregated state is classified.

    aggregator:
        "gru"  — GRU; final hidden state feeds the classifier (default).
        "attn" — softmax attention pooling over the sequence embeddings
                 (order-aware via the time feature; a lightweight ablation).
    """

    def __init__(
        self,
        image_dim: int,
        cnv_dim: int,
        img_hidden: int = 256,
        cnv_hidden: int = 128,
        attn_dim: int = 128,
        temporal_hidden: int = 256,
        fusion_hidden: int = 256,
        dropout: float = 0.2,
        aggregator: str = "gru",
        out_dim: int = 1,
    ) -> None:
        super().__init__()
        if aggregator not in {"gru", "attn"}:
            raise ValueError(f"unsupported aggregator: {aggregator!r}")
        self.aggregator = aggregator
        self.encoder = BiopsyEncoder(
            image_dim=image_dim,
            cnv_dim=cnv_dim,
            img_hidden=img_hidden,
            cnv_hidden=cnv_hidden,
            attn_dim=attn_dim,
            dropout=dropout,
        )
        # one scalar time feature appended to each per-biopsy embedding
        self.seq_dim = self.encoder.out_dim + 1

        if aggregator == "gru":
            self.temporal = nn.GRU(
                input_size=self.seq_dim,
                hidden_size=temporal_hidden,
                num_layers=1,
                batch_first=True,
            )
            agg_out = temporal_hidden
        else:  # attn pooling
            self.seq_proj = nn.Sequential(
                nn.Linear(self.seq_dim, temporal_hidden), nn.ReLU(inplace=True), nn.Dropout(dropout)
            )
            self.attn_score = nn.Linear(temporal_hidden, 1)
            agg_out = temporal_hidden

        self.classifier = nn.Sequential(
            nn.Linear(agg_out, fusion_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden, out_dim),
        )

    def _encode_sequence(
        self,
        bags: Sequence[torch.Tensor],
        cnv: torch.Tensor,
        time_feat: torch.Tensor,
    ) -> torch.Tensor:
        """Encode one patient's history into a [seq_len, seq_dim] tensor.

        ``bags`` is a length-``seq_len`` list of [n_tiles, image_dim] tensors,
        ``cnv`` is [seq_len, cnv_dim], ``time_feat`` is [seq_len].
        """
        embeddings = [self.encoder(bag, cnv[i]) for i, bag in enumerate(bags)]
        sequence = torch.stack(embeddings, dim=0)  # [seq_len, encoder.out_dim]
        return torch.cat([sequence, time_feat.unsqueeze(-1)], dim=-1)  # [seq_len, seq_dim]

    def _aggregate(self, sequence: torch.Tensor) -> torch.Tensor:
        """Aggregate a [seq_len, seq_dim] sequence into a single [agg_out] vector."""
        if self.aggregator == "gru":
            _, hidden = self.temporal(sequence.unsqueeze(0))  # hidden: [1, 1, temporal_hidden]
            return hidden.squeeze(0).squeeze(0)
        projected = self.seq_proj(sequence)  # [seq_len, temporal_hidden]
        weights = torch.softmax(self.attn_score(projected).squeeze(-1), dim=0)
        return torch.sum(projected * weights.unsqueeze(-1), dim=0)

    def sequence_attention(
        self,
        bags: Sequence[torch.Tensor],
        cnv: torch.Tensor,
        time_feat: torch.Tensor,
    ) -> torch.Tensor:
        """Per-biopsy attention weights (attn aggregator only) — for interpretation."""
        if self.aggregator != "attn":
            raise ValueError("sequence_attention is only defined for the 'attn' aggregator")
        sequence = self._encode_sequence(bags, cnv, time_feat)
        projected = self.seq_proj(sequence)
        return torch.softmax(self.attn_score(projected).squeeze(-1), dim=0)

    def forward_one(
        self,
        bags: Sequence[torch.Tensor],
        cnv: torch.Tensor,
        time_feat: torch.Tensor,
    ) -> torch.Tensor:
        """Forward a single landmark (one patient history) -> [out_dim] logit."""
        sequence = self._encode_sequence(bags, cnv, time_feat)
        aggregated = self._aggregate(sequence)
        return self.classifier(aggregated)

    def forward(
        self,
        batch_bags: Sequence[Sequence[torch.Tensor]],
        batch_cnv: Sequence[torch.Tensor],
        batch_time: Sequence[torch.Tensor],
    ) -> torch.Tensor:
        """Forward a batch of landmarks (histories vary in length) -> [batch, out_dim].

        Sequences are variable length, so we loop per landmark rather than pad —
        histories are short (median 4 biopsies) and batches are small.
        """
        logits = [
            self.forward_one(bags, cnv, time_feat)
            for bags, cnv, time_feat in zip(batch_bags, batch_cnv, batch_time)
        ]
        return torch.stack(logits, dim=0)
