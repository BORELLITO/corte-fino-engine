import json
import unittest
from pathlib import Path

from editorial.review import review_script


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "salmo_13_script.json"


class ScriptReviewTests(unittest.TestCase):
    def test_salmo13_passes_automated_review(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = review_script(payload)
        self.assertEqual(result.status, "PASS_AUTOMATED_REVIEW")
        self.assertEqual(result.errors, ())
        self.assertGreater(result.word_count, 140)

    def test_forbidden_promise_is_no_go(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["blocks"][3]["text"] += " Milagre garantido para quem esperar."
        result = review_script(payload)
        self.assertEqual(result.status, "NO_GO")
        self.assertTrue(any("forbidden_phrase" in item for item in result.errors))

    def test_wrong_block_order_is_no_go(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["blocks"] = list(reversed(payload["blocks"]))
        result = review_script(payload)
        self.assertIn("review:block_order", result.errors)


if __name__ == "__main__":
    unittest.main()
