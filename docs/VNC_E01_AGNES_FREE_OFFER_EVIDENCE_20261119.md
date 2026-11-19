# VERBO NO CHÃO — evidências de elegibilidade para teste Agnes Flash | 2026-11-19

## Evidência pública verificada
- Fonte oficial: https://wiki.agnes-ai.com/en/docs/pricing.md (consultada em 2026-11-19).
- O modelo **exato** `agnes-video-2.5-flash` em **720P** tem preço de tabela de USD 0.025 por segundo, mas **Angel User Trial Price USD 0 por segundo** durante a promoção por tempo limitado.
- A promoção contempla usuários `default`. **Agent Plan não é elegível** ao preço trial e pode ter cobrança de tabela.
- A própria fonte adverte que promoções podem mudar, que a conta e a fatura determinam cobranças reais, e que falhas podem ou não ser faturadas.

## Evidência da conta apresentada pelo usuário (não verificável via GitHub)
- Capturas mostraram saldo 0 USD, voucher 0 USD, recarga automática não vinculada e ausência de pagamentos registrados; a tela Agent Plan mostrou nenhuma assinatura ativa.
- Após contato via Live Chat da Agnes, usuário compartilhou resposta textual dizendo que uma conta gratuita com saldo 0 e sem assinatura paga pode solicitar 6s/720P no modelo Flash com custo zero durante a promoção.
- Esta resposta **não é comprovante assinado de precificação específica da conta**, nem substitui a fatura. Nenhuma credencial, nome pessoal, ID de conta ou chave foi copiada para o repositório.

## Condições de segurança e limites
- Somente `agnes-video-2.5-flash`; nunca `agnes-video-2.5` pago.
- Um vídeo em 720P, 9:16, 6 segundos, `n=1`, texto-para-vídeo sem mídia de entrada.
- Limite financeiro pretendido: USD 0. Não há garantia transacional de preço obtida via `GET /v1/models`.
- Credencial exclusiva do ambiente GitHub `verbo-no-chao-agnes-readonly` e nunca em logs nem arquivos.
- O teste de conectividade catalog-only já foi aprovado: https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44564661171
- **NENHUMA SUBMISSÃO DE GERAÇÃO AUTORIZADA NESTA ETAPA.** Gate `scene_generation_authorized=false`, `enable_submission=false` e demais flags permanecem intactas.
- Após autorização específica do usuário para a cena S01, verificar novamente o preço oficial/eligibilidade imediatamente antes de uma única tentativa de POST; em caso de divergência, bloquear. Nenhuma repetição automática, nenhum fallback pago, nenhuma publicação.
- Estado: preço público e confirmação conversacional favoráveis; faturamento real, fila do provedor, vídeo e direitos de uso ainda não validados.
