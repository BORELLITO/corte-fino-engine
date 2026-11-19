"""Offline adversarial tests for rejected E01 S01 stock footage."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agents import e01_s01_stock_rejection_gate as g
from agents import e01_s01_multi_stock_pilot_v1 as pilot


def valid_preview(sha, ids):
    return {
        "project": "VERBO_NO_CHAO_EXCLUSIVO",
        "scene_id": "VNC-E01V2-S01",
        "status": "REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_EDITORIAL_AND_RIGHTS_PENDING",
        "editorial_reviewed": False,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
        "source_audio_added": False,
        "captions_added": False,
        "full_video_decode_ok": True,
        "output_sha256": sha,
        "source_clips": [
            {
                "video_id": i,
                "page_url": f"https://www.pexels.com/video/source-{i}/",
                "source_sha256": hashlib.sha256(str(i).encode()).hexdigest(),
                "source_rights_cleared": False,
            } for i in ids
        ],
    }


class S01StockRejectionLock(unittest.TestCase):
    def test_registry_is_locked_by_independent_history(self):
        r = g.load_registry()
        self.assertEqual(len(r["rejections"]), 2)
        self.assertEqual({x["output_sha256"] for x in r["rejections"]},
                         set(g.LOCKED_REJECTIONS))

    def test_both_previously_rejected_outputs_remain_rejected(self):
        for sha, sources in g.LOCKED_REJECTIONS.items():
            with self.subTest(sha=sha):
                verdict = g.classify_s01_stock_preview(
                    valid_preview(sha, sorted(sources))
                )
                self.assertEqual(verdict["editorial_decision"],
                                 "REJECTED_EDITORIAL_PREVIOUS_QA")
                self.assertEqual(verdict["release_gate"], "BLOCKED_NOT_MASTER")
                self.assertFalse(verdict["publication_authorized"])
                self.assertFalse(verdict["master_allowed"])

    def test_different_encode_of_same_rejected_source_set_is_still_rejected(self):
        sha = "f" * 64
        v = g.classify_s01_stock_preview(valid_preview(sha, [8860242, 4458845]))
        self.assertEqual(v["reason"], "known_rejected_output_or_identical_stock_source_set")

    def test_new_source_set_is_only_pending_not_accepted(self):
        sha = "a" * 64
        v = g.classify_s01_stock_preview(valid_preview(sha, [11111, 22222]))
        self.assertEqual(v["editorial_decision"], "PENDING_HUMAN_FRAME_AND_RIGHTS_REVIEW")
        self.assertFalse(v["semantic_review_completed"])
        self.assertFalse(v["license_review_completed"])
        self.assertEqual(v["release_gate"], "BLOCKED_NOT_MASTER")

    def test_false_rights_master_publication_or_audio_claims_are_blocked(self):
        for flag in ("editorial_reviewed", "rights_cleared", "master_allowed",
                     "publication_authorized", "source_audio_added", "captions_added"):
            report = valid_preview("a" * 64, [11111])
            report[flag] = True
            with self.subTest(flag=flag), self.assertRaises(g.S01EditorialGateError):
                g.classify_s01_stock_preview(report)

    def test_fake_metadata_and_misidentified_project_are_blocked(self):
        for field, value in (("project", "CORTE_FINO"), ("scene_id", "VNC-E01V2-S02"),
                             ("status", "READY_FOR_OWNER_APPROVAL"),
                             ("output_sha256", "invalid"),
                             ("full_video_decode_ok", False),
                             ("source_clips", [])):
            report = valid_preview("a" * 64, [11111])
            report[field] = value
            with self.subTest(field=field), self.assertRaises(g.S01EditorialGateError):
                g.classify_s01_stock_preview(report)

    def test_source_license_claim_duplicate_and_wrong_origin_blocked(self):
        for change in ("license", "duplicate", "wrong_origin", "bad_hash"):
            report = valid_preview("a" * 64, [11111, 22222])
            if change == "license":
                report["source_clips"][0]["source_rights_cleared"] = True
            elif change == "duplicate":
                report["source_clips"][1]["video_id"] = 11111
            elif change == "wrong_origin":
                report["source_clips"][0]["page_url"] = "https://invalid.example/a.mp4"
            elif change == "bad_hash":
                report["source_clips"][0]["source_sha256"] = "0"
            with self.subTest(change=change), self.assertRaises(g.S01EditorialGateError):
                g.classify_s01_stock_preview(report)

    def test_actual_movie_hash_must_match_report(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "physical.mp4"
            path.write_bytes(b"fixture only - not a video; no physical decode is claimed")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            report = valid_preview(digest, [12345])
            verdict = g.classify_s01_stock_preview(report, movie_path=path)
            self.assertTrue(verdict["physical_sha_checked"])
            self.assertEqual(verdict["release_gate"], "BLOCKED_NOT_MASTER")
            report["output_sha256"] = "e" * 64
            with self.assertRaises(g.S01EditorialGateError):
                g.classify_s01_stock_preview(report, movie_path=path)
            path.unlink()
            with self.assertRaises(g.S01EditorialGateError):
                g.classify_s01_stock_preview(valid_preview(digest, [12345]),
                                              movie_path=path)

    def test_registry_mutation_is_fail_closed(self):
        baseline = g.load_registry()
        variants = []
        broken = copy.deepcopy(baseline)
        broken["rejections"].pop()
        variants.append(broken)
        broken = copy.deepcopy(baseline)
        broken["rejections"][0]["decision"] = "APPROVED"
        variants.append(broken)
        broken = copy.deepcopy(baseline)
        broken["rejections"][1]["output_sha256"] = "0" * 64
        variants.append(broken)
        broken = copy.deepcopy(baseline)
        broken["rejections"][1]["source_video_ids"] = [111111]
        variants.append(broken)
        broken = copy.deepcopy(baseline)
        broken["publication_authorized"] = True
        variants.append(broken)
        broken = copy.deepcopy(baseline)
        broken["rejections"][0]["rights_cleared"] = True
        variants.append(broken)
        for obj in variants:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "registry.json"
                path.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(g.S01EditorialGateError):
                    g.load_registry(path)

    def test_physical_pilot_has_release_lock_in_its_result_path(self):
        import inspect
        source = inspect.getsource(pilot.main)
        self.assertIn("classify_s01_stock_preview(result, movie_path=target)", source)
        self.assertIn("REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_REJECTED_EDITORIAL", source)
        self.assertEqual([s["id"] for s in pilot.INPUTS], [8860242, 4458845])


if __name__ == "__main__":
    unittest.main()
