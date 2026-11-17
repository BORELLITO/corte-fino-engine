import unittest

from editorial.validators import validate_editorial_package
from rights.validators import validate_rights_record


def valid_package():
    return {
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
    }


class EditorialValidationTests(unittest.TestCase):
    def test_valid_package_passes(self):
        self.assertEqual(validate_editorial_package(valid_package()), [])

    def test_missing_biblical_context_fails(self):
        payload = valid_package()
        payload["biblical_basis"]["context"] = ""
        self.assertIn("biblical_basis:context", validate_editorial_package(payload))

    def test_forbidden_religious_claim_fails(self):
        payload = valid_package()
        payload["safety"]["guaranteed_miracle"] = True
        self.assertIn(
            "editorial:forbidden_safety:guaranteed_miracle",
            validate_editorial_package(payload),
        )


class RightsValidationTests(unittest.TestCase):
    def test_cleared_commercial_asset_passes(self):
        record = {
            "asset_id": "asset-001",
            "source": "licensed-library",
            "license": "commercial-use",
            "commercial_use": True,
            "evidence_ref": "license-record-001",
            "attribution_required": False,
            "status": "CLEARED",
        }
        self.assertEqual(validate_rights_record(record), [])

    def test_unverified_asset_fails_closed(self):
        record = {
            "asset_id": "asset-002",
            "source": "unknown",
            "license": "",
            "commercial_use": False,
            "evidence_ref": "",
            "status": "UNREVIEWED",
        }
        errors = validate_rights_record(record)
        self.assertIn("rights:status", errors)
        self.assertIn("rights:commercial_use", errors)
        self.assertIn("rights:evidence_ref", errors)


if __name__ == "__main__":
    unittest.main()
