import unittest

from editorial.script_validator import validate_script_package


def valid_script():
    return {
        "script_id": "vnc-salmo-13-script-001",
        "status": "DRAFT_REVIEW_REQUIRED",
        "source_decision_ref": "contracts/pilot_source_decision.json",
        "source_mode": "reference_and_paraphrase",
        "contains_verbatim_quote": False,
        "duration_target_seconds": 75,
        "blocks": [
            {"type": "opening", "text": "Tem dias em que o silêncio parece uma resposta."},
            {"type": "connection", "text": "Você continua esperando, mas não sabe por quanto tempo."},
            {"type": "biblical_reference", "text": "O Salmo 13 nasce exatamente nesse lugar de espera e lamento."},
            {"type": "reflection", "text": "O salmista não esconde a dor; ele a leva para a presença de Deus."},
            {"type": "application", "text": "Nomear o que dói pode ser um ato de fé, não de desistência."},
            {"type": "conclusion", "text": "A espera continua sendo difícil, mas o silêncio não precisa ser o fim da esperança."}
        ]
    }


class ScriptPackageTests(unittest.TestCase):
    def test_valid_script_passes(self):
        self.assertEqual(validate_script_package(valid_script()), [])

    def test_literal_quote_is_blocked(self):
        payload = valid_script()
        payload["contains_verbatim_quote"] = True
        result = validate_script_package(payload)
        self.assertIn("script:contains_verbatim_quote", result)

    def test_missing_narrative_block_is_blocked(self):
        payload = valid_script()
        payload["blocks"] = payload["blocks"][:-1]
        result = validate_script_package(payload)
        self.assertIn("script:block_missing:conclusion", result)


if __name__ == "__main__":
    unittest.main()
