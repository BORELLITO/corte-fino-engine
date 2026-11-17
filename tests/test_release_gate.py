import json
import unittest
from pathlib import Path

from qa.release_gate import validate_release_candidate


FIXTURE = Path(__file__).parent / "fixtures" / "salmo_13_dry_run.json"


def promoted_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["fixture_mode"] = False
    payload["release_candidate_id"] = "rc-salmo-13-001"
    basis = payload["editorial"]["biblical_basis"]
    basis["translation"] = "validated-translation-source"
    basis["source_ref"] = "validated-biblical-source"
    rights = payload["rights"][0]
    rights.update({
        "source": "licensed-library",
        "license": "commercial-use",
        "commercial_use": True,
        "evidence_ref": "verified-license-record",
        "status": "CLEARED"
    })
    voice = payload["audiovisual"]["audio"]["voice"]
    voice.update({
        "source": "licensed-voice",
        "commercial_use": True,
        "evidence_ref": "verified-voice-record"
    })
    music = payload["audiovisual"]["audio"]["music"]
    music.update({
        "source": "licensed-instrumental",
        "commercial_use": True,
        "evidence_ref": "verified-music-record"
    })
    return payload


class ReleaseGateTests(unittest.TestCase):
    def test_fixture_is_no_go(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = validate_release_candidate(payload)
        self.assertEqual(result.status, "NO_GO")
        self.assertIn("release:fixture_mode", result.errors)

    def test_promoted_structure_passes(self):
        result = validate_release_candidate(promoted_fixture())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.errors, ())

    def test_pending_translation_is_no_go(self):
        payload = promoted_fixture()
        payload["editorial"]["biblical_basis"]["translation"] = "confirmar antes da publicação"
        result = validate_release_candidate(payload)
        self.assertEqual(result.status, "NO_GO")
        self.assertIn("release:translation", result.errors)

    def test_fixture_rights_cannot_pass_as_release(self):
        payload = promoted_fixture()
        payload["rights"][0]["status"] = "FIXTURE_ONLY"
        payload["rights"][0]["commercial_use"] = False
        result = validate_release_candidate(payload)
        self.assertEqual(result.status, "NO_GO")
        self.assertTrue(any("rights:status" in item for item in result.errors))


if __name__ == "__main__":
    unittest.main()
