"""Create three real original script drafts. No Bible translation copied or auto-approval.

Theological source research is versioned as reference notes. Its factual claims
still require independent editorial review before voice generation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from agents.content_production import ProductionError, check, read
from editorial.review import review_script, REQUIRED_ORDER
from editorial.script_validator import validate_script_package

TRUSTED_CONTEXT_HOSTS = frozenset({
    "bibleproject.com",
    "classic.net.bible.org",
    "www.workingpreacher.org",
})
CONTEXT_KEYS = (
    "literary_genre", "historical_setting", "central_reading",
    "application_limit", "misreading_to_avoid",
)
EXPECTED_IDS = ("VNC-W01-E1", "VNC-W01-E2", "VNC-W01-E3")


def validate_batch(seed: Any, plan: Any, source_policy: Any) -> list[dict[str, Any]]:
    check(isinstance(seed, dict) and seed.get("project") == "verbo-no-chao",
          "script_batch:project")
    check(seed.get("publication_authorized") is False and seed.get("owner_approval") is False,
          "script_batch:approval_lock")
    check(seed.get("editorial_status") == "DRAFT_REVIEW_REQUIRED"
          and seed.get("contextual_review") == "HUMAN_REVIEW_REQUIRED"
          and seed.get("quotation_policy") == "NO_VERBATIM_TRANSLATION",
          "script_batch:review_or_quotation_policy")
    check(seed.get("source_plan") == "agents/editorial_seed.json", "script_batch:source_plan")
    check(isinstance(source_policy, dict)
          and source_policy.get("project") == "verbo-no-chao"
          and source_policy.get("source_mode") == "reference_and_paraphrase"
          and source_policy.get("selected_translation") is None
          and source_policy.get("biblical_review_required") is True
          and source_policy.get("publication_authorized") is False,
          "script_batch:source_policy")
    check(isinstance(plan, dict) and plan.get("project") == "verbo-no-chao"
          and plan.get("approval_status") == "DRAFT_REVIEW_REQUIRED"
          and plan.get("publication_authorized") is False
          and plan.get("start_date") == "NOT_SCHEDULED"
          and plan.get("ideas_count") == 39,
          "script_batch:plan_contract")
    planned = {item.get("episode_id"): item for item in plan.get("episodes", [])
               if isinstance(item, dict)}
    check(len(planned) == 39, "script_batch:plan_duplicate_or_missing")
    scripts = seed.get("episodes")
    check(isinstance(scripts, list) and len(scripts) == 3,
          "script_batch:three_drafts")
    check(tuple(item.get("episode_id") for item in scripts if isinstance(item, dict)) == EXPECTED_IDS,
          "script_batch:first_three_order")
    normalized_texts: set[str] = set()
    records: list[dict[str, Any]] = []
    urls_used: set[str] = set()
    for position, script in enumerate(scripts, 1):
        episode_id = script["episode_id"]
        planning = planned.get(episode_id)
        check(isinstance(planning, dict) and planning.get("week") == 1
              and planning.get("relative_day") == (1, 4, 6)[position - 1],
              f"script_batch:wrong_plan_slot:{episode_id}")
        check(script.get("reference") == planning.get("scripture_reference")
              and script.get("title_proposal") == planning.get("title_proposal"),
              f"script_batch:plan_reference_or_title_mismatch:{episode_id}")
        check(script.get("status") == "DRAFT_REVIEW_REQUIRED"
              and script.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW"
              and script.get("publication_authorized") is False
              and script.get("owner_approval") is False,
              f"script_batch:forged_approval:{episode_id}")
        check(script.get("source_decision_ref") == "contracts/new_script_source_policy.json",
              f"script_batch:wrong_source_policy:{episode_id}")
        check(isinstance(script.get("script_id"), str) and
              script["script_id"].startswith("vnc-" + episode_id.lower()),
              f"script_batch:script_id:{episode_id}")
        errors = validate_script_package(script)
        check(not errors, f"script_batch:script_contract:{episode_id}:{','.join(errors)}")
        reviewed = review_script(script)
        check(reviewed.status == "PASS_AUTOMATED_REVIEW" and not reviewed.errors,
              f"script_batch:automated_review:{episode_id}:{','.join(reviewed.errors)}")
        check(reviewed.estimated_seconds >= 63.75
              and reviewed.estimated_seconds <= 86.25,
              f"script_batch:duration_outside_75s_window:{episode_id}")
        full_text = " ".join(block.get("text", "") for block in script["blocks"])
        check(all(isinstance(b.get("text"), str) and len(b["text"].strip()) >= 35
                  for b in script["blocks"]), f"script_batch:weak_block:{episode_id}")
        check(tuple(b.get("type") for b in script["blocks"]) == REQUIRED_ORDER,
              f"script_batch:wrong_block_order:{episode_id}")
        fingerprint = hashlib.sha256(re.sub(r"\s+", " ", full_text.casefold()).encode()).hexdigest()
        check(fingerprint not in normalized_texts, f"script_batch:duplicate_full_script:{episode_id}")
        normalized_texts.add(fingerprint)
        context = script.get("biblical_context")
        check(isinstance(context, dict) and
              all(isinstance(context.get(k), str) and len(context[k]) > 25
                  for k in CONTEXT_KEYS) and
              context.get("theological_status") == "CONTEXT_REVIEW_REQUIRED",
              f"script_batch:weak_or_approved_theology:{episode_id}")
        book = script["reference"].split()[0].casefold()
        biblical_text = next(b["text"] for b in script["blocks"] if b["type"] == "biblical_reference")
        check(book in biblical_text.casefold(), f"script_batch:book_not_mentioned:{episode_id}")
        sources = script.get("research_sources")
        check(isinstance(sources, list) and len(sources) >= 2,
              f"script_batch:missing_two_context_sources:{episode_id}")
        for source in sources:
            check(isinstance(source, dict), f"script_batch:source_not_object:{episode_id}")
            url = source.get("url")
            check(isinstance(url, str), f"script_batch:source_url_missing:{episode_id}")
            parsed = urlsplit(url)
            check(parsed.scheme == "https"
                  and parsed.hostname in TRUSTED_CONTEXT_HOSTS
                  and not parsed.username and not parsed.password
                  and parsed.port in (None, 443),
                  f"script_batch:untrusted_source_url:{episode_id}")
            check(url not in urls_used and len(source.get("note", "")) >= 35,
                  f"script_batch:reused_or_unexplained_source:{episode_id}")
            urls_used.add(url)
        records.append({
            "episode_id": episode_id,
            "script_id": script["script_id"],
            "reference": script["reference"],
            "word_count": reviewed.word_count,
            "estimated_seconds": reviewed.estimated_seconds,
            "automated_review": reviewed.status,
            "original_script_sha256": fingerprint,
            "status": "DRAFT_REVIEW_REQUIRED",
            "biblical_context_review": "PENDING_INDEPENDENT_REVIEW",
            "publication_authorized": False,
        })
    check(len(records) == 3, "script_batch:count")
    return records


def produce(root: Path, output: Path, *, upstream_root: Path | None = None) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    upstream_root = (upstream_root or root).resolve()
    check(not any(output.is_relative_to(root / p)
                  for p in ("contracts", "docs", "tests", "agents")),
          "script_batch:protected_output_directory")
    ev: dict[str, str] = {}
    seed = read(root, "agents/first_batch_seed.json", ev)
    source_policy = read(root, "contracts/new_script_source_policy.json", ev)
    editorial_seed = read(root, "agents/editorial_seed.json", ev)
    plan = read(upstream_root, "operations/growth_90d.json", ev)
    report = read(upstream_root, "editorial-deliveries/production_report.json", ev)
    check(isinstance(report, dict) and report.get("project") == "verbo-no-chao"
          and report.get("status") == "DELIVERABLES_GENERATED_REVIEW_REQUIRED"
          and report.get("publication_authorized") is False,
          "script_batch:upstream_production_not_verified")
    canonical = next((x for x in report.get("files", [])
                      if x.get("path") == "operations/growth_90d.json"), None)
    check(isinstance(canonical, dict)
          and canonical.get("sha256") == ev["operations/growth_90d.json"],
          "script_batch:upstream_plan_hash_mismatch")
    check(plan.get("evidence_sha256", {}).get("agents/editorial_seed.json")
          == ev["agents/editorial_seed.json"], "script_batch:seed_hash_mismatch")
    check(editorial_seed.get("publication_authorized") is False,
          "script_batch:editorial_seed_publication_flag")
    records = validate_batch(seed, plan, source_policy)

    package = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "batch_id": "VNC-W01-THREE-SCRIPTS",
        "status": "DRAFT_REVIEW_REQUIRED",
        "contextual_review_status": "PENDING_INDEPENDENT_REVIEW",
        "originality_review_status": "PENDING_INDEPENDENT_REVIEW",
        "owner_approval": False, "publication_authorized": False,
        "scripts": seed["episodes"], "automated_checks": records,
        "evidence_sha256": ev,
        "limitations": [
            "A source URL is not a license or theological endorsement",
            "Drafted as original paraphrases; lack of copying is not algorithmically proven",
            "Automated regex/length checks cannot prove theological accuracy",
            "Duration uses a word-speed estimate, not generated speech",
            "No approval for audio generation, asset use, scheduling or publishing",
        ],
    }
    md = [
        "# VERBO NO CHÃO — Primeiros três roteiros originais",
        "",
        "**RASCUNHOS PARA REVISÃO BÍBLICA E EDITORIAL. Não são vídeos nem roteiros aprovados para voz.**",
        "",
        "Os três textos preservam contexto, paráfrases próprias e ações responsáveis.",
        "Fontes externas são apoio para conferência; não autorizam copiar traduções ou comentários.",
    ]
    for script, record in zip(seed["episodes"], records):
        md.extend([
            "", "## " + script["episode_id"] + " — " + script["title_proposal"],
            "",
            "Referência: **" + script["reference"] + "**",
            f"Estimativa: {record['word_count']} palavras / {record['estimated_seconds']} s (não áudio medido)",
            "",
            "### Narração proposta", "",
        ])
        for block in script["blocks"]:
            md.extend(["**" + block["type"] + "**", block["text"], ""])
        md.extend([
            "### Contexto e riscos interpretativos", "",
            "- Contexto: " + script["biblical_context"]["historical_setting"],
            "- Leitura central: " + script["biblical_context"]["central_reading"],
            "- Limite da aplicação: " + script["biblical_context"]["application_limit"],
            "- Evitar: " + script["biblical_context"]["misreading_to_avoid"],
            "", "### Referências para conferência", "",
        ])
        md.extend("- " + x["url"] + " — " + x["note"] for x in script["research_sources"])
        md.extend(["", "Status: DRAFT_REVIEW_REQUIRED | PENDING_INDEPENDENT_REVIEW", ""])

    def as_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"

    def write(relative: str, content: str) -> dict[str, str]:
        path = (output / relative).resolve()
        check(path.is_relative_to(output), "script_batch:output_path_escape")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": relative, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}

    files = [
        write("operations/first_batch_scripts.json", as_json(package)),
        write("editorial-deliveries/first_batch_scripts.md", "\n".join(md) + "\n"),
    ]
    result = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "status": "FIRST_THREE_DRAFTS_GENERATED_REVIEW_REQUIRED",
        "scripts_count": 3, "files": files, "checks": records,
        "source_evidence_sha256": ev, "owner_approval": False,
        "publication_authorized": False,
    }
    write("editorial-deliveries/first_batch_report.json", as_json(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce first three Verbo no Chão script drafts")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--upstream-dir", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = produce(args.root, args.output_dir, upstream_root=args.upstream_dir)
    except (ProductionError, ValueError, OSError, TypeError, KeyError) as exc:
        parser.exit(1, f"BLOCKED: {type(exc).__name__}:{exc}\n")
    print(json.dumps({k: result[k] for k in ("status", "scripts_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
