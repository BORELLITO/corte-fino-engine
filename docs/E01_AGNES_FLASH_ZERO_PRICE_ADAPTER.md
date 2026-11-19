# E01 Agnes Video 2.5 Flash — prepared alternative provider, no charges

**Candidate:** Agnes 2.5 Flash, 720p, 4–12 seconds, 9:16, image references/first frame; official developer model catalog lists an **active limited-time US$0/sec promotional rate**, not a perpetual free plan. Queue delays and model access may make production infeasible. Confirm account-specific terms before first real call.

Official references:
- https://github.com/AgnesAI-Labs/skills/blob/main/agnes-ai-models/references/model_catalog.md
- https://github.com/AgnesAI-Labs/AgnesAI-Models
- https://wiki.agnes-ai.com/en/docs/pricing.md
- Modern API: POST https://apihub.agnes-ai.com/v1/videos. Requires `AGNES_API_KEY`; requests are asynchronous and polled by `video_id`.

**Implement without spending:** `python -m agents.e01_agnes_flash_free_only` validates the exact 6s/720P/9:16/model-S01 prompt and the never-paid contract. It **makes ZERO network calls and ZERO video submissions**, even if a secret is already present. No subscription is created. This is a safe handoff, **not a proof of production**.

**Later safe activation steps requiring access:** authenticate once via ChatGPT Work Cloud Browser using the secure login flow, inspect API key and actual account entitlement/price with the provider; store secret only in GitHub encrypted Actions secrets or connected provider. If zero-cost rate is not proved within the user's exact account **do not submit**. Verify terms for commercial Shorts output. Never use `agnes-video-2.5` paid model as fallback, never print credentials or bill on retries. On true $0 entitlement, ONE S01 request followed by metadata/full decoded MP4, director scene review, private Drive quarantine and provenance lock; require direct user approval for publication, not per-shot creative selection.

**No TinyFish** is part of this integration. Use Work's native Cloud Browser only if account linking is necessary, otherwise GitHub Playwright for public pages.

## Executed adapter evidence, not a generation

Validated by Engine Gates https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44317305889 — 443 Python tests (10 skipped), all remaining passed, with strict free-plan model payload shape and zero-cost guard. The provider key and account price are still **unverified**. The public Agnes pricing documentation was opened by the separate Github Chromium browser proof https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44317311003 but the Markdown page returned an empty HTML title, so this does **not** confirm current contractual pricing or account model access. No API calls or videos were submitted; no fees paid.


## Continuidade apos renomear o repositorio (19/11/2026)
O repositorio canonico agora e `BORELLITO/verbo-no-chao-engine`. O acesso ao Google Flow via navegador automatizado foi rejeitado e NAO e rota de producao. O adaptador atual esta no PR draft #53: `agents/e01_agnes_flash_transport_v1.py`, com workflow read-only e bloqueios de custo em `contracts/e01_agnes_flash_runtime_gate_v1.json`. A chave Agnes sera guardada APENAS no ambiente GitHub `verbo-no-chao-agnes-readonly`, nome `VNC_AGNES_API_KEY`, apos restricao de deployment branch a `verbo-no-chao/agnes-flash-transport-gated-20261119-v1`. Nao confundir o plano offline validado com uma geracao de video real, nem a lista de modelos com preco zero para a conta.
