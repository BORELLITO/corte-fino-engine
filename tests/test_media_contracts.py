import unittest

from media.validators import validate_audiovisual_package


def valid_package():
    return {
        "video_id": "vnc-001",
        "format": "vertical_short",
        "resolution": "1080x1920",
        "fps": 60,
        "scenes": [
            {
                "scene_id": "s01",
                "start_ms": 0,
                "end_ms": 3500,
                "narration_ref": "n01",
                "visual_intent": "solidão e espera",
                "relation": "atmospheric",
                "rights_ref": "asset-001"
            },
            {
                "scene_id": "s02",
                "start_ms": 3500,
                "end_ms": 75000,
                "narration_ref": "n02",
                "visual_intent": "esperança gradual",
                "relation": "symbolic",
                "rights_ref": "asset-002"
            }
        ],
        "audio": {
            "voice": {
                "source": "licensed-voice",
                "language": "pt-BR",
                "commercial_use": True,
                "evidence_ref": "voice-rights-001",
                "intelligibility_status": "PASSED"
            },
            "music": {
                "source": "licensed-instrumental",
                "commercial_use": True,
                "evidence_ref": "music-rights-001",
                "voice_priority": True,
                "lyrics": "instrumental"
            }
        },
        "captions": {
            "language": "pt-BR",
            "max_lines": 2,
            "no_overlap": True,
            "segments": [
                {"start_ms": 0, "end_ms": 1600, "text": "Quando a espera parece abandono"},
                {"start_ms": 1600, "end_ms": 3500, "text": "a dor ainda pode ser dita"}
            ]
        }
    }


class MediaContractTests(unittest.TestCase):
    def test_valid_package_passes(self):
        self.assertEqual(validate_audiovisual_package(valid_package()), [])

    def test_scene_overlap_fails(self):
        payload = valid_package()
        payload["scenes"][1]["start_ms"] = 3000
        self.assertIn("scene:1:overlap", validate_audiovisual_package(payload))

    def test_unlicensed_voice_fails(self):
        payload = valid_package()
        payload["audio"]["voice"]["commercial_use"] = False
        self.assertIn("voice:commercial_use", validate_audiovisual_package(payload))

    def test_caption_with_three_lines_fails(self):
        payload = valid_package()
        payload["captions"]["segments"][0]["text"] = "linha 1\nlinha 2\nlinha 3"
        self.assertIn("caption:0:max_lines", validate_audiovisual_package(payload))


if __name__ == "__main__":
    unittest.main()
