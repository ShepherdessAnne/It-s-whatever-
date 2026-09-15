"""Train the raw project-file -> final-video baseline on submitted pairs."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import av
import torch
from torch import Tensor
from torch.nn import functional as functional
from torch.utils.data import DataLoader, Dataset

from pipeline.dataset import PairRecord, paired_records, preflight
from pipeline.model import RawFileVideoModel


def project_bytes_as_tokens(paths: tuple[Path, ...], max_tokens: int) -> Tensor:
    """Keep each source file raw, separating files with token 257; zero pads."""
    values: list[int] = []
    for path in paths:
        values.extend(byte + 1 for byte in path.read_bytes())
        values.append(257)
        if len(values) >= max_tokens:
            break
    return torch.tensor((values[:max_tokens] + [0] * max_tokens)[:max_tokens], dtype=torch.long)


def decode_video(path: Path, frame_count: int, size: int) -> Tensor:
    decoded: list[Tensor] = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            image = torch.from_numpy(frame.to_ndarray(format="rgb24")).permute(2, 0, 1).float() / 255
            decoded.append(image)
            if len(decoded) >= frame_count:
                break
    if not decoded:
        raise ValueError(f"no decodable video frames in {path}")
    while len(decoded) < frame_count:
        decoded.append(decoded[-1].clone())
    video = torch.stack(decoded[:frame_count], dim=1).unsqueeze(0)
    return functional.interpolate(video, size=(frame_count, size, size), mode="trilinear", align_corners=False).squeeze(0)


class PairedDataset(Dataset[tuple[Tensor, Tensor]]):
    def __init__(self, pairs: list[PairRecord], max_tokens: int, frames: int, size: int) -> None:
        self.pairs, self.max_tokens, self.frames, self.size = pairs, max_tokens, frames, size

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        pair = self.pairs[index]
        return project_bytes_as_tokens(pair.project_files, self.max_tokens), decode_video(pair.video, self.frames, self.size)


def train(manifest: Path, output: Path, epochs: int, batch_size: int, frames: int, size: int, max_tokens: int) -> None:
    pairs = paired_records(manifest)
    errors = preflight(pairs)
    if errors:
        raise RuntimeError("Dataset preflight failed:\n" + "\n".join(errors))
    if not pairs:
        raise RuntimeError("No valid file_video_pair records found in manifest")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = PairedDataset(pairs, max_tokens=max_tokens, frames=frames, size=size)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = RawFileVideoModel(max_tokens=max_tokens).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)
    output.mkdir(parents=True, exist_ok=True)
    print(f"Training {len(dataset)} paired examples on {device}.")
    for epoch in range(1, epochs + 1):
        model.train()
        losses: list[float] = []
        for tokens, target in loader:
            tokens, target = tokens.to(device), target.to(device)
            prediction = model(tokens, frames=frames, height=size, width=size)
            reconstruction = functional.mse_loss(prediction, target)
            temporal = functional.l1_loss(prediction[:, :, 1:] - prediction[:, :, :-1], target[:, :, 1:] - target[:, :, :-1])
            loss = reconstruction + 0.1 * temporal
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(loss.item())
        mean_loss = sum(losses) / len(losses)
        print(f"epoch={epoch} loss={mean_loss:.6f}")
        torch.save({"epoch": epoch, "model": model.state_dict(), "optimizer": optimizer.state_dict(), "loss": mean_loss}, output / "checkpoint.pt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train raw project-file to final-video reconstruction baseline")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--max-tokens", type=int, default=8192)
    args = parser.parse_args()
    random.seed(0)
    torch.manual_seed(0)
    train(**vars(args))
