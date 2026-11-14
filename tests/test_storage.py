from __future__ import annotations

import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from volunteer_portal import storage


class StorageTests(unittest.TestCase):
    def test_append_and_load_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records_file = Path(tmp) / "records.jsonl"
            with patch.object(storage, "RECORDS_FILE", records_file):
                storage.append_record({"example_id": "1", "mode": "file_video_pair"})
                loaded = storage.load_records()
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0]["example_id"], "1")

    def test_simultaneous_feedback_is_not_lost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(storage, "RECORDS_FILE", Path(tmp) / "records.jsonl"):
                storage.append_record({"example_id": "x", "feedback": []})
                with ThreadPoolExecutor(max_workers=8) as pool:
                    feedback = list(pool.map(
                        lambda i: storage.add_feedback("x", f"comment-{i}", None, None), range(32)
                    ))
                self.assertEqual(len({row["feedback_id"] for row in feedback}), 32)
                self.assertEqual(len(storage.load_records()[0]["feedback"]), 32)

    def test_append_cannot_be_overwritten_by_feedback_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(storage, "RECORDS_FILE", Path(tmp) / "records.jsonl"):
                storage.append_record({"example_id": "existing", "feedback": []})
                loaded = threading.Event()
                release = threading.Event()
                append_finished = threading.Event()
                errors: list[BaseException] = []
                original = storage._load_records_unlocked

                def paused_read():
                    rows = original()
                    if threading.current_thread().name == "feedback-thread":
                        loaded.set()
                        if not release.wait(5):
                            raise TimeoutError("feedback read was not released")
                    return rows

                def feedback_task():
                    try:
                        storage.add_feedback("existing", "new", None, None)
                    except BaseException as exc:
                        errors.append(exc)

                def append_task():
                    try:
                        storage.append_record({"example_id": "new", "feedback": []})
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        append_finished.set()

                with patch.object(storage, "_load_records_unlocked", side_effect=paused_read):
                    feedback_thread = threading.Thread(target=feedback_task, name="feedback-thread")
                    append_thread = threading.Thread(target=append_task)
                    feedback_thread.start()
                    try:
                        self.assertTrue(loaded.wait(3))
                        append_thread.start()
                        self.assertFalse(append_finished.wait(0.1), "append bypassed the rewrite lock")
                    finally:
                        release.set()
                        feedback_thread.join(timeout=5)
                        if append_thread.ident is not None:
                            append_thread.join(timeout=5)
                self.assertFalse(errors, errors)
                self.assertEqual({row["example_id"] for row in storage.load_records()}, {"existing", "new"})
                self.assertEqual(len(storage.load_records()[0]["feedback"]), 1)


if __name__ == "__main__":
    unittest.main()
