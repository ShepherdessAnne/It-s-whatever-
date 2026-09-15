"""A compact, trainable raw-file-conditioned video reconstruction model."""

from __future__ import annotations

import torch
from torch import Tensor, nn


class RawFileVideoModel(nn.Module):
    """Condition a small video decoder on raw project-file byte tokens.

    This is intentionally a working baseline, not a claim that the external
    research models have been merged.  It gives the paired-data pipeline a
    concrete forward/backward path today.
    """

    def __init__(self, vocab_size: int = 258, width: int = 256, max_tokens: int = 8192) -> None:
        super().__init__()
        self.max_tokens = max_tokens
        self.token_embedding = nn.Embedding(vocab_size, width, padding_idx=0)
        self.position_embedding = nn.Embedding(max_tokens, width)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=width, nhead=8, dim_feedforward=width * 4, batch_first=True, activation="gelu"
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=4)
        self.condition = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, width), nn.GELU())
        self.decoder = nn.Sequential(
            nn.ConvTranspose3d(width, 128, kernel_size=(2, 4, 4), stride=(2, 4, 4)),
            nn.GELU(),
            nn.ConvTranspose3d(128, 64, kernel_size=(2, 4, 4), stride=(2, 4, 4)),
            nn.GELU(),
            nn.Conv3d(64, 3, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, tokens: Tensor, frames: int, height: int, width: int) -> Tensor:
        if tokens.ndim != 2:
            raise ValueError("tokens must have shape [batch, sequence]")
        if tokens.shape[1] > self.max_tokens:
            raise ValueError(f"token sequence exceeds max_tokens={self.max_tokens}")
        positions = torch.arange(tokens.shape[1], device=tokens.device).unsqueeze(0)
        encoded = self.encoder(
            self.token_embedding(tokens) + self.position_embedding(positions),
            src_key_padding_mask=tokens.eq(0),
        )
        mask = tokens.ne(0).unsqueeze(-1)
        pooled = (encoded * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)
        latent = self.condition(pooled).view(tokens.shape[0], -1, 1, 1, 1)
        output = self.decoder(latent)
        return nn.functional.interpolate(output, size=(frames, height, width), mode="trilinear", align_corners=False)
