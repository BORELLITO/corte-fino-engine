import tempfile
import unittest
from pathlib import Path

from qa.clean_room_gate import violations


class CleanRoomGateTests(unittest.TestCase):
    def test_clean_fixture_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Verbo no Chão\n", encoding="utf-8")
            (root / "contracts").mkdir()
            self.assertEqual(violations(root), [])

    def test_unapproved_root_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Verbo no Chão\n", encoding="utf-8")
            (root / "old").mkdir()
            (root / "old" / "file.txt").write_text("x", encoding="utf-8")
            self.assertTrue(any("outside-approved-root" in item for item in violations(root)))


if __name__ == "__main__":
    unittest.main()
