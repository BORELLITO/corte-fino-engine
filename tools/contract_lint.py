"""Structural lint for every versioned JSON contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    for path in sorted((root / "contracts").glob("*.schema.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path}: root must be object")
            continue
        if not isinstance(data.get("required"), list) or not data["required"]:
            errors.append(f"{path}: required must be a non-empty list")
        if not isinstance(data.get("properties"), dict):
            errors.append(f"{path}: properties must be an object")
        for key in data.get("required", []):
            if key not in data.get("properties", {}):
                errors.append(f"{path}: required field missing from properties: {key}")
    if errors:
        print("BLOCKED")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print("PASS: contract schemas are structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
