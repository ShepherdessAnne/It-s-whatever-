"""Load raw project-file/video pairs for the trainable baseline.

The project files deliberately remain unnormalised: their bytes are the model
input.  This is the project's current data contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PairRecord:
    example_id: str
    project_files: tuple[Path, ...]
    video: Path


def read_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def resolve_stored_path(stored_path: str, manifest_path: Path) -> Path:
    """Resolve portal paths relative to the portal package, not the CWD."""
    candidate = Path(stored_path)
    if candidate.is_absolute():
        return candidate
    if manifest_path.parent.name == "data" and manifest_path.parent.parent.name == "volunteer_portal":
        return manifest_path.parent.parent / candidate
    return manifest_path.parent / candidate


def paired_records(manifest_path: Path) -> list[PairRecord]:
    pairs: list[PairRecord] = []
    for row in read_manifest(manifest_path):
        if row.get("mode") != "file_video_pair":
            continue
        project_files = tuple(
            resolve_stored_path(item["stored_path"], manifest_path)
            for item in row.get("project_files", [])
            if item.get("stored_path")
        )
        video_info = row.get("video") or {}
        if not project_files or not video_info.get("stored_path"):
            continue
        pairs.append(
            PairRecord(
                example_id=str(row.get("example_id", "unknown")),
                project_files=project_files,
                video=resolve_stored_path(video_info["stored_path"], manifest_path),
            )
        )
    return pairs


def preflight(pairs: list[PairRecord]) -> list[str]:
    """Return actionable errors without silently dropping paired examples."""
    errors: list[str] = []
    for pair in pairs:
        missing = [str(path) for path in (*pair.project_files, pair.video) if not path.is_file()]
        if missing:
            errors.append(f"{pair.example_id}: missing files: {', '.join(missing)}")
    return errors
