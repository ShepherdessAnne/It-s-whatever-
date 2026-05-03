from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Batch:
    example_id: str
    mode: str


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")

    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_batches(records: list[dict]) -> list[Batch]:
    return [
        Batch(example_id=str(item.get("example_id", "unknown")), mode=str(item.get("mode", "unknown")))
        for item in records
    ]


def train(manifest: Path, epochs: int) -> None:
    records = read_manifest(manifest)
    batches = build_batches(records)

    if not batches:
        print("No samples found in manifest; nothing to train.")
        return

    print(f"Loaded {len(batches)} paired samples from {manifest}")
    for epoch in range(1, epochs + 1):
        print(f"Epoch {epoch}/{epochs}")
        for batch in batches:
            # Placeholder for real multi-model forward/backward pass.
            print(f"  training on example={batch.example_id} mode={batch.mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train on paired ingestion manifest")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to JSONL records manifest")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    train(args.manifest, args.epochs)
