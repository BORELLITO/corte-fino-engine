# Candidatos visuais — piloto Salmo 13

Estado: EXPANDED_MULTI_SHOT_BANK_PENDING_ZERO_COST_VISUAL_QA
Data: 2026-11-17 (America/Sao_Paulo)

## Critério

O banco foi ampliado para sustentar um vídeo de aproximadamente 75 segundos sem repetir planos. A seleção mantém Pexels como fonte dominante e distribui funções visuais entre espera, caminho, neblina, luz, reflexão, água e conclusão.

Nenhum candidato está liberado para publicação. O status só muda após importação persistente, inspeção técnica, QA visual, registro de licença, identificação durável e hash quando disponível.

## Banco expandido

- 12 assets persistidos na biblioteca cloud.
- 8 verticais nativos 9:16.
- 4 horizontais para reenquadramento controlado.
- Seleção final esperada: 10–12 planos distintos.
- Regra bloqueante: nenhum clipe pode aparecer duas vezes no mesmo vídeo, inclusive com crop, zoom, velocidade, espelhamento ou cor diferentes.

Os 12 registros completos, páginas de origem e identificadores estão no [ledger de direitos](PILOT_SALMO_13_RIGHTS_LEDGER.md).

## QA técnico já confirmado

- Todos os 12 assets são `video/mp4`.
- Dimensões e durações foram confirmadas pela biblioteca cloud.
- S13-V04 é vertical 2160×3840 e precisa ser normalizado.
- S13-V09–V12 são horizontais e exigem teste de crop.
- Os demais oito assets são verticais nativos.

## QA visual

O extrator de quadros cloud foi acionado para inspeção de sequência, área segura de legenda e redundância visual, mas retornou `zero_balance`: a operação exigiria aproximadamente 2 créditos e a conta possui 0. Nenhum crédito foi consumido.

Por isso, o QA visual permanece **NÃO TESTADO**, e nenhum asset foi liberado para montagem final com base apenas em metadados.

## Próximo gate

Executar QA visual por uma rota gratuita compatível, mantendo a regra de zero repetição; depois selecionar os 10–12 planos definitivos, gerar/validar a narração e iniciar a montagem.
