"""Load protected editorial rejections so a rejected source can never be re-picked."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _walk(node: Any, found: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, (int, str)) and key == "id" and str(value).isdigit():
                found.update({str(value), f"pexels-{value}"})  # over-exclusion is harmless
            elif isinstance(value, str) and (HEX64.match(value) or value.startswith("https://")) \
                    and key in {"sha256", "source_hash", "source_url", "url", "page_url"}:
                found.add(value)
            elif isinstance(value, str) and key in {"asset_id", "source_id"}:
                found.add(value)
            _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)


def load_rejections(contracts_dir: Path) -> set[str]:
    """Union of ids, URLs and SHA-256 found in every *rejections*.json contract."""
    found: set[str] = set()
    for path in sorted(contracts_dir.glob("*rejection*.json")):
        try:
            _walk(json.loads(path.read_text(encoding="utf-8")), found)
        except (OSError, json.JSONDecodeError):
            raise  # an unreadable rejection list must block, never be skipped
    return found
