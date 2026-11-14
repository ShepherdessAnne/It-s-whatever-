from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import torch
except ImportError:
    torch = None


@unittest.skipIf(torch is None, "torch unavailable")
class TokenTests(unittest.TestCase):
    def test_project_reads_only_token_budget(self) -> None:
        with patch.dict(sys.modules, {"av": sys.modules.get("av", types.ModuleType("av"))}):
            from pipeline.train import project_bytes_as_tokens
        with tempfile.TemporaryDirectory() as tmp:
            huge = Path(tmp) / "huge.blend"
            huge.write_bytes(b"A" * 1024 * 1024)
            following = Path(tmp) / "next.blend"
            following.write_bytes(b"ignored")
            with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read_bytes")):
                self.assertEqual(project_bytes_as_tokens((huge, following), 4).tolist(), [66, 66, 66, 66])

    def test_project_token_separators_and_padding_unchanged(self) -> None:
        with patch.dict(sys.modules, {"av": sys.modules.get("av", types.ModuleType("av"))}):
            from pipeline.train import project_bytes_as_tokens
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a", Path(tmp) / "b"
            first.write_bytes(b"\x00\xff")
            second.write_bytes(b"\x01")
            self.assertEqual(project_bytes_as_tokens((first, second), 8).tolist(), [1, 256, 257, 2, 257, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
