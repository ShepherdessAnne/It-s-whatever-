from __future__ import annotations

import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.pull_and_build_components import load_components


class ComponentLoaderTests(unittest.TestCase):
    def test_load_components_expands_environment_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "components.json"
            config.write_text(
                textwrap.dedent(
                    """
                    {
                      "components": [
                        {
                          "name": "example",
                          "repo": "${EXAMPLE_REPO}",
                          "ref": "${EXAMPLE_REF:-main}",
                          "build_cmd": "${EXAMPLE_BUILD:-python -m pip wheel . -w dist}"
                        }
                      ]
                    }
                    """
                ).strip(),
                encoding="utf-8",
            )

            original_repo = os.environ.get("EXAMPLE_REPO")
            os.environ["EXAMPLE_REPO"] = "https://example.com/repo.git"
            try:
                components = load_components(config)
            finally:
                if original_repo is None:
                    os.environ.pop("EXAMPLE_REPO", None)
                else:
                    os.environ["EXAMPLE_REPO"] = original_repo

            self.assertEqual(len(components), 1)
            self.assertEqual(components[0].repo, "https://example.com/repo.git")
            self.assertEqual(components[0].ref, "main")


if __name__ == "__main__":
    unittest.main()
