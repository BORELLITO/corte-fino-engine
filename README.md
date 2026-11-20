# Verbo no Chão

Motor audiovisual cristão original. Produz curtas verticais (1080×1920, 9:16) com base em texto bíblico, narração em pt-BR e legendas sincronizadas, sob gates fail-closed que bloqueiam qualquer entrega sem evidência física real.

**Estado em 20/11/2026:** episódio piloto **E01 — "Quando você pergunta e nada muda"** (Habacuque 1:2–4) em curadoria de stock, 12 cenas planejadas, nenhuma aprovada para master. Master e publicação permanecem bloqueados. Ver `docs/ENGINE_LOCK.md` para o estado canônico vigente.

Esta branch é independente do legado Corte Fino/Because Of This: nenhum conteúdo operacional desses projetos é reaproveitado (política clean-room, `docs/CLEAN_ROOM_POLICY.md`).

## Como o motor funciona

| Camada | Local | Papel |
|---|---|---|
| Contratos | `contracts/*.json`, `contracts/*.schema.json` | Esquema e estado de cada cena, roteiro, voz, direitos e política editorial |
| Validador de gates | `engine/quality_gates.py` | Falha fechado: bloqueia se qualquer campo, hash ou estado estiver ausente/inválido |
| Orquestração | `orchestrator/runflow.py`, `render.py`, `state_machine.py`, `dry_run.py` | Recebe um *brief*, exige um pacote de provedor com mídia física real, renderiza com FFmpeg e valida bytes antes de promover o estado |
| Agentes/especialistas | `agents/` (46 módulos) | Auditorias determinísticas e de leitura (não LLMs persistentes) + intake de stock real (download, hash, prova física) por cena |
| QA, editorial, direitos, mídia | `qa/`, `editorial/`, `rights/`, `media/` | Gates de release, revisão de roteiro, validação de direitos e probe físico (ffprobe/ffmpeg) |
| Testes | `tests/` (482 testes) | Cobrem pass, bloqueio, repetição de clipe, ausência de direitos/trilha e tentativa de publicação prematura |

Fluxo obrigatório (sem pular etapas): `PEDIDO → BRIEFING → ROTEIRO → FONTES → VOZ → TRILHA → TIMELINE → LEGENDAS → QA → MANIFESTO → PREVIEW_READY/READY_FOR_OWNER_APPROVAL → APROVAÇÃO → PUBLICAÇÃO AUTORIZADA`.

## Política de automação aprovada

Para episódios novos (não o piloto), `contracts/video_workflow_policy.json` (v1.1, `APPROVED`) e `contracts/autonomous_editorial_policy_v1.json` autorizam o motor a executar sozinho: seleção de roteiro/fontes/voz/trilha/legendas, produção cloud e QA interno completo, **sem exigir revisão intermediária do proprietário**. A única ação que continua exigindo autorização explícita e separada é a **publicação**. Nenhum gate de direitos, mídia física ou repetição de clipe é dispensado por essa política — ver `docs/AUTOMATED_VIDEO_WORKFLOW.md`.

Na prática, hoje: a orquestração (`runflow.py`) e a renderização (`render.py`) já são reais e funcionam sobre um pacote de provedor com mídia física. O que falta para "pedido → vídeo pronto" de ponta a ponta é um provedor de aquisição de clipes generalizado — atualmente a curadoria de stock (`agents/e01_stock_candidates.py`, `e01_candidate_media_intake.py`, `e01_two_real_stock_support.py`) é feita por scripts específicos por cena, não por um módulo único parametrizável por *brief*.

## Executando os gates localmente

```bash
python3 -m unittest discover -s tests -t .
python3 -m engine.quality_gates <manifest.json> --artifact-root <dir>
```

A CI `verbo-no-chao-gates.yml` deve passar antes de qualquer promoção de estado. `verbo-no-chao-agents.yml` roda as oito auditorias de especialista (`docs/SPECIALIST_TEAM.md`).

## Travas que nunca são dispensadas

1. Clean-room: nenhum asset/prompt/voz/identidade de projetos antigos.
2. Cloud-only; o dispositivo do proprietário só controla a sessão.
3. Mesmo asset de origem nunca aparece duas vezes no mesmo vídeo (crop/zoom/espelhamento não criam asset novo).
4. Cada asset precisa de origem, SHA-256, intervalo temporal e estado de direitos.
5. Direitos pendentes só permitem `PREVIEW_READY`; nunca publicação.
6. `publication_authorized` só é `true` em `PUBLISHED`, após aprovação explícita.

Detalhes completos em `docs/ENGINE_LOCK.md`.
