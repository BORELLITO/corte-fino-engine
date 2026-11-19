# VERBO NO CHÃO — Agnes Video 2.5 Flash | API direta protegida (19/11/2026)

## Decisão
- Agnes é candidata a geração automática por API; nenhum acesso autenticado nem vídeo foi comprovado.
- Adaptador: agents/e01_agnes_flash_transport_v1.py. Contrato: contracts/e01_agnes_flash_runtime_gate_v1.json.
- Reutiliza pedido canônico de S01: 6 segundos, 720P, retrato 9:16, n=1, text-to-video, agnes-video-2.5-flash.
- Todos os seis bloqueios de submissão no contrato estão FALSE; não existe fallback pago nem publicação.

## Evidências oficiais
1. Preços https://wiki.agnes-ai.com/en/docs/pricing.md — vídeo Flash 720P US$ 0/segundo apenas na promoção de teste para contas default elegíveis; preço de tabela US$ 0,025/segundo. Agent Plan não recebe promoção. A fatura da conta é a verdade para qualquer cobrança.
2. Catálogo https://github.com/AgnesAI-Labs/skills/blob/main/agnes-ai-models/references/model_catalog.md — endpoint POST /v1/videos, GET /v1/models, polling GET /agnesapi com video_id e model_name. Flash suporta 720P, 4–12 segundos e n=1.
3. Relatos de fila https://github.com/AgnesAI-Labs/AgnesAI-Models/issues/146 — erro 503 Video Query is full, outubro de 2026. Sem retries automáticos em POST, que podem duplicar cobranças.

## Operação
- plan: apenas valida e produz o pedido, sem rede/segredo.
- preflight: consulta autenticada GET /v1/models quando houver chave AGNES_API_KEY; não prova custo zero.
- poll: consulta somente status e SHA256 de URL de um trabalho previamente conhecido; não baixa mídia privada.
- submit: implementação disponível mas bloqueada por contrato até aprovação da S01, confirmação comprovada do plano default e preço zero para a conta, e liberação específica.

## Comandos locais
- python -m agents.e01_agnes_flash_transport_v1 --mode plan
- python -m unittest tests.test_e01_agnes_flash_transport_v1 -v
- python -m agents.e01_agnes_flash_transport_v1 --mode preflight (somente após colocar AGNES_API_KEY em ambiente seguro).

## Segurança e limites
- Chave nunca no chat, no código, no PR nem em logs públicos; futura configuração em GitHub Actions Secret VNC_AGNES_API_KEY.
- Workflow novo só executa testes, plano offline e GET autenticado opcional; NÃO faz POST.
- A API oficial não fornece ao nosso adaptador uma prova programática do preço específico da conta: manter enable_submission FALSE até verificação.
- Não carregar imagens, não guardar URLs privadas, não entregar MP4, não liberar master nem publicar.
- MASTER_BLOCKED / PUBLISH_BLOCKED. Produção cinematográfica e direitos ainda pendentes.

## Reversão
Branch isolada e PR draft. Nenhuma mudança ao motor aprovado, às branches operacionais ou a outros projetos.
