# Auditoria do lote visual cloud — Salmo 13

Estado: `EXPANDED_MULTI_SHOT_BANK_READY_FOR_VISUAL_QA`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Escopo

- Projeto: Verbo no Chão — piloto Salmo 13.
- Regra clean-room: nenhum conteúdo, mídia, identidade, prompt ou fluxo operacional do Because Of This Stories foi utilizado.
- Fonte dominante do lote: Pexels, com licença de origem revisada.
- Nenhum asset foi liberado automaticamente para publicação.

## Resultado da expansão

O banco passou de 4 para 12 assets persistidos, corrigindo a insuficiência apontada para um vídeo de aproximadamente 75 segundos.

| Grupo | Quantidade | Uso |
|---|---:|---|
| Verticais nativos 9:16 | 8 | prioridade de montagem |
| Horizontais para reenquadramento | 4 | usar somente após crop aprovado |
| Total persistido | 12 | banco suficiente para selecionar 10–12 planos |

## QA técnico confirmado

- Todos os 12 assets foram importados por rota cloud persistente.
- Todos foram identificados como `video/mp4`.
- As dimensões e durações foram confirmadas pela biblioteca audiovisual.
- S13-V04 é vertical 2160×3840 e deve ser normalizado para o master.
- S13-V09, S13-V10, S13-V11 e S13-V12 são horizontais e exigem reenquadramento controlado.
- Os demais oito assets são verticais nativos 9:16.

## Composição prevista

- 10–12 planos no vídeo final;
- 2–4 reservas;
- cortes médios de 3–7 segundos;
- nenhum plano repetido;
- água e luz usados como respiro, não como preenchimento;
- caminho e estrada reservados para transições e conclusão;
- espaço inferior protegido para legendas;
- correção cromática neutra levemente quente, com contraste moderado.

## Direitos

- Pexels: licença pública gratuita para uso comercial sem atribuição obrigatória, sujeita às restrições de terceiros e da licença.
- Ledger específico criado e atualizado em [PILOT_SALMO_13_RIGHTS_LEDGER.md](PILOT_SALMO_13_RIGHTS_LEDGER.md).
- Hashes ainda pendentes.
- Nenhum asset está autorizado para publicação isoladamente.
- Não houve gasto, publicação ou criação de conta.

## Próximo gate

1. executar QA visual dos 12 assets na composição 9:16;
2. testar crops dos quatro horizontais;
3. eliminar redundâncias, logos, marcas ou planos visualmente fracos;
4. fechar 10–12 planos definitivos;
5. resolver narração comercialmente autorizada;
6. iniciar montagem somente após os gates anteriores.
