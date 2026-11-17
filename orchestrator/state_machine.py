"""State transitions for the Verbo no Chão engine foundation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StateMachine:
    transitions: dict[str, tuple[str, ...]]
    current: str

    @classmethod
    def from_contract(cls, contract_path: Path) -> "StateMachine":
        data = json.loads(contract_path.read_text(encoding="utf-8"))
        transitions = {
            state: tuple(next_states)
            for state, next_states in data["transitions"].items()
        }
        initial = data["initial"]
        if initial not in transitions:
            raise ValueError("Initial state is not declared")
        return cls(transitions=transitions, current=initial)

    def can_transition(self, next_state: str) -> bool:
        return next_state in self.transitions.get(self.current, ())

    def transition(self, next_state: str) -> "StateMachine":
        if not self.can_transition(next_state):
            raise ValueError(f"Invalid transition: {self.current} -> {next_state}")
        return StateMachine(self.transitions, next_state)
