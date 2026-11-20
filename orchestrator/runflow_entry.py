"""Single production entry for Verbo no Chão: `episode_id` + `mode`.

Resolves the versioned pipeline spec, audits the workflow tree for spend/replay hazards, evaluates every
stage from physical evidence and, in preview mode, hands a provider package (if one physically exists) to the
legacy fail-closed Runflow. It never calls a provider, never spends, never publishes and never invents media.
Output is a sanitized JSON/Markdown report only (no media)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from orchestrator.pipeline import evaluate

PROJECT_ID = "verbo-no-chao"
EPISODE_RE = re.compile(r"^E[0-9]{2}$")
MODES = ("preflight", "preview")
ALLOWED_REPORT_SUFFIXES = {".json", ".md"}
PAID_HOSTS = ("api.elevenlabs.io", "api.openai.com", "api.anthropic.com")
# Único segredo extra permitido: link temporário de LEITURA da voz já gerada, só no workflow do master.
ALLOWED_SECRETS = {"verbo-no-chao-e01-master-run.yml": {"VNC_E01_AUDIO_URL"}}


def audit_workflows(root: Path) -> list[dict[str, str]]:
    """Static audit of .github/workflows. Findings with severity BLOCK stop every mode."""
    findings: list[dict[str, str]] = []
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        name = path.name
        if re.search(r"^\s*schedule\s*:", text, re.M) or "cron:" in text:
            findings.append({"file": name, "severity": "BLOCK", "rule": "schedule_trigger"})
        extra = sorted(set(re.findall(r"secrets\.([A-Za-z0-9_]+)", text)) - {"GITHUB_TOKEN"} - ALLOWED_SECRETS.get(name, set()))
        if extra:
            findings.append({"file": name, "severity": "BLOCK", "rule": "non_github_secret:" + ",".join(extra)})
        for host in PAID_HOSTS:
            if host in text:
                findings.append({"file": name, "severity": "BLOCK", "rule": f"paid_provider_host:{host}"})
        on_block = text.split("jobs:", 1)[0]
        if re.search(r"^\s{2}push\s*:", on_block, re.M) and not re.search(r"^\s{4}branches\s*:", on_block, re.M):
            findings.append({"file": name, "severity": "BLOCK", "rule": "push_without_branch_filter"})
    return findings


def _safe_workflow(root: Path, workflow: str | None) -> str:
    if not workflow:
        return "NO_AUTOMATED_EXECUTOR"
    path = (root / ".github" / "workflows" / workflow).resolve()
    try:
        path.relative_to((root / ".github" / "workflows").resolve())
        text = path.read_text(encoding="utf-8")
    except (ValueError, OSError):
        return "WORKFLOW_MISSING"
    if "RETIRED" in text or "offline guard only" in text:
        return "WORKFLOW_RETIRED"
    return "OK"


def resolve_spec(root: Path, episode_id: str) -> tuple[Path, dict[str, Any], str]:
    if not isinstance(episode_id, str) or not EPISODE_RE.match(episode_id):
        raise ValueError("episode_id:invalid (expected E01..E99)")
    low = episode_id.lower()
    for version in ("v3", "v2", "v1"):
        path = root / "contracts" / f"{low}_pipeline_{version}.json"
        if path.is_file():
            raw = path.read_bytes()
            return path, json.loads(raw), hashlib.sha256(raw).hexdigest()
    raise ValueError(f"spec:missing for {episode_id}")


def run_entry(root: Path, episode_id: str, mode: str, report_dir: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    env = dict(os.environ if env is None else env)
    if mode not in MODES:
        raise ValueError("mode:invalid (preflight|preview)")
    blockers: list[str] = []
    if env.get("VNC_BUDGET_NEW_SPEND", "0") not in ("0", "0.0", ""):
        blockers.append("budget_new_spend_must_be_zero")
    if env.get("VNC_PUBLICATION_AUTHORIZED", "false").lower() == "true":
        blockers.append("publication_must_not_be_enabled_in_runflow")
    spec_path, spec, spec_sha = resolve_spec(root, episode_id)
    findings = audit_workflows(root)
    blockers += [f"workflow_guard:{f['file']}:{f['rule']}" for f in findings if f["severity"] == "BLOCK"]
    pipe = evaluate(spec, root)
    stage_view = {}
    for sid, st in pipe["stages"].items():
        executor_state = _safe_workflow(root, st.get("workflow")) if st["status"] == "READY" else None
        stage_view[sid] = {
            "status": st["status"], "executor": st["executor"], "executor_state": executor_state,
            "unmet": st["unmet"], "evidence": st["evidence"], "evidence_sha256": st["evidence_sha256"],
            "idempotency_key": hashlib.sha256(f"{PROJECT_ID}|{episode_id}|{spec_sha}|{sid}|{st['evidence_sha256']}".encode()).hexdigest(),
        }
    nxt = pipe["next_stage"]
    next_action = None
    if nxt:
        st = stage_view[nxt]
        next_action = ("owner_authorization_required" if st["status"] == "HUMAN_ACTION"
                       else "blocked:" + (st["executor_state"] or "UNKNOWN"))
        if st["status"] == "READY" and st["executor_state"] == "OK":
            next_action = "run_workflow:" + spec["stages"][[s["id"] for s in spec["stages"]].index(nxt)]["workflow"]
    state = "BLOCKED"
    preview_note = None
    if mode == "preview":
        pkg = root / "episodes" / episode_id / "package" / "package.json"
        if not pkg.is_file():
            blockers.append("BLOCKED_NO_PHYSICAL_PACKAGE")
            preview_note = "no provider package materialized; nothing rendered, nothing invented"
        elif not blockers:
            from orchestrator.runflow import run_flow
            res = run_flow({"episode_id": episode_id, "spec_sha256": spec_sha}, pkg.parent, report_dir, render=True)
            state = res.state
            preview_note = f"legacy runflow status={res.status}"
            if res.status != "PASS":
                blockers += list(res.errors)
    report = {
        "project_id": PROJECT_ID, "episode_id": episode_id, "mode": mode, "spec": spec_path.relative_to(root).as_posix(),
        "spec_sha256": spec_sha, "state": state, "pipeline_state": pipe["state"], "next_stage": nxt, "next_action": next_action,
        "budget_new_spend_brl": 0, "publication_authorized": False, "published": False,
        "blockers": sorted(set(blockers)), "workflow_findings": findings, "stages": stage_view, "preview_note": preview_note,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "runflow_entry_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Runflow {episode_id} ({mode})", f"state: {state}", f"pipeline: {pipe['state']}", f"next: {nxt} -> {next_action}", "published: false", "spend: 0"]
    lines += [f"- {s}: {v['status']}" for s, v in stage_view.items()]
    lines += [f"BLOCKER {b}" for b in report["blockers"]]
    (report_dir / "runflow_entry_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    bad = [p.name for p in report_dir.iterdir() if p.suffix not in ALLOWED_REPORT_SUFFIXES]
    if bad:
        raise RuntimeError(f"report_dir:non_sanitized_files:{bad}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Verbo no Chão Runflow entry (episode_id + mode)")
    ap.add_argument("--episode-id", default="E01")
    ap.add_argument("--mode", default="preflight", choices=MODES)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--report-dir", type=Path, default=Path("run-reports"))
    a = ap.parse_args()
    rep = run_entry(a.root.resolve(), a.episode_id, a.mode, a.report_dir)
    print(json.dumps({k: rep[k] for k in ("episode_id", "mode", "state", "pipeline_state", "next_stage", "next_action", "blockers", "published")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
