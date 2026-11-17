# Rights ledger — piloto Salmo 13

Estado: EXPANDED_LEDGER_PENDING_HASH_AND_VISUAL_REVIEW_NO_CREDITS
Data: 2026-11-17 (America/Sao_Paulo)

## Regra

Importação persistente e licença pública da fonte não equivalem, sozinhas, a autorização de publicação. Cada asset precisa manter origem, identificação durável, metadados, QA visual e revisão final.

## Fonte

- Provedor dominante: Pexels.
- Licença consultada: https://www.pexels.com/license/
- Uso comercial sem atribuição obrigatória, sujeito às restrições da licença e a direitos de terceiros.
- Estado: SOURCE_LICENSE_REVIEWED_PENDING_ASSET_HASH_AND_FINAL_QA.

## Lote

- 12 assets persistidos.
- Todos `video/mp4`.
- 8 verticais nativos 9:16.
- 4 horizontais para reenquadramento.
- Identificadores, dimensões, durações e páginas de origem permanecem registrados na versão anterior deste ledger e nos IDs cloud do lote.
- Hashes ainda pendentes.
- Publicação de todos os itens: NÃO LIBERADA.

## Bloqueio de QA visual

A extração automatizada de quadros foi iniciada para verificar composição, redundância, crop e espaço de legendas, mas a ferramenta retornou `zero_balance`, exigindo aproximadamente 2 créditos; saldo disponível: 0. Nenhum crédito foi consumido.

Estado correto: QA visual NÃO TESTADO. Não confundir bloqueio de ferramenta com aprovação editorial.

## Invariantes

- Nenhum clipe pode repetir no mesmo vídeo.
- Transformações não criam um clipe novo.
- Cada plano final deverá registrar asset, origem e intervalo temporal.
- Qualquer repetição bloqueia a aprovação.

## Pendências

1. QA visual por rota gratuita;
2. hashes;
3. revisão de logos, marcas e pessoas identificáveis;
4. crop dos horizontais;
5. seleção final de 10–12 planos;
6. narração, trilha, legendas e montagem.
