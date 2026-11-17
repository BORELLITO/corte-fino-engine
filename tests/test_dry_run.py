import copy
import unittest

from orchestrator.dry_run import run_dry_run


def package():
    return {
        "run_id": "run-001",
        "editorial": {
            "video_id": "vnc-001",
            "audience": "pessoas em dificuldades",
            "theme": "espera",
            "opening": "Quando a espera parece abandono",
            "biblical_basis": {
                "reference": "Salmo 13",
                "translation": "tradução a confirmar",
                "context": "oração de lamento",
                "textual_basis": "o salmista apresenta sua angústia",
                "interpretation": "o lamento pode coexistir com a fé",
                "application": "nomear a dor sem abandonar a esperança",
                "certainty": "GROUNDED_INTERPRETATION",
                "safety": {}
            },
            "reflection": "A fé não exige fingir que está tudo bem.",
            "application": "Leve sua pergunta a Deus com honestidade.",
            "conclusion": "A espera não precisa ser atravessada sozinho.",
            "language": "pt-BR",
            "format": "short",
            "duration_seconds": 75,
            "originality": "ORIGINAL",
            "safety": {}
        },
        "rights": [
            {
                "asset_id": "asset-001",
                "source": "licensed-library",
                "license": "commercial-use",
                "commercial_use": True,
                "evidence_ref": "license-001",
                "status": "CLEARED"
            }
        ],
        "audiovisual": {
            "video_id": "vnc-001",
            "format": "vertical_short",
            "resolution": "1080x1920",
            "fps": 60,
            "scenes": [{
                "scene_id": "s01",
                "start_ms": 0,
                "end_ms": 75000,
                "narration_ref": "n01",
                "visual_intent": "esperança gradual",
                "relation": "symbolic",
                "rights_ref": "asset-001"
            }],
            "audio": {
                "voice": {
                    "source": "licensed-voice",
                    "language": "pt-BR",
                    "commercial_use": True,
                    "evidence_ref": "voice-001",
                    "intelligibility_status": "PASSED"
                },
                "music": {
                    "source": "licensed-instrumental",
                    "commercial_use": True,
                    "evidence_ref": "music-001",
                    "voice_priority": True,
                    "lyrics": "instrumental"
                }
            },
            "captions": {
                "language": "pt-BR",
                "max_lines": 2,
                "no_overlap": True,
                "segments": [{
                    "start_ms": 0,
                    "end_ms": 2000,
                    "text": "Quando a espera parece abandono"
                }]
            }
        }
    }


class DryRunTests(unittest.TestCase):
    def test_complete_package_passes(self):
        result = run_dry_run(package())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.state, "INTERNAL_VALIDATED")
        self.assertEqual(result.errors, ())

    def test_missing_rights_reference_blocks(self):
        payload = package()
        payload["audiovisual"]["scenes"][0]["rights_ref"] = "missing"
        result = run_dry_run(payload)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("rights:missing_reference:missing", result.errors)

    def test_publication_is_blocked(self):
        payload = package()
        payload["publication_requested"] = True
        result = run_dry_run(payload)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("publication:not_allowed_in_dry_run", result.errors)

    def test_input_is_not_mutated(self):
        payload = package()
        before = copy.deepcopy(payload)
        run_dry_run(payload)
        self.assertEqual(payload, before)


if __name__ == "__main__":
    unittest.main()
