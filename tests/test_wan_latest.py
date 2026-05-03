from __future__ import annotations

import unittest

from scripts.check_wan_latest import _wan_model_minor, latest_wan_repo_name


class WanLatestTests(unittest.TestCase):
    def test_latest_repo_name(self) -> None:
        repo_names = ["Wan2.1", "Wan2.2", "Wan2.10", "misc"]
        self.assertEqual(latest_wan_repo_name(repo_names), "Wan2.10")

    def test_wan_model_minor(self) -> None:
        self.assertEqual(_wan_model_minor("wan@2.7"), 7)
        self.assertIsNone(_wan_model_minor("wan-2.7"))


if __name__ == "__main__":
    unittest.main()
