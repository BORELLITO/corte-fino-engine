"""Reject accidental release of unverified Pexels shortlist media."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from agents.e01_stock_candidates import CONTRACT, ROOT, StockIntakeError, validate, main, run_probe

class TestE01StockCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / CONTRACT).read_text(encoding="utf-8"))

    def edited(self, mutate):
        data = copy.deepcopy(self.original)
        mutate(data)
        return data

    def test_candidates_remain_pending_and_match_storyboard(self):
        result = validate(ROOT)
        self.assertEqual(result["candidate_count"], 4)
        self.assertEqual(result["source_media_bytes_verified"], 0)
        self.assertFalse(result["ready_for_final_master"])
        self.assertFalse(result["publication_authorized"])

    def test_cannot_promote_to_master_without_media(self):
        for field in ("full_media_integrity_confirmed",
                      "footage_approved_for_edit", "final_master_available",
                      "publication_authorized"):
            with self.subTest(field=field):
                data = self.edited(lambda d: d.update({field: True}))
                with self.assertRaises(StockIntakeError):
                    validate(ROOT, data)

    def test_cannot_claim_download_or_commercial_rights(self):
        for key, value in (("download_performed", True),
                           ("physical_sha256", "a"*64),
                           ("physical_probe", {}),
                           ("third_party_rights", "CLEARED"),
                           ("commercial_publication_cleared", True),
                           ("editorial_status", "APPROVED")):
            with self.subTest(key=key):
                data = self.edited(
                    lambda d: d["candidates"][0].update({key: value}))
                with self.assertRaises(StockIntakeError):
                    validate(ROOT, data)

    def test_wrong_host_and_id_cannot_be_downloaded(self):
        for url in ("https://evil.invalid/video-files/40417800/x.mp4",
                    "http://videos.pexels.com/video-files/40417800/x.mp4",
                    "https://videos.pexels.com/video-files/999/x.mp4",
                    "https://videos.pexels.com/video-files/40417800/x.mp4?key=1",
                    "https://videos.pexels.com.evil.invalid/video-files/40417800/x.mp4"):
            with self.subTest(url=url):
                data = self.edited(lambda d:
                    d["candidates"][0].update(download_url=url))
                with self.assertRaises(StockIntakeError):
                    validate(ROOT, data)

    def test_short_clip_mismatch_rejected(self):
        data = self.edited(lambda d:
            d["candidates"][1].update(page_duration_seconds=3))
        with self.assertRaises(StockIntakeError):
            validate(ROOT, data)

    def test_duplicate_video_or_scene_blocked(self):
        data = self.edited(lambda d:
            d["candidates"][1].update(video_id=40417800))
        with self.assertRaises(StockIntakeError):
            validate(ROOT, data)
        data = self.edited(lambda d:
            d["candidates"][1].update(scene_id="VNC-E01V2-S03"))
        with self.assertRaises(StockIntakeError):
            validate(ROOT, data)

    def test_cdn_replacement_cannot_pass_with_same_valid_metadata(self):
        from unittest.mock import patch
        def forged(item, temp, ffprobe, ffmpeg):
            return {"id": item["id"], "sha256": "f"*64}
        with patch("agents.e01_stock_candidates.probe_item", side_effect=forged):
            report = run_probe(ROOT, "ffprobe", "ffmpeg")
        self.assertEqual(report["status"], "BLOCKED_PROBE_INCOMPLETE")
        self.assertEqual(report["source_media_bytes_verified"], 0)
        self.assertFalse(report["publication_authorized"])

    def test_no_real_download_claim_in_metadata_cli_report(self):
        with tempfile.TemporaryDirectory() as td:
            report_file = Path(td) / "report.json"
            from unittest.mock import patch
            with patch("sys.argv", ["intake", "--report", str(report_file)]):
                self.assertEqual(main(), 0)
            report = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "METADATA_VALID_RIGHTS_PENDING")
            self.assertEqual(report["source_media_bytes_verified"], 0)

if __name__ == "__main__":
    unittest.main()
