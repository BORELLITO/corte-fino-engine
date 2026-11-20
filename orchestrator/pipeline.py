"""Episode pipeline driver: reads evidence contracts and decides what happens next.

Fail-closed and read-only. It never edits evidence and never reports PUBLISHED.
A stage is DONE only if its evidence file parses and satisfies every condition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
DONE, READY, WAITING, HUMAN = "DONE", "READY", "WAITING", "HUMAN_ACTION"


def _check(value: Any, cond: dict[str, Any]) -> bool:
    if "equals" in cond:
        # `True == 1` in Python; require identical type so 1 never satisfies true.
        return type(value) is type(cond["equals"]) and value == cond["equals"]
    if cond.get("is_sha256"):
        return isinstance(value, str) and bool(_SHA256.match(value))
    return False  # unknown condition type: fail closed


def _load(root: Path, rel: str) -> tuple[dict[str, Any] | None, str | None, str | None]:
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
        raw = path.read_bytes()
        data = json.loads(raw)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return None, None, f"evidence_unreadable:{rel}:{type(exc).__name__}"
    if not isinstance(data, dict):
        return None, None, f"evidence_not_object:{rel}"
    return data, hashlib.sha256(raw).hexdigest(), None


def evaluate(pipeline: dict[str, Any], root: Path) -> dict[str, Any]:
    stages = pipeline.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("pipeline:stages_missing")
    ids = [s.get("id") for s in stages]
    if len(set(ids)) != len(ids):
        raise ValueError("pipeline:duplicate_stage_id")
    results: dict[str, dict[str, Any]] = {}
    for stage in stages:  # contract order must already be topological
        sid = stage["id"]
        unknown = [r for r in stage.get("requires", []) if r not in results]
        if unknown:
            raise ValueError(f"pipeline:{sid}:requires_unknown_or_later:{unknown}")
        data, digest, err = _load(root, stage["evidence"])
        unmet: list[str] = [err] if err else []
        if data is not None:
            for cond in stage.get("done_when", []):
                field = cond.get("field")
                if field not in data or not _check(data[field], cond):
                    unmet.append(f"{field}:expected:{cond.get('equals', 'sha256')}")
        if not stage.get("done_when"):
            unmet.append("no_done_condition_declared")
        blocked_by = [r for r in stage.get("requires", []) if results[r]["status"] != DONE]
        if not unmet and not blocked_by:
            status = DONE
        elif blocked_by:
            status = WAITING
        elif stage.get("executor") == "human_only":
            status = HUMAN
        else:
            status = READY
        results[sid] = {
            "status": status,
            "executor": stage.get("executor"),
            "workflow": stage.get("workflow"),
            "evidence": stage["evidence"],
            "evidence_sha256": digest,
            "unmet": unmet,
            "waiting_on": blocked_by,
        }
    actionable = [(s, r) for s, r in results.items() if r["status"] in (READY, HUMAN)]
    nxt = actionable[0] if actionable else None
    all_done = all(r["status"] == DONE for r in results.values())
    return {
        "pipeline_id": pipeline.get("pipeline_id"),
        "episode_id": pipeline.get("episode_id"),
        "state": "AWAITING_PUBLICATION" if all_done else "BLOCKED",
        "next_stage": nxt[0] if nxt else None,
        "next_action": (
            None if not nxt else
            "owner_authorization_required" if nxt[1]["status"] == HUMAN else
            f"run_workflow:{nxt[1]['workflow']}" if nxt[1].get("workflow") else "no_automated_executor"
        ),
        "stages": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate the episode pipeline from evidence")
    ap.add_argument("--pipeline", type=Path, default=Path("contracts/e01_pipeline_v1.json"))
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    report = evaluate(json.loads(args.pipeline.read_text(encoding="utf-8")), args.root)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
