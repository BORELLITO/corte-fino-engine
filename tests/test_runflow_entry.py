import json
import shutil
from pathlib import Path

import pytest

from orchestrator.runflow_entry import audit_workflows, resolve_spec, run_entry

ROOT = Path(__file__).resolve().parents[1]


def _copy(tmp_path):
    shutil.copytree(ROOT / "contracts", tmp_path / "contracts")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    return tmp_path


def test_real_repo_preflight_is_blocked_and_never_published(tmp_path):
    rep = run_entry(ROOT, "E01", "preflight", tmp_path / "r", env={})
    assert rep["published"] is False and rep["publication_authorized"] is False
    assert rep["budget_new_spend_brl"] == 0
    assert rep["stages"]["publication"]["status"] != "DONE"
    assert rep["stages"]["voice_rights"]["status"] == "HUMAN_ACTION"
    assert rep["next_action"] == "owner_authorization_required"


def test_preview_without_package_is_blocked(tmp_path):
    rep = run_entry(ROOT, "E01", "preview", tmp_path / "r", env={})
    assert "BLOCKED_NO_PHYSICAL_PACKAGE" in rep["blockers"]
    assert rep["state"] == "BLOCKED"


@pytest.mark.parametrize("bad", ["../E01", "E1", "e01", "E01; rm", "", "E001", "E01/.."])
def test_episode_id_rejects_traversal_and_junk(bad):
    with pytest.raises(ValueError):
        resolve_spec(ROOT, bad)


def test_unknown_episode_has_no_spec():
    with pytest.raises(ValueError):
        resolve_spec(ROOT, "E99")


def test_invalid_mode(tmp_path):
    with pytest.raises(ValueError):
        run_entry(ROOT, "E01", "publish", tmp_path / "r", env={})


def test_spend_and_publication_flags_block(tmp_path):
    rep = run_entry(ROOT, "E01", "preflight", tmp_path / "r", env={"VNC_BUDGET_NEW_SPEND": "5", "VNC_PUBLICATION_AUTHORIZED": "true"})
    assert "budget_new_spend_must_be_zero" in rep["blockers"]
    assert "publication_must_not_be_enabled_in_runflow" in rep["blockers"]


def test_idempotency_key_stable_and_changes_with_evidence(tmp_path):
    a = run_entry(ROOT, "E01", "preflight", tmp_path / "a", env={})
    b = run_entry(ROOT, "E01", "preflight", tmp_path / "b", env={})
    assert a["stages"]["script"]["idempotency_key"] == b["stages"]["script"]["idempotency_key"]
    assert a["stages"]["script"]["idempotency_key"] != a["stages"]["voice_measured"]["idempotency_key"]


def test_workflow_audit_flags_schedule_secret_paid_host_and_unfiltered_push(tmp_path):
    root = _copy(tmp_path)
    wf = root / ".github" / "workflows"
    (wf / "a.yml").write_text("on:\n  schedule:\n    - cron: '0 * * * *'\njobs:\n  x:\n    steps: []\n")
    (wf / "b.yml").write_text("on:\n  workflow_dispatch:\njobs:\n  x:\n    env:\n      K: ${{ secrets.ELEVENLABS_API_KEY }}\n")
    (wf / "c.yml").write_text("on:\n  workflow_dispatch:\njobs:\n  x:\n    run: curl https://api.elevenlabs.io/v1\n")
    (wf / "d.yml").write_text("on:\n  push:\n    paths: ['x']\njobs:\n  x:\n    steps: []\n")
    (wf / "e.yml").write_text("on:\n  push:\n    branches: ['a']\njobs:\n  x:\n    env:\n      T: ${{ secrets.GITHUB_TOKEN }}\n")
    rules = {(f["file"], f["rule"].split(":")[0]) for f in audit_workflows(root)}
    assert ("a.yml", "schedule_trigger") in rules
    assert ("b.yml", "non_github_secret") in rules
    assert ("c.yml", "paid_provider_host") in rules
    assert ("d.yml", "push_without_branch_filter") in rules
    assert not any(f == "e.yml" for f, _ in rules)


def test_guard_blocks_when_workflow_hazard_present(tmp_path):
    root = _copy(tmp_path / "r")
    (root / ".github" / "workflows" / "bad.yml").write_text("on:\n  schedule:\n    - cron: '0 * * * *'\njobs: {}\n")
    shutil.copy(ROOT / "orchestrator" / "__init__.py", root / "x.py") if False else None
    rep = run_entry(root, "E01", "preflight", tmp_path / "rep", env={})
    assert any(b.startswith("workflow_guard:bad.yml") for b in rep["blockers"])


def test_report_dir_contains_only_json_and_md(tmp_path):
    run_entry(ROOT, "E01", "preflight", tmp_path / "r", env={})
    assert {p.suffix for p in (tmp_path / "r").iterdir()} <= {".json", ".md"}


def test_pipeline_never_names_missing_workflow():
    from orchestrator.pipeline import evaluate
    spec = json.loads((ROOT / "contracts" / "e01_pipeline_v3.json").read_text())
    out = evaluate(spec, ROOT)
    assert out["stages"]["clips_approved"]["status"] == "READY"
    assert out["next_action"] != "run_workflow:None"


def test_master_requires_voice_and_clip_rights():
    spec = json.loads((ROOT / "contracts" / "e01_pipeline_v3.json").read_text())
    master = next(s for s in spec["stages"] if s["id"] == "master")
    assert {"clips_rights", "voice_rights"} <= set(master["requires"])
    pub = next(s for s in spec["stages"] if s["id"] == "publication")
    assert pub["executor"] == "human_only"
