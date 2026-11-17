# Auditoria do lote visual cloud — Salmo 13

Estado: `VISUAL_QA_COMPLETE_ASSET_GATE_PASSED_PENDING_AUDIO_AND_ASSEMBLY`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Resultado comprovado

- 12 assets persistidos na biblioteca cloud.
- 8 vídeos verticais nativos 9:16.
- 4 vídeos horizontais para reenquadramento.
- Todos identificados como `video/mp4`.
- Dimensões e durações confirmadas por `ffprobe`.
- Todos os arquivos foram baixados do CDN persistido e receberam SHA-256.
- QA visual gratuito concluído com quadros de início/meio/fim.
- Crop central 9:16 testado nos horizontais S13-V09, S13-V10 e S13-V11.
- O lote oferece oito planos PRIMARY distintos, três RESERVE e um REJECTED_HARMONY.
- A regra de zero repetição foi aplicada à seleção; nenhum asset será usado duas vezes no mesmo vídeo.

## Método de QA

1. Download dos 12 MP4 a partir dos CDN registrados no ledger.
2. Verificação de tipo, dimensão e duração com `ffprobe`.
3. Geração local de quadros representativos no início, meio e fim de cada vídeo.
4. Montagem de contact sheet para comparação de paleta, redundância, composição e espaço de legenda.
5. Teste de reenquadramento 9:16 para V09–V11.
6. Cálculo de SHA-256 dos bytes baixados.
7. Registro da decisão no ledger de direitos e na lista de candidatos.

A extração de quadros Creative Claw permaneceu indisponível por saldo zero, mas isso não bloqueou a inspeção porque a rota gratuita local produziu evidência visual real. Nenhum crédito foi consumido.

## Decisão visual

| Grupo | Assets | Resultado |
|---|---|---|
| PRIMARY | V02, V03, V05, V07, V08, V09, V10, V11 | liberados como candidatos de montagem, uma ocorrência por asset |
| RESERVE | V01, V04, V06 | preservar para substituição justificada; não empilhar com seus equivalentes |
| REJECTED_HARMONY | V12 | retirar do piloto por paleta azul urbana e quebra de atmosfera |

Os oito PRIMARY foram escolhidos por cobrirem abertura, espera, reflexão, floresta, luz, caminho e conclusão sem depender de repetição de fonte. V05 e V06 são visualmente próximos; V09–V11 cumprem funções de caminho diferentes, mas devem ser ordenados com intenção. V01–V03 são três amanheceres aéreos próximos; o plano final não deve usá-los como preenchimento repetitivo.

## Gate de zero repetição

Para cada plano do vídeo final, o manifesto deverá conter:

- `asset_id`;
- página de origem;
- hash do arquivo usado;
- intervalo temporal `in`/`out`;
- transformação de enquadramento;
- posição na timeline.

Bloquear se:

- o mesmo `asset_id` aparecer mais de uma vez;
- o hash do arquivo renderizado não corresponder ao ledger;
- uma transformação for usada para mascarar a repetição;
- o intervalo temporal estiver ausente ou se sobrepuser a outro uso do mesmo asset;
- o plano for substituído fora do manifesto.

## Bloqueios restantes

- revisão de logos, marcas, propriedades e pessoas identificáveis nos trechos efetivamente escolhidos;
- seleção da ordem e dos intervalos no storyboard;
- normalização/crop dos assets usados;
- voz comercialmente autorizada;
- trilha com licença compatível;
- legendas sincronizadas;
- QA final de áudio, safe area, codificação, duração e elegibilidade para publicação.

## Decisão operacional

O banco visual foi validado para avançar à etapa de storyboard/timeline e áudio, não para publicação. Nenhum gasto, publicação, criação de conta ou uso de conteúdo do Because Of This Stories foi realizado. O estado de publicação permanece bloqueado até que os gates restantes tenham evidência registrada.
