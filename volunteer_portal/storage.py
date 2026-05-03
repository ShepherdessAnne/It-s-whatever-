from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
RECORDS_FILE = DATA_DIR / "records.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_upload(src_path: Path, dst_path: Path) -> dict[str, Any]:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    return {
        "filename": dst_path.name,
        "stored_path": str(dst_path.relative_to(BASE_DIR)),
        "sha256": sha256_of_file(dst_path),
        "size_bytes": dst_path.stat().st_size,
    }


def append_record(record: dict[str, Any]) -> None:
    with RECORDS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_records() -> list[dict[str, Any]]:
    if not RECORDS_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with RECORDS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def create_file_video_record(
    project_file_paths: list[Path],
    video_path: Path,
    display_name: str | None,
) -> dict[str, Any]:
    example_id = str(uuid4())
    example_dir = UPLOAD_DIR / example_id

    project_files = []
    for path in project_file_paths:
        saved = save_upload(path, example_dir / "project_files" / path.name)
        project_files.append(saved)

    video = save_upload(video_path, example_dir / "video" / video_path.name)

    record = {
        "example_id": example_id,
        "mode": "file_video_pair",
        "project_files": project_files,
        "video": video,
        "volunteer": {"display_name": display_name or ""},
        "feedback": [],
        "created_at": now_iso(),
    }
    append_record(record)
    return record


def create_prompt_video_record(
    prompt: str,
    video_path: Path,
    display_name: str | None,
) -> dict[str, Any]:
    example_id = str(uuid4())
    example_dir = UPLOAD_DIR / example_id

    video = save_upload(video_path, example_dir / "video" / video_path.name)

    record = {
        "example_id": example_id,
        "mode": "prompt_video_pair",
        "prompt": prompt,
        "video": video,
        "volunteer": {"display_name": display_name or ""},
        "feedback": [],
        "created_at": now_iso(),
    }
    append_record(record)
    return record


def add_feedback(
    example_id: str,
    comment: str,
    author: str | None,
    labels: list[str] | None,
) -> dict[str, Any]:
    records = load_records()
    new_feedback = {
        "feedback_id": str(uuid4()),
        "author": author or "",
        "comment": comment,
        "labels": labels or [],
        "created_at": now_iso(),
    }

    updated = False
    for record in records:
        if record.get("example_id") == example_id:
            record.setdefault("feedback", []).append(new_feedback)
            updated = True
            break

    if not updated:
        raise ValueError(f"example_id not found: {example_id}")

    with RECORDS_FILE.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return new_feedback
