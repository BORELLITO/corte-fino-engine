import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_v2_candidate import approved_v2, PARENT_SHA, V2_SHA, OLD, NEW, SCRIPT_PATH, REVIEW_PATH
from agents.e01_voice_preview import approved_source
from agents.autonomous_editorial_gate import canonical_sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "agents/first_batch_seed.json",
    "contracts/autonomous_editorial_policy_v1.json",
    "contracts/e01_ai_editorial_review_v1.json",
    "contracts/kokoro_voice_research_v1.json",
    SCRIPT_PATH,
    REVIEW_PATH,
)

def make_copy(dst: Path):
    for p in SOURCE_FILES:
        target = dst / p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, target)


class V2CandidateTests(unittest.TestCase):
    def test_v2_exact_new_sha_and_v1_unmodified(self):
        text, approved = approved_v2(ROOT)
        self.assertIn(NEW, text)
        self.assertNotIn(OLD, text)
        self.assertEqual(approved["script_sha256"], V2_SHA)
        self.assertEqual(approved["review_file_ref"], REVIEW_PATH)
        self.assertFalse(approved["publication_authorized"])
        old_text, old_receipt = approved_source(ROOT)
        self.assertEqual(old_receipt["script_sha256"], PARENT_SHA)
        self.assertIn(OLD, old_text)

    def test_v2_has_exactly_one_changed_sentence(self):
        seed = json.loads((ROOT / "agents/first_batch_seed.json").read_text(encoding="utf-8"))
        v2 = json.loads((ROOT / SCRIPT_PATH).read_text(encoding="utf-8"))["episode"]
        for i in range(6):
            if i == 1:
                self.assertEqual(v2["blocks"][i]["text"],
                                 seed["episodes"][0]["blocks"][i]["text"].replace(OLD, NEW))
            else:
                self.assertEqual(v2["blocks"][i], seed["episodes"][0]["blocks"][i])

    def test_unreviewed_words_in_other_block_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);make_copy(root)
            path = root / SCRIPT_PATH
            j = json.loads(path.read_text(encoding="utf-8"))
            j["episode"]["blocks"][3]["text"] += " Deus promete amanhã."
            path.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "unreviewed_changes_outside_approved_phrase"):
                approved_v2(root)

    def test_tampered_v2_review_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);make_copy(root)
            path = root / REVIEW_PATH
            j = json.loads(path.read_text(encoding="utf-8"))
            j["reviewed_canonical_script_sha256"] = PARENT_SHA
            path.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
                approved_v2(root)

    def test_v1_review_cannot_approve_v2(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);make_copy(root)
            shutil.copy2(root / "contracts/e01_ai_editorial_review_v1.json", root / REVIEW_PATH)
            with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
                approved_v2(root)

    def test_modified_reference_or_new_religious_promise_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);make_copy(root)
            path=root/SCRIPT_PATH
            j=json.loads(path.read_text(encoding="utf-8"))
            j["episode"]["reference"]="João 3:16"
            path.write_text(json.dumps(j,ensure_ascii=False),encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "unreviewed_changes_outside_approved_phrase"):
                approved_v2(root)

    def test_claiming_voice_licensed_or_published_is_rejected(self):
        for flag in ("voice_rights_cleared","production_wav_master_approved","publication_authorized"):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);make_copy(root)
                path=root/SCRIPT_PATH
                j=json.loads(path.read_text(encoding="utf-8"));j[flag]=True
                path.write_text(json.dumps(j,ensure_ascii=False),encoding="utf-8")
                with self.subTest(flag=flag):
                    with self.assertRaisesRegex(ProductionError, "candidate_release_flags"):
                        approved_v2(root)

    def test_v2_script_length_and_hash_constant(self):
        text, result=approved_v2(ROOT)
        self.assertTrue(950 < len(text) < 1300)
        self.assertEqual(len(V2_SHA), 64)
        self.assertEqual(result["script_sha256"], V2_SHA)
        self.assertNotEqual(PARENT_SHA, V2_SHA)


if __name__ == "__main__":
    unittest.main()
