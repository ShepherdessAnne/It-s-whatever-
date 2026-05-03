from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from volunteer_portal import storage


class StorageTests(unittest.TestCase):
    def test_append_and_load_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            records_file = data_dir / "records.jsonl"

            original = storage.RECORDS_FILE
            storage.RECORDS_FILE = records_file
            try:
                storage.append_record({"example_id": "1", "mode": "file_video_pair"})
                loaded = storage.load_records()
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0]["example_id"], "1")
            finally:
                storage.RECORDS_FILE = original


if __name__ == "__main__":
    unittest.main()
