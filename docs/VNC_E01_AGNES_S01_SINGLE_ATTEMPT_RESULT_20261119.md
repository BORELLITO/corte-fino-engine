# E01 S01 — primeira tentativa Agnes Flash | 2026-11-19

## Escopo autorizado
Usuário autorizou UMA tentativa de geração da cena `VNC-E01V2-S01` exclusivamente sob preço promocional anunciado USD 0; publicação não autorizada. Modelo `agnes-video-2.5-flash`, 6 segundos, 720P, 9:16, texto-para-vídeo, `n=1`, sem mídias de referência.

## Execução real observada
- Repositório: `BORELLITO/verbo-no-chao-engine`.
- Branch de execução isolada: `verbo-no-chao/agnes-flash-transport-gated-20261119-v1`.
- Commit que disparou workflow: `c5c80fb019224b5828a38b33242dd5fded171ebf`.
- Workflow: https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44583046047
- Resultado CI: `failure` na etapa `One approved 6s Flash S01 attempt`. Os 17 testes offline do workflow passaram antes do POST; Engine Gates e Eight Specialist Audits passaram para o commit do acionamento.
- Preflight oficial de preço: `OFFICIAL_DEFAULT_FLASH_720P_ZERO_USD_PRICE_CONFIRMED`, na checagem em tempo de execução.
- GET autenticado ao catálogo de modelos: `AUTHENTICATED_MODEL_CATALOG_CONFIRMED`.
- Bloqueio durável criado **antes** do POST em `operations/agnes_s01_one_shot_lock_20261119.json`, evitando novas tentativas por rerun.
- Foi feita uma chamada `POST /v1/videos` à Agnes. Resposta transformada em `provider_quota_or_queue_unavailable` pelo adaptador (`HTTP 429` ou `HTTP 503`); o adaptador não registra separadamente qual desses códigos ocorreu, logo a causa exata NÃO é verificada.
- Nenhum `video_id` foi retornado ao programa, nenhum arquivo MP4 foi gerado/baixado/validado, nenhum conteúdo foi publicado. Sem nova tentativa automática.
- **Faturamento após tentativa NÃO verificado**: os prints anteriores de saldo zero não substituem consulta posterior à fatura; a documentação da Agnes informa que falhas podem ou não ser faturadas. Não declarar custo final USD 0 sem evidência contábil.

## Segurança e continuidade
- Chave permanece em GitHub Environment `verbo-no-chao-agnes-readonly`; não publicada nos logs.
- Contrato canônico `contracts/e01_agnes_flash_runtime_gate_v1.json` continua com `enable_submission=false` e `publication_authorized=false`.
- Essa autorização de uma tentativa está CONSUMIDA. Não apagar o lock ou repetir via Actions sem nova decisão humana explícita e revisão do estado remoto.
- Evidência externa semelhante: https://github.com/AgnesAI-Labs/AgnesAI-Models/issues/142 (relatos 503 fila cheia). É evidência de problema semelhante, NÃO confirmação de que esta conta recebeu HTTP 503 especificamente.
- Próximo passo técnico seguro: verificar o registro de faturamento e escolher alternativa gratuita para adquirir cena real; qualquer nova submissão à Agnes exige nova autorização, sem repetição automática.
