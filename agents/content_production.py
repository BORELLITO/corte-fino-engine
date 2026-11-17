"""Versioned, deterministic editorial producers. No LLM/API, uploads or publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PILOT = "salmo 13"
SLOTS = (1, 4, 6)
BLOCKED_HOOKS = ("milagre garantido", "cura garantida", "prosperidade garantida", "deus me revelou")


class ProductionError(ValueError):
    pass


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise ProductionError(reason)


def read(root: Path, rel: str, evidence: dict[str, str]) -> Any:
    p = (root / rel).resolve()
    check(p.is_relative_to(root.resolve()) and p.is_file(), f"evidence_missing:{rel}")
    b = p.read_bytes()
    evidence[rel] = hashlib.sha256(b).hexdigest()
    try:
        return json.loads(b) if rel.endswith(".json") else b.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProductionError(f"evidence_invalid:{rel}") from exc


def text(value: Any, minimum: int = 5) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def validate_seed(seed: Any) -> None:
    check(isinstance(seed, dict) and seed.get("project") == "verbo-no-chao", "seed:project")
    check(seed.get("publication_authorized") is False, "seed:publication_lock")
    ap = seed.get("approval_scope", {})
    check(isinstance(ap, dict), "seed:approval_scope")
    for field in ("name", "editorial_promise", "primary_audience", "secondary_audience", "theological_voice"):
        item = ap.get(field)
        check(isinstance(item, dict) and text(item.get("value"), 2)
              and str(item.get("status", "")).startswith("OWNER_APPROVED_"), f"seed:approval:{field}")
    check(ap["name"]["value"] == "VERBO NO CHÃO", "seed:name_changed")
    check(ap["editorial_promise"]["value"] ==
          "Dar sentido bíblico às dores, dúvidas e recomeços da vida real — com contexto, profundidade e esperança honesta.",
          "seed:promise_changed")
    check(ap["theological_voice"]["value"] == "Cristã ampla, bíblica, cristocêntrica e não sectária",
          "seed:voice_changed")
    safety = ap.get("editorial_guardrails")
    check(isinstance(safety, dict) and safety.get("status", "").startswith("OWNER_APPROVED_")
          and isinstance(safety.get("value"), list) and len(safety["value"]) >= 7
          and all(text(x) for x in safety["value"]), "seed:safety")
    check(ap.get("tagline", {}).get("status") == "PROPOSED_NOT_FINAL_APPROVAL",
          "seed:tagline_promoted")
    proposal = seed.get("proposal")
    check(isinstance(proposal, dict) and proposal.get("status") == "DRAFT_REVIEW_REQUIRED",
          "seed:review_status")
    check(proposal.get("window_days") == 90, "seed:window")
    cadence = proposal.get("cadence", {})
    check(isinstance(cadence, dict) and cadence.get("shorts_per_week") == 3
          and cadence.get("slot_days") == list(SLOTS)
          and cadence.get("status") == "HYPOTHESIS_NOT_APPROVED", "seed:cadence")
    check(proposal.get("duration_target_seconds") in {70, 75, 78}
          and proposal.get("duration_status") == "PROPOSED_COMPATIBLE_WITH_SCRIPT_CONTRACT",
          "seed:duration")
    check(proposal.get("pilot_exclusion", {}).get("reference") == "Salmo 13", "seed:pilot_protection")
    pillars = proposal.get("pillars")
    check(isinstance(pillars, list) and len(pillars) >= 3, "seed:pillars")
    pids = [x.get("id") for x in pillars if isinstance(x, dict)]
    check(len(pids) == len(pillars) and len(set(pids)) == len(pids), "seed:pillar_ids")
    check(all(text(p.get("label")) and text(p.get("editorial_goal")) for p in pillars), "seed:pillar_labels")
    weeks = proposal.get("weeks")
    check(isinstance(weeks, list) and len(weeks) == 13, "seed:thirteen_weeks")
    unique = {k: set() for k in ("id", "reference", "title_proposal", "hook_proposal")}
    for i, week in enumerate(weeks, 1):
        check(isinstance(week, dict) and week.get("week") == i
              and week.get("pillar") in pids and text(week.get("theme")),
              f"seed:week:{i}")
        ideas = week.get("ideas")
        check(isinstance(ideas, list) and len(ideas) == 3, f"seed:three_ideas:{i}")
        for idea in ideas:
            check(isinstance(idea, dict), "seed:idea")
            for k in ("id", "reference", "title_proposal", "hook_proposal",
                      "practical_angle", "theological_caution"):
                check(text(idea.get(k)), f"seed:missing:{k}")
            for k, seen in unique.items():
                value = idea[k].casefold().strip()
                check(value not in seen, f"seed:duplicate:{k}:{value}")
                seen.add(value)
            reference = idea["reference"].casefold().strip()
            check(not (reference == PILOT or reference.startswith(PILOT + ":")),
                  "seed:pilot_in_plan")
            check(any(c.isdigit() for c in reference), "seed:invalid_reference")
            hook = (idea["title_proposal"] + " " + idea["hook_proposal"]).casefold()
            check(not any(x in hook for x in BLOCKED_HOOKS), "seed:unsafe_promise")
    check(len(unique["id"]) == 39, "seed:thirty_nine_ideas")


def produce(root: Path, output: Path) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    check(not any(output.is_relative_to(root / p) for p in ("contracts", "docs", "tests", "agents")),
          "output:protected_directory")
    ev: dict[str, str] = {}
    seed = read(root, "agents/editorial_seed.json", ev)
    validate_seed(seed)
    refs = seed.get("provenance")
    check(isinstance(refs, list) and len(refs) >= 4 and len(set(refs)) == len(refs),
          "seed:provenance")
    docs = {}
    for rel in refs:
        check(isinstance(rel, str) and rel.startswith(("contracts/", "docs/")),
              "seed:unsafe_source_path")
        docs[rel] = read(root, rel, ev)
    check("Estado: " + chr(96) + "APPROVED" + chr(96) in docs["docs/CLEAN_ROOM_POLICY.md"],
          "policy:clean_room")
    check("publication_authorized" in docs["docs/ENGINE_LOCK.md"],
          "policy:publication_lock")
    check(docs["contracts/video_workflow_policy.json"].get("publication_authorized_by_default") is False
          and docs["contracts/video_workflow_policy.json"].get("final_owner_approval_required") is True,
          "policy:video_approval")
    check(docs["contracts/pilot_source_decision.json"].get("source_mode") == "reference_and_paraphrase"
          and docs["contracts/pilot_source_decision.json"].get("selected_translation") is None,
          "policy:scripture_license")
    ap, proposed = seed["approval_scope"], seed["proposal"]
    strategy = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "approval_status": "DRAFT_REVIEW_REQUIRED",
        "name": ap["name"]["value"],
        "tagline": {"text": ap["tagline"]["value"], "status": "PROPOSED"},
        "audience": {"primary": ap["primary_audience"]["value"], "secondary": ap["secondary_audience"]["value"]},
        "editorial_promise": ap["editorial_promise"]["value"],
        "differentiator": "Narrativas cristãs curtas com contexto bíblico, honestidade emocional e aplicação responsável, sem promessas automáticas.",
        "theological_voice": ap["theological_voice"]["value"],
        "content_pillars": proposed["pillars"],
        "format_proposal": {"duration_seconds": proposed["duration_target_seconds"],
                            "status": "PROPOSED_NOT_APPROVED",
                            "narrative": ["conexão humana", "contexto", "reflexão", "aplicação", "esperança honesta"]},
        "safety": ap["editorial_guardrails"]["value"],
        "evidence_refs": sorted(ev), "evidence_sha256": ev,
        "publication_authorized": False, "owner_approval": False,
        "generated_by": "rule_based_editorial_producer_v1",
    }
    ideas = []
    for week in proposed["weeks"]:
        for j, idea in enumerate(week["ideas"]):
            relative_day = 7 * (week["week"] - 1) + SLOTS[j]
            ideas.append({
                "slot_id": f"DAY-{relative_day:03d}", "relative_day": relative_day,
                "week": week["week"], "week_theme": week["theme"], "pillar": week["pillar"],
                "episode_id": idea["id"], "scripture_reference": idea["reference"],
                "title_proposal": idea["title_proposal"], "opening_proposal": idea["hook_proposal"],
                "practical_angle": idea["practical_angle"], "theological_caution": idea["theological_caution"],
                "source_mode": "reference_and_paraphrase",
                "script_status": "IDEA_ONLY_REQUIRES_CONTEXT_AND_SCRIPT_REVIEW",
                "media_status": "NOT_GENERATED", "rights_status": "NOT_REVIEWED",
                "publication_authorized": False,
            })
    check(len(ideas) == 39 and max(x["relative_day"] for x in ideas) == 90, "plan:coverage")
    plan = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "approval_status": "DRAFT_REVIEW_REQUIRED", "start_date": "NOT_SCHEDULED",
        "window_days": 90,
        "cadence": {"shorts_per_week": 3, "relative_days_of_week": list(SLOTS),
                    "status": "HYPOTHESIS_NOT_APPROVED", "publish_automatically": False},
        "milestones": [
            {"day": 30, "focus": "Validar clareza editorial e primeira safra",
             "gate": "revisao_roteiros_contexto_direitos"},
            {"day": 60, "focus": "Comparar dados reais se houver dados verificáveis",
             "gate": "metricas_com_fonte_ou_plano_base"},
            {"day": 90, "focus": "Revisar diversidade, identidade e continuidade",
             "gate": "revisao_qualidade_e_aprovacao"},
        ],
        "assumptions": [
            "A cadência é proposta reversível, sem agendamento aprovado",
            "39 pautas não são roteiros finalizados",
            "Cada episódio exige revisão contextual bíblica e avaliação de direitos",
            "Sem métricas reais não há previsão de views, retenção ou crescimento",
            "O piloto Salmo 13 não integra esta fila",
            "Nenhum vídeo pode ser publicado automaticamente",
        ],
        "ideas_count": 39, "episodes": ideas,
        "evidence_sha256": ev, "owner_approval": False, "publication_authorized": False,
        "generated_by": "rule_based_editorial_producer_v1",
    }
    md_strategy = [
        "# VERBO NO CHÃO — Estratégia editorial",
        "", "**PROPOSTA PARA REVISÃO. Não aprova roteiro, mídia nem publicação.**",
        "", "## Identidade e direção aprovadas", "",
        f"- Canal: {strategy['name']}",
        f"- Promessa: {strategy['editorial_promise']}",
        f"- Público principal: {strategy['audience']['primary']}",
        f"- Público secundário: {strategy['audience']['secondary']}",
        f"- Voz teológica: {strategy['theological_voice']}",
        "", "## Diferenciação proposta", "", strategy["differentiator"],
        "", "## Pilares propostos", "",
    ] + [f"- **{p['label']}** — {p['editorial_goal']}" for p in strategy["content_pillars"]] + [
        "", "## Forma narrativa proposta", "",
        "Conexão humana → contexto bíblico → reflexão → aplicação possível → esperança honesta.",
        "", "## Regras obrigatórias", "",
    ] + [f"- {r}" for r in strategy["safety"]] + [
        "", "## Estado das decisões", "",
        "- Nome, promessa, público e voz teológica preservam decisões já aprovadas.",
        "- Assinatura, pilares, duração e cadência continuam como propostas.",
        "- Não há alegação de pesquisa de mercado, resultados ou licença verificada nesta entrega.",
    ]
    md_plan = [
        "# VERBO NO CHÃO — Planejamento de 90 dias",
        "", "**PROPOSTA: sem datas reais, agendamento ou publicação.**",
        "", "39 ideias em 13 semanas, dias relativos 1, 4 e 6; Dia 1 ainda não está definido.",
        "O piloto Salmo 13 não foi incluído. Cada referência bíblica exige contextualização independente.",
        "", "## Marcos de revisão", "",
    ] + [f"- **Dia {m['day']}:** {m['focus']} ({m['gate']})" for m in plan["milestones"]]
    for week in proposed["weeks"]:
        md_plan.extend(["", f"## Semana {week['week']} — {week['theme']}", ""])
        for episode in (x for x in ideas if x["week"] == week["week"]):
            md_plan.extend([
                f"**Dia {episode['relative_day']}: {episode['title_proposal']}**",
                f"Referência: {episode['scripture_reference']}",
                f"Gancho: {episode['opening_proposal']}",
                f"Aplicação: {episode['practical_angle']}",
                f"Trava teológica: {episode['theological_caution']}",
                "",
            ])
    md_plan += ["", "## Gates de promoção", "",
                "Contexto bíblico → roteiro aprovado → fonte/licenças → montagem → QA físico → aprovação do proprietário → autorização de publicação separada.",
                "A ausência de métricas não permite inventar resultados nem reordenar a fila como se já existisse evidência."]

    def dump(data: Any) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    def write(rel: str, content: str) -> dict[str, str]:
        path = (output / rel).resolve()
        check(path.is_relative_to(output), "output:path_escape")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": rel, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}

    files = [
        write("operations/niche_strategy.json", dump(strategy)),
        write("operations/growth_90d.json", dump(plan)),
        write("editorial-deliveries/editorial_strategy.md", "\n".join(md_strategy) + "\n"),
        write("editorial-deliveries/90_day_plan.md", "\n".join(md_plan) + "\n"),
    ]
    report = {"schema_version": "1.0.0", "project": "verbo-no-chao",
              "status": "DELIVERABLES_GENERATED_REVIEW_REQUIRED",
              "producer_roles": ["niche_strategy", "growth_90d"],
              "ideas_count": len(ideas), "weeks_count": len(proposed["weeks"]), "window_days": 90,
              "files": files, "source_evidence_sha256": ev, "publication_authorized": False}
    write("editorial-deliveries/production_report.json", dump(report))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="VERBO NO CHÃO editorial producers")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = produce(args.root, args.output_dir)
    except (ProductionError, OSError, TypeError, KeyError, ValueError) as exc:
        parser.exit(1, f"BLOCKED: {type(exc).__name__}: {exc}\n")
    print(json.dumps({k: report[k] for k in ("status", "ideas_count", "weeks_count", "window_days")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
