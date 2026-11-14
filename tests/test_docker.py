from pathlib import Path
import unittest


class DockerPackagingTests(unittest.TestCase):
    def test_image_copies_scripts_declared_in_pyproject(self):
        dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text()
        self.assertIn("COPY scripts ./scripts", dockerfile)


if __name__ == "__main__":
    unittest.main()
