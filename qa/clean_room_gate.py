"""Static gate for the clean bootstrap tree."""

from __future__ import annotations

import argparse
from pathlib import Path

ALLOWED_ROOTS = {
    ".gitignore",
    "README.md",
    "analytics",
    "contracts",
    "delivery",
    "docs",
    "editorial",
    "media",
    "orchestrator",
    "qa",
    "rights",
    "tests",
}

FORBIDDEN_PATH_PARTS = {"creator", "publisher", "radar", "assets", "secrets"}


def violations(root: Path) -> list[str]:
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root)
        first = relative.parts[0]
        if first not in ALLOWED_ROOTS:
            result.append(f"outside-approved-root:{relative}")
        if path.name in {"main.py", "requirements.txt", "setup.py", "package.json"}:
            result.append(f"legacy-shaped-file:{relative}")
        if any(part in FORBIDDEN_PATH_PARTS for part in relative.parts):
            result.append(f"legacy-shaped-path:{relative}")
    readme = root / "README.md"
    if not readme.exists() or "Verbo no Chão" not in readme.read_text(encoding="utf-8"):
        result.append("identity-missing:README.md")
    return sorted(set(result))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    found = violations(Path(args.root).resolve())
    if found:
        for item in found:
            print(f"FAIL {item}")
        return 1
    print("PASS clean-room gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
