from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import UploadFile
from volunteer_portal import app as portal


def upload(name: str, content: bytes = b"data") -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(content))


class UploadCleanupTests(unittest.TestCase):
    def test_file_video_cleans_staging_after_success(self) -> None:
        captured = []

        def save(project_paths, video_path, display_name):
            captured.extend([*project_paths, video_path])
            self.assertEqual([p.read_bytes() for p in captured], [b"scene", b"scene2", b"video"])
            return {"example_id": "ok"}

        with patch.object(portal, "create_file_video_record", side_effect=save):
            portal.submit_file_video("volunteer", [upload("one.blend", b"scene"), upload("two.json", b"scene2")], upload("out.mp4", b"video"))

        self.assertEqual(len(captured), 3)
        self.assertTrue(all(not p.exists() for p in captured))

    def test_file_video_cleans_staging_on_persistence_error(self) -> None:
        captured = []

        def fail(project_paths, video_path, display_name):
            captured.extend([*project_paths, video_path])
            raise RuntimeError("storage failure")

        with patch.object(portal, "create_file_video_record", side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, "storage failure"):
                portal.submit_file_video("", [upload("scene.blend")], upload("out.mp4"))
        self.assertEqual(len(captured), 2)
        self.assertTrue(all(not p.exists() for p in captured))

    def test_prompt_video_cleans_staging_on_success_and_error(self) -> None:
        captured = []

        def save(prompt, video_path, display_name):
            captured.append(video_path)
            self.assertEqual(video_path.read_bytes(), b"movie")
            if prompt == "fail":
                raise RuntimeError("storage failure")
            return {"example_id": "ok"}

        with patch.object(portal, "create_prompt_video_record", side_effect=save):
            portal.submit_prompt_video("success", "", upload("video.mp4", b"movie"))
            with self.assertRaisesRegex(RuntimeError, "storage failure"):
                portal.submit_prompt_video("fail", "", upload("video.mp4", b"movie"))
        self.assertEqual(len(captured), 2)
        self.assertTrue(all(not p.exists() for p in captured))

    def test_file_video_cleans_partial_staging_if_next_upload_fails(self) -> None:
        class BrokenStream(io.BytesIO):
            def read(self, *args, **kwargs):
                raise OSError("broken upload")

        original_named_temp = tempfile.NamedTemporaryFile
        with tempfile.TemporaryDirectory() as tmp:
            def local_temp(*args, **kwargs):
                return original_named_temp(*args, dir=tmp, **kwargs)

            with patch.object(portal.tempfile, "NamedTemporaryFile", side_effect=local_temp):
                with self.assertRaisesRegex(OSError, "broken upload"):
                    portal.submit_file_video("", [upload("good.blend"), UploadFile(filename="bad.blend", file=BrokenStream())], upload("out.mp4"))
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
