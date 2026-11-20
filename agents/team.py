"""Eight bounded, read-only specialist audits and their evidence coordinator.

Not eight persistent AI models. No external API calls, publication or cost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_IDS = (
    "niche_strategy", "growth_90d", "idea_research", "retention_script",
    "titles_covers", "shorts_production", "performance", "monetization",
)


def _read(root: Path, rel: str, evidence: dict[str, str]) -> Any:
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"evidence_missing:{rel}")
    raw = path.read_bytes()
    evidence[rel] = hashlib.sha256(raw).hexdigest()
    if rel.endswith(".json"):
        return json.loads(raw)
    return raw.decode("utf-8")


def _require(condition: bool, why: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(why)


def _governance(root: Path, evidence: dict[str, str], blockers: list[str]) -> None:
    policy = _read(root, "docs/CLEAN_ROOM_POLICY.md", evidence)
    lock = _read(root, "docs/ENGINE_LOCK.md", evidence)
    _require("Estado: `APPROVED`" in policy, "clean_room_policy_not_approved", blockers)
    _require("A branch operacional atual verificada" in lock and
             "`verbo-no-chao/e01-stock-curation-gate-v1`" in lock,\n             "canonical_branch_not_recorded", blockers)
    _require("publication_authorized" in lock, "publication_lock_missing", blockers)


def _audit_role(agent: str, root: Path, evidence: dict[str, str], blockers: list[str], limitations: list[str]) -> None:
    if agent == "niche_strategy":
        _governance(root, evidence, blockers)
        try:
            strategy = _read(root, "operations/niche_strategy.json", evidence)
            _require(strategy.get("project") == "verbo-no-chao", "strategy_project_invalid", blockers)
            for key in ("audience", "editorial_promise", "differentiator", "evidence_refs"):
                _require(bool(strategy.get(key)), f"strategy_missing:{key}", blockers)
            source = _read(root, "agents/editorial_seed.json", evidence)
            _require(strategy.get("approval_status") == "DRAFT_REVIEW_REQUIRED",
                     "strategy_must_remain_review_required", blockers)
            _require(strategy.get("publication_authorized") is False and
                     strategy.get("owner_approval") is False,
                     "strategy_unapproved_publication_or_owner_claim", blockers)
            _require(strategy.get("editorial_promise") ==
                     source["approval_scope"]["editorial_promise"]["value"],
                     "strategy_promise_differs_from_approved", blockers)
            _require(strategy.get("audience", {}).get("primary") ==
                     source["approval_scope"]["primary_audience"]["value"],
                     "strategy_primary_audience_differs", blockers)
            _require(strategy.get("evidence_sha256", {}).get("agents/editorial_seed.json") ==
                     evidence["agents/editorial_seed.json"], "strategy_source_hash_mismatch", blockers)
            _require(isinstance(strategy.get("content_pillars"), list) and
                     len(strategy["content_pillars"]) >= 3,
                     "strategy_pillars_missing", blockers)
        except (ValueError, KeyError, TypeError):
            blockers.append("niche_strategy_not_documented_or_invalid:operations/niche_strategy.json")
        limitations.append("Strategy is a generated proposal based on approved positioning, not live market research or an approved content launch")

    elif agent == "growth_90d":
        try:
            plan = _read(root, "operations/growth_90d.json", evidence)
            _require(plan.get("project") == "verbo-no-chao", "growth_project_invalid", blockers)
            for key in ("start_date", "cadence", "milestones", "assumptions"):
                _require(bool(plan.get(key)), f"growth_missing:{key}", blockers)
            _require(isinstance(plan.get("milestones"), list) and len(plan["milestones"]) >= 3,
                     "growth_milestones_insufficient", blockers)
            source = _read(root, "agents/editorial_seed.json", evidence)
            _require(plan.get("approval_status") == "DRAFT_REVIEW_REQUIRED" and
                     plan.get("start_date") == "NOT_SCHEDULED",
                     "growth_cannot_schedule_or_auto_approve", blockers)
            _require(plan.get("publication_authorized") is False and
                     plan.get("owner_approval") is False,
                     "growth_unapproved_publication_or_owner_claim", blockers)
            _require(plan.get("window_days") == 90 and
                     plan.get("ideas_count") == 39,
                     "growth_window_or_count_mismatch", blockers)
            _require(plan.get("cadence", {}).get("status") == "HYPOTHESIS_NOT_APPROVED" and
                     plan.get("cadence", {}).get("publish_automatically") is False,
                     "growth_cadence_not_review_only", blockers)
            episodes = plan.get("episodes")
            _require(isinstance(episodes, list) and len(episodes) == 39,
                     "growth_missing_39_episode_briefs", blockers)
            if isinstance(episodes, list):
                days = [e.get("relative_day") for e in episodes if isinstance(e, dict)]
                ref_ids = [e.get("scripture_reference") for e in episodes if isinstance(e, dict)]
                _require(len(days) == 39 and len(set(days)) == 39 and min(days, default=0) == 1 and
                         max(days, default=0) == 90,
                         "growth_invalid_relative_calendar", blockers)
                _require(len(ref_ids) == 39 and len(set(ref_ids)) == 39 and
                         "Salmo 13" not in ref_ids,
                         "growth_duplicate_or_pilot_reference", blockers)
                _require(all(e.get("publication_authorized") is False and
                             e.get("script_status") == "IDEA_ONLY_REQUIRES_CONTEXT_AND_SCRIPT_REVIEW"
                             for e in episodes if isinstance(e, dict)),
                         "growth_episode_approval_inflation", blockers)
            _require(plan.get("evidence_sha256", {}).get("agents/editorial_seed.json") ==
                     evidence["agents/editorial_seed.json"], "growth_source_hash_mismatch", blockers)
        except (ValueError, KeyError, TypeError):
            blockers.append("growth_plan_not_documented_or_invalid:operations/growth_90d.json")
        limitations.append("Cadence and all 39 ideas remain proposals; no verified views, audience analytics or publication dates")

    elif agent == "idea_research":
        decision = _read(root, "contracts/pilot_source_decision.json", evidence)
        manifest = _read(root, "contracts/pilot_salmo_13_master.json", evidence)
        _read(root, "docs/PILOT_SALMO_13_SOURCE_AUDIT.md", evidence)
        _require(isinstance(decision, dict), "source_decision_invalid", blockers)
        assets = manifest.get("assets", [])
        _require(isinstance(assets, list) and bool(assets), "research_assets_missing", blockers)
        if isinstance(assets, list):
            urls = [item.get("source_url") for item in assets if isinstance(item, dict)]
            _require(len(urls) == len(assets), "research_asset_invalid", blockers)
            _require(all(isinstance(url, str) and url.startswith("https://") for url in urls),
                     "research_provenance_missing", blockers)
            _require(len(set(urls)) == len(urls), "research_duplicate_source", blockers)
        # The research specialist also inspects the actual new-script source briefs.
        batch = _read(root, "operations/first_batch_scripts.json", evidence)
        source_policy = _read(root, "contracts/new_script_source_policy.json", evidence)
        _require(batch.get("status") == "DRAFT_REVIEW_REQUIRED",
                 "research_script_batch_must_require_review", blockers)
        _require(source_policy.get("biblical_review_required") is True,
                 "research_biblical_review_policy_missing", blockers)
        scripts = batch.get("scripts")
        _require(isinstance(scripts, list) and len(scripts) == 3,
                 "research_first_three_scripts_missing", blockers)
        if isinstance(scripts, list):
            for i, script in enumerate(scripts, 1):
                if not isinstance(script, dict):
                    blockers.append("research_script_not_object")
                    continue
                context = script.get("biblical_context")
                sources = script.get("research_sources")
                _require(isinstance(context, dict) and
                         context.get("theological_status") == "CONTEXT_REVIEW_REQUIRED" and
                         all(bool(context.get(key)) for key in
                             ("historical_setting", "central_reading", "application_limit", "misreading_to_avoid")),
                         f"research_weak_or_unreviewed_context:{i}", blockers)
                _require(isinstance(sources, list) and len(sources) >= 2 and
                         all(isinstance(item, dict) and
                             isinstance(item.get("url"), str) and
                             item["url"].startswith("https://") and
                             bool(item.get("note")) for item in sources),
                         f"research_source_notes_missing:{i}", blockers)
                _require(script.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW",
                         f"research_invalid_biblical_review_state:{i}", blockers)
        limitations.append("References are documented, not live-fetched or independently endorsed; exegesis and rights need human review")
        limitations.append("No independent proof of visual suitability, third-party rights or Bible translation license")

    elif agent == "retention_script":
        from editorial.review import review_script
        from editorial.script_validator import validate_script_package
        script = _read(root, "tests/fixtures/salmo_13_script.json", evidence)
        source_ref = script.get("source_decision_ref") if isinstance(script, dict) else None
        if isinstance(source_ref, str):
            _read(root, source_ref, evidence)
        else:
            blockers.append("script_source_ref_missing")
        blockers.extend(validate_script_package(script))
        review = review_script(script)
        _require(review.status == "PASS_AUTOMATED_REVIEW", "script_automated_review_failed", blockers)
        blockers.extend(review.errors)
        batch = _read(root, "operations/first_batch_scripts.json", evidence)
        new_policy = _read(root, "contracts/new_script_source_policy.json", evidence)
        _require(new_policy.get("source_mode") == "reference_and_paraphrase",
                 "script_new_source_policy_invalid", blockers)
        scripts = batch.get("scripts")
        _require(batch.get("status") == "DRAFT_REVIEW_REQUIRED" and
                 batch.get("publication_authorized") is False and
                 isinstance(scripts, list) and len(scripts) == 3,
                 "script_first_batch_not_review_only", blockers)
        if isinstance(scripts, list):
            for i, draft in enumerate(scripts, 1):
                if not isinstance(draft, dict):
                    blockers.append(f"script_draft_not_object:{i}")
                    continue
                blockers.extend(
                    f"script_new_{i}:{error}" for error in validate_script_package(draft)
                )
                verdict = review_script(draft)
                blockers.extend(f"script_new_{i}:{error}" for error in verdict.errors)
                _require(verdict.status == "PASS_AUTOMATED_REVIEW" and
                         draft.get("status") == "DRAFT_REVIEW_REQUIRED" and
                         draft.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW" and
                         draft.get("owner_approval") is False and
                         draft.get("publication_authorized") is False,
                         f"script_new_{i}:approval_or_review_invalid", blockers)
        limitations.append("Drafts passed deterministic review only; no audio, rights, or theological human approval")
        limitations.append("Automated narrative structure cannot prove actual audience retention")

    elif agent == "titles_covers":
        try:
            package = _read(root, "operations/titles_covers.json", evidence)
            titles = package.get("titles") if isinstance(package, dict) else None
            _require(isinstance(titles, list) and len(titles) >= 2 and all(isinstance(t, str) and t.strip() for t in titles),
                     "title_options_missing", blockers)
            _require(bool(package.get("cover_brief")), "cover_brief_missing", blockers)
            _require(bool(package.get("script_ref")), "title_script_reference_missing", blockers)
        except ValueError:
            blockers.append("title_package_not_documented:operations/titles_covers.json")
        limitations.append("A title/cover brief does not prove an actual rendered, rights-cleared thumbnail")

    elif agent == "shorts_production":
        from engine.quality_gates import validate_manifest
        manifest = _read(root, "contracts/pilot_salmo_13_master.json", evidence)
        blockers.extend(f"manifest:{e}" for e in validate_manifest(manifest))
        _require(manifest.get("publication_authorized") is False, "pilot_publication_not_locked", blockers)
        blockers.append("physical_master_and_audio_not_available_to_ci")
        limitations.append("Historical declared SHA-256 and PASS labels do not prove media decode or perceptual quality")

    elif agent == "performance":
        try:
            metrics = _read(root, "operations/metrics_snapshot.json", evidence)
            _require(metrics.get("project") == "verbo-no-chao", "metrics_project_invalid", blockers)
            for key in ("platform", "collected_at", "source", "video_metrics"):
                _require(bool(metrics.get(key)), f"metrics_missing:{key}", blockers)
            _require(isinstance(metrics.get("video_metrics"), list) and bool(metrics["video_metrics"]),
                     "metrics_need_real_videos", blockers)
        except ValueError:
            blockers.append("real_metrics_not_available:operations/metrics_snapshot.json")
        limitations.append("Never fabricate views, retention, subscriber counts or benchmarks")

    elif agent == "monetization":
        manifest = _read(root, "contracts/pilot_salmo_13_master.json", evidence)
        _read(root, "docs/PILOT_SALMO_13_RIGHTS_LEDGER.md", evidence)
        rights = manifest.get("rights") or {}
        for key in ("visual_review", "voice_review", "music_review", "monetization"):
            _require(rights.get(key) in {"CLEARED", "PASS"}, f"rights_not_cleared:{key}", blockers)
        for item in manifest.get("assets", []):
            _require(item.get("rights_status") in {"CLEARED", "PASS"},
                     f"asset_rights_pending:{item.get('asset_id', 'unknown')}", blockers)
        _require(manifest.get("publication_authorized") is False, "unsafe_publication_flag", blockers)
        limitations.append("Rights labels need actual license evidence and human review; never authorize publication")

    else:
        raise ValueError(f"agent_unknown:{agent}")


def run_agent(agent: str, root: Path) -> dict[str, Any]:
    root = root.resolve()
    evidence: dict[str, str] = {}
    registry = _read(root, "agents/registry.json", evidence)
    agents = registry.get("agents", [])
    ids = [item.get("id") for item in agents]
    if ids != list(CANONICAL_IDS) or registry.get("project") != "verbo-no-chao" or registry.get("default_publication_authorized") is not False:
        raise ValueError("agent_registry_contract_mismatch")
    if agent not in ids:
        raise ValueError(f"agent_unknown:{agent}")
    blockers: list[str] = []
    limitations: list[str] = []
    try:
        _audit_role(agent, root, evidence, blockers, limitations)
    except (FileNotFoundError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        blockers.append(f"evidence_or_contract_error:{type(exc).__name__}:{exc}")
    return {
        "schema_version": "1.0.0", "project": "verbo-no-chao", "mode": "read_only_ci_audit",
        "agent": agent, "title": agents[ids.index(agent)]["title"],
        "status": "BLOCKED" if blockers else "PASS_CHECKED_SCOPE",
        "blockers": sorted(set(blockers)), "limitations": limitations,
        "evidence_sha256": evidence, "publication_authorized": False,
        "commit_sha": os.environ.get("GITHUB_SHA", "local-unverified"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def aggregate(input_dir: Path, audio_preflight_path: Path | None = None) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for path in sorted(input_dir.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        aid = payload.get("agent")
        if aid not in CANONICAL_IDS or aid in found:
            raise ValueError(f"unexpected_or_duplicate_agent_report:{aid}")
        if payload.get("project") != "verbo-no-chao" or payload.get("publication_authorized") is not False:
            raise ValueError(f"unsafe_agent_report:{aid}")
        if payload.get("status") not in {"BLOCKED", "PASS_CHECKED_SCOPE"}:
            raise ValueError(f"invalid_status:{aid}")
        if payload.get("status") == "BLOCKED" and not payload.get("blockers"):
            raise ValueError(f"blocked_without_reason:{aid}")
        found[aid] = payload
    if set(found) != set(CANONICAL_IDS):
        raise ValueError(f"missing_agent_reports:{sorted(set(CANONICAL_IDS) - set(found))}")
    statuses = {aid: found[aid]["status"] for aid in CANONICAL_IDS}
    audio_status: dict[str, Any] | None = None
    if audio_preflight_path is not None:
        raw = audio_preflight_path.read_bytes()
        preflight = json.loads(raw)
        if not isinstance(preflight, dict):
            raise ValueError("invalid_audio_preflight_report")
        if (
            preflight.get("project") != "verbo-no-chao"
            or preflight.get("episode_id") != "VNC-W01-E1"
            or preflight.get("stage") != "AUDIO_PREFLIGHT_ONLY"
            or preflight.get("status") != "BLOCKED"
            or preflight.get("voice_license_approved") is not False
            or preflight.get("ai_editorial_review_verified") is not True
            or preflight.get("video_readiness_status") != "BLOCKED_PHYSICAL_MEDIA_AND_RIGHTS_NOT_PROVEN"
            or preflight.get("final_video_qa_completed") is not False
            or preflight.get("owner_finished_video_review_required") is not False
            or preflight.get("ai_editorial_script_approved") is not True
            or preflight.get("ai_editorial_review_status") != "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION"
            or preflight.get("owner_script_review_required") is not False
            or preflight.get("human_theological_review_required_for_script") is not False
            or preflight.get("rights_review_handoff_generated") is not True
            or preflight.get("rights_review_handoff_status") != "REVIEW_PACKET_READY_NOT_APPROVED"
            or preflight.get("historical_smoke_evidence_verified") is not True
            or preflight.get("historical_smoke_source_report_sha256") !=
               "1b83c7dcdcf11c18241d20c572b72db286b3c4a1a38cdae45dc8ffa5acf9af37"
            or preflight.get("internal_context_crosscheck_completed") is not True
            or preflight.get("human_theological_review_pending") is not True
            or preflight.get("audio_generated") is not False
            or preflight.get("publication_authorized") is not False
            or not isinstance(preflight.get("blockers"), list)
            or not preflight["blockers"]
        ):
            raise ValueError("audio_preflight_failed_closed_contract")
        # Verify actual downloaded artifacts, not just the summary's claims.
        # GitHub Actions places report.json and all supporting files under
        # audio-preflight/. A green coordinator must prove byte-level integrity.
        required_files = {
            "audio-preflight/preflight.json",
            "audio-preflight/preflight.md",
            "audio-preflight/context_crosscheck.json",
            "audio-preflight/historical_smoke.json",
            "audio-preflight/rights_review_handoff.json",
            "audio-preflight/e01_human_review_packet.md",
            "audio-preflight/ai_editorial_approval.json",
            "audio-preflight/video_pillar_readiness.json",
        }
        file_specs = preflight.get("files")
        if not isinstance(file_specs, list) or len(file_specs) != len(required_files):
            raise ValueError("audio_preflight_missing_hashed_files")
        paths = [x.get("path") if isinstance(x, dict) else None for x in file_specs]
        if set(paths) != required_files or len(set(paths)) != len(paths):
            raise ValueError("audio_preflight_missing_hashed_files")
        artifact_root = audio_preflight_path.resolve().parent.parent
        verified_paths: dict[str, str] = {}
        for item in file_specs:
            name = item["path"]
            expected = item.get("sha256")
            if (not isinstance(expected, str) or len(expected) != 64 or
                    any(c not in "0123456789abcdef" for c in expected)):
                raise ValueError("audio_preflight_bad_file_digest")
            full_path = (artifact_root / name).resolve()
            if not full_path.is_relative_to(artifact_root) or not full_path.is_file():
                raise ValueError("audio_preflight_artifact_missing")
            if full_path.stat().st_size > 250000:
                raise ValueError("audio_preflight_artifact_oversize")
            actual = hashlib.sha256(full_path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError("audio_preflight_artifact_hash_mismatch")
            verified_paths[name] = actual
        from agents.video_pillar_readiness import validate_video_pillar_report
        pillar_report = json.loads((artifact_root / "audio-preflight/video_pillar_readiness.json").read_bytes())
        validate_video_pillar_report(pillar_report)
        audio_status = {
            "supporting_file_hashes_verified": True,
            "twelve_pillar_video_readiness": pillar_report["status"],
            "owner_finished_video_review_required": False,
            "final_video_qa_completed": False,
            "supporting_file_count": len(verified_paths),
            "ai_editorial_approval_sha256": verified_paths["audio-preflight/ai_editorial_approval.json"],
            "ai_editorial_script_approved": True,
            "owner_script_review_required": False,
            "human_theological_review_required_for_script": False,
            "human_review_packet_sha256": verified_paths["audio-preflight/e01_human_review_packet.md"],
            "status": "BLOCKED",
            "report_sha256": hashlib.sha256(raw).hexdigest(),
            "blockers": preflight["blockers"],
            "voice_license_approved": False,
            "rights_review_handoff_generated": True,
            "rights_review_handoff_status": "REVIEW_PACKET_READY_NOT_APPROVED",
            "historical_smoke_evidence_verified": True,
            "historical_smoke_source_report_sha256":
                "1b83c7dcdcf11c18241d20c572b72db286b3c4a1a38cdae45dc8ffa5acf9af37",
            "internal_context_crosscheck_completed": True,
            "human_theological_review_pending": True,
            "audio_generated": False,
        }
    return {
        "schema_version": "1.0.0", "project": "verbo-no-chao", "coordinator": "specialist-evidence-collector",
        "status": "BLOCKED" if audio_status is not None or any(v == "BLOCKED" for v in statuses.values()) else "CHECKS_PASSED_NOT_PUBLICATION_APPROVED",
        "agents_executed": len(found),
        "agents_passed_scope": sum(v == "PASS_CHECKED_SCOPE" for v in statuses.values()),
        "agents_blocked": sum(v == "BLOCKED" for v in statuses.values()),
        "audio_preflight": audio_status,
        "reports": [found[aid] for aid in CANONICAL_IDS],
        "publication_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verbo no Chão specialist checks")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--agent", choices=CANONICAL_IDS)
    group.add_argument("--aggregate", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--audio-preflight", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.aggregate:
        if args.input_dir is None:
            parser.error("--aggregate requires --input-dir")
        result = aggregate(args.input_dir, audio_preflight_path=args.audio_preflight)
    else:
        result = run_agent(args.agent, args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k in ("agent", "status", "agents_executed", "agents_blocked", "blockers")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
