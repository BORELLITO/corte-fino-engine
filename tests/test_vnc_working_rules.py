import hashlib
import json
import unittest
from pathlib import Path


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


class WorkingRulesTests(unittest.TestCase):
    def test_both_owner_rules_are_registered_with_enforcement(self):
        r = _j("contracts/vnc_working_rules_v1.json")
        self.assertEqual([x["id"] for x in r["rules"]], ["R1", "R2", "R3"])
        for x in r["rules"]:
            for f in x["enforced_by"]:
                self.assertTrue(Path(f).is_file(), f)
        self.assertTrue(Path("docs/REGRAS_DE_TRABALHO_VNC_V1.md").is_file())

    def test_r1_every_stage_has_a_physical_preview_with_matching_hash(self):
        m = _j("contracts/e01_v3_preview_manifest_v1.json")
        self.assertEqual(set(m["stages"]), {"captions", "caption_band", "scenes", "clip_review"})
        for name, st in m["stages"].items():
            self.assertTrue(Path(st["contract"]).is_file(), name)
            self.assertTrue(st["previews"], name)
            for pv in st["previews"]:
                f = m["files"][pv]
                data = Path(pv).read_bytes()
                self.assertGreater(len(data), 10_000, pv)
                self.assertEqual(len(data), f["bytes"], pv)
                self.assertEqual(hashlib.sha256(data).hexdigest(), f["sha256"], pv)
                head = data[:12]
                self.assertTrue(head[:8] == b"\x89PNG\r\n\x1a\n" or head[4:8] == b"ftyp", pv)
        self.assertIs(m["approved_by_user"], False)

    def test_r1_previews_carry_no_audio_track(self):
        data = Path("previews/e01_v3/e01_v3_captions_0-26s_SEM_AUDIO.mp4").read_bytes()
        self.assertNotIn(b"soun", data)  # no audio handler box

    def test_r2_every_scene_is_reviewed_and_nothing_is_approved(self):
        c = _j("contracts/e01_v3_clip_review_v1.json")
        refit = _j("contracts/e01_v3_12_scene_refit_v1.json")
        self.assertEqual([s["scene"] for s in c["scenes"]], [s["id"] for s in refit["scenes"]])
        self.assertIs(c["any_clip_approved"], False)
        self.assertIs(c["frames_viewed"], False)
        self.assertEqual(c["scenes_with_viable_candidate"] + c["scenes_without_clip"], 12)
        for s, r in zip(c["scenes"], refit["scenes"]):
            self.assertEqual(s["scene_seconds"], r["duration_seconds"])
            self.assertEqual(s["min_source_seconds_with_handles"], round(r["duration_seconds"] + 1.0, 2))
            self.assertEqual(s["needs_second_shot"], r["needs_internal_shot_change"])
            self.assertIn("faixa y", s["refined_requirements"]["framing_pt"])
            if s["viable_candidates"]:
                self.assertEqual(s["status"], "CANDIDATE_PENDING_FRAME_REVIEW")
            else:
                self.assertEqual(s["status"], "NO_VIABLE_CLIP_ACQUISITION_NEEDED")
            for cl in s["viable_candidates"]:
                self.assertNotIn("REJECTED", cl["state"])

    def test_r2_contract_is_reproducible_from_evidence(self):
        from agents.e01_v3_clip_review import OUT, build
        self.assertEqual(build(), _j(OUT))


if __name__ == "__main__":
    unittest.main()


class ElevenLabsAudioOnlyRuleTests(unittest.TestCase):
    def test_r3_registered_and_forbids_visual_generation_there(self):
        r = _j("contracts/vnc_working_rules_v1.json")
        r3 = [x for x in r["rules"] if x["id"] == "R3"][0]
        self.assertIn("somente para áudio", r3["text_pt"])
        self.assertIn("nunca são gerados nele", r3["text_pt"])
