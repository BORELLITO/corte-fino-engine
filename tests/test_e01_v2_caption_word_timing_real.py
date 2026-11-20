"""Pins the real per-word timing copied from the E01 v2 captions artifact."""
import hashlib
import json
import unittest
from pathlib import Path

from agents.e01_v2_caption_pipeline import (
    ASR_BYTES, ASR_SHA, MAX_LINES, SCRIPT_SHA, VOICE_DURATION, WAV_SHA, make_cues,
)

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "contracts/e01_v2_caption_word_timing_real_v1.json"
TIMELINE_SHA = "cac98a9c82dfbcdc0d77c204733d31f3568bc1b5991bcbe2d5b5fc0c9aa5d53e"


class E01RealWordTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))
        cls.words = cls.data["words"]

    def test_provenance_and_hashes_pinned(self):
        p = self.data["provenance"]
        self.assertEqual(p["source_workflow_run_id"], 44208934506)
        self.assertEqual(p["source_artifact_id"], 14385236602)
        self.assertEqual(p["source_file_sha256"], TIMELINE_SHA)
        self.assertEqual(p["script_sha256"], SCRIPT_SHA)
        self.assertEqual(p["wav_sha256"], WAV_SHA)
        self.assertEqual(p["asr_report_sha256"], ASR_SHA)
        self.assertEqual(p["asr_report_bytes"], ASR_BYTES)
        self.assertEqual(self.data["speech_duration_seconds"], VOICE_DURATION)
        evidence = json.loads((ROOT / p["evidence_contract"]).read_text(encoding="utf-8"))
        listed = {o["filename"]: o for o in evidence["outputs"]}
        self.assertEqual(listed[p["source_file"]]["sha256"], TIMELINE_SHA)
        self.assertEqual(listed[p["source_file"]]["bytes"], p["source_file_bytes"])

    def test_182_words_ordered_and_bounded(self):
        w = self.words
        self.assertEqual(len(w), 182)
        self.assertEqual(self.data["word_count"], 182)
        self.assertEqual([x["index"] for x in w], list(range(182)))
        for x in w:
            self.assertLess(x["start"], x["end"], x["text"])
            self.assertGreaterEqual(x["start"], 0)
            self.assertLessEqual(x["end"], VOICE_DURATION, x["text"])
        for a, b in zip(w, w[1:]):
            self.assertLessEqual(a["start"], b["start"])
            self.assertLessEqual(a["end"], b["end"])

    def test_make_cues_two_lines_no_overlap(self):
        cues = make_cues([dict(x) for x in self.words])
        # Current (v3) layout re-cues the words; the artifact's 28 cues used the old layout.
        self.assertEqual(self.data["provenance"]["source_cue_count"], 28)
        self.assertGreaterEqual(len(cues), 20)
        for c in cues:
            self.assertLessEqual(len(c["lines"]), MAX_LINES)
            self.assertLess(c["start"], c["end"])
        for a, b in zip(cues, cues[1:]):
            self.assertLessEqual(a["end"], b["start"])
        self.assertEqual([x["index"] for c in cues for x in c["words"]], list(range(182)))


if __name__ == "__main__":
    unittest.main()
