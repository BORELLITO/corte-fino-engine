import json
import unittest
from pathlib import Path

from orchestrator.state_machine import StateMachine


ROOT = Path(__file__).resolve().parents[1]


class StateMachineTests(unittest.TestCase):
    def test_contract_starts_clean(self):
        machine = StateMachine.from_contract(ROOT / "contracts/state_machine.json")
        self.assertEqual(machine.current, "CLEAN_BOOTSTRAP")

    def test_valid_progression(self):
        machine = StateMachine.from_contract(ROOT / "contracts/state_machine.json")
        machine = machine.transition("INTERNAL_VALIDATED")
        machine = machine.transition("RELEASE_CANDIDATE")
        self.assertEqual(machine.transition("STABLE").current, "STABLE")

    def test_invalid_skip_is_blocked(self):
        machine = StateMachine.from_contract(ROOT / "contracts/state_machine.json")
        with self.assertRaises(ValueError):
            machine.transition("STABLE")

    def test_contract_is_valid_json(self):
        payload = json.loads((ROOT / "contracts/state_machine.json").read_text(encoding="utf-8"))
        self.assertIn("transitions", payload)
        self.assertEqual(payload["initial"], "CLEAN_BOOTSTRAP")


if __name__ == "__main__":
    unittest.main()
