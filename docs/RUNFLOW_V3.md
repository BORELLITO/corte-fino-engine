# Runflow V3 — entrada única de produção

Acionar: Actions > "Verbo no Chão — Runflow de Produção" > `episode_id` (E01) + `mode` (`preflight` | `preview`).

- Custo novo R$0: sem segredos (só GITHUB_TOKEN), sem provedores pagos; flags `VNC_BUDGET_NEW_SPEND=0` e `VNC_PUBLICATION_AUTHORIZED=false` fixas.
- Trava de workflows: bloqueia se existir `schedule`, segredo além do GITHUB_TOKEN, host pago ou `push` sem filtro de branch.
- Estado vem de evidência física (`contracts/e01_pipeline_v3.json`); etapa sem executor seguro vira `no_automated_executor`, nunca roda às cegas.
- `preview` só renderiza se existir `episodes/<ID>/package/package.json`; senão `BLOCKED_NO_PHYSICAL_PACKAGE`.
- Chave de idempotência: `project|episode|spec_sha|stage|evidence_sha`. Concorrência por episódio, sem cancelar.
- Artefato público: apenas JSON/MD sanitizados. Nenhuma mídia, nenhuma publicação.
- Rollback: reverter o merge desta PR; nada foi mesclado sem autorização.
