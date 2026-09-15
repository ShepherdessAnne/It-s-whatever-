from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.dataset import paired_records, preflight


class DatasetTests(unittest.TestCase):
    def test_file_video_pairs_resolve_from_portal_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "volunteer_portal"
            manifest = root / "data" / "records.jsonl"
            project = root / "uploads" / "a" / "project_files" / "scene.blend"
            video = root / "uploads" / "a" / "video" / "render.mp4"
            project.parent.mkdir(parents=True)
            video.parent.mkdir(parents=True)
            project.write_bytes(b"scene")
            video.write_bytes(b"video")
            manifest.parent.mkdir(parents=True, exist_ok=True)
            records = [
                {"example_id": "a", "mode": "file_video_pair", "project_files": [{"stored_path": "uploads/a/project_files/scene.blend"}], "video": {"stored_path": "uploads/a/video/render.mp4"}},
                {"example_id": "future", "mode": "prompt_video_pair", "video": {"stored_path": "unused.mp4"}},
            ]
            manifest.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")

            pairs = paired_records(manifest)

            self.assertEqual([pair.example_id for pair in pairs], ["a"])
            self.assertEqual(preflight(pairs), [])

    def test_preflight_reports_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "records.jsonl"
            manifest.write_text(json.dumps({"example_id": "missing", "mode": "file_video_pair", "project_files": [{"stored_path": "scene.blend"}], "video": {"stored_path": "render.mp4"}}) + "\n", encoding="utf-8")
            errors = preflight(paired_records(manifest))
            self.assertEqual(len(errors), 1)
            self.assertIn("missing", errors[0])


if __name__ == "__main__":
    unittest.main()
