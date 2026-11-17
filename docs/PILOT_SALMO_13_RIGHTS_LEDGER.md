# Rights ledger — piloto Salmo 13

Estado: PARTIAL_LEDGER_PENDING_HASH_AND_FINAL_REVIEW
Data: 2026-11-17 (America/Sao_Paulo)

## Regra

Este ledger controla a origem e a elegibilidade operacional dos assets do piloto. Importação persistente e licença pública da fonte não equivalem, sozinhas, a autorização de publicação. Cada item precisa manter origem, identificação durável, metadados e revisão final.

## Fonte licenciada

- Provedor: Pexels.
- Licença consultada: Pexels License, uso comercial permitido sem atribuição obrigatória, sujeito às restrições da licença e a direitos de terceiros.
- Página da licença: https://www.pexels.com/license/
- Regra operacional: não usar cópia isolada sem tratamento editorial; não sugerir endosso; remover/evitar marcas, logos, pessoas identificáveis em contexto sensível e qualquer elemento que crie promessa ou associação indevida.
- Estado de direitos do lote: SOURCE_LICENSE_REVIEWED_PENDING_ASSET_HASH_AND_FINAL_QA.

## Assets persistidos

| ID editorial | Página de origem | Asset cloud | Identificador durável | MIME | Dimensões | Duração | Hash | Publicação |
|---|---|---|---|---|---:|---:|---|---|
| S13-V01 | https://www.pexels.com/video/a-sunrise-over-a-city-with-fog-and-trees-18310302/ | https://cdn.creativeclaw.co/u/cfe41e70/videos/bda458db-8fe2-4f6f-bdeb-956db4dc48c9.mp4 | e4f8059a-5773-487d-8fb5-a769bf1dbf22 | video/mp4 | 1080×1920 | 17.045 s | pendente | NÃO LIBERADO |
| S13-V02 | https://www.pexels.com/video/a-sunrise-over-a-field-with-trees-and-houses-18675414/ | https://cdn.creativeclaw.co/u/cfe41e70/videos/47f1dd8e-35d9-451b-a1d9-1b4b3386f60c.mp4 | 096d4719-2826-4cce-ab34-456a75b40cd8 | video/mp4 | 1080×1920 | 34.027 s | pendente | NÃO LIBERADO |
| S13-V03 | https://www.pexels.com/video/the-sun-is-shining-through-the-trees-and-fog-18675419/ | https://cdn.creativeclaw.co/u/cfe41e70/videos/b1a5f814-e916-4610-b506-3656ef8fa9a7.mp4 | 75ad51e6-333a-4a65-ab9f-432fa929fb64 | video/mp4 | 1080×1920 | 46.100 s | pendente | NÃO LIBERADO |
| S13-V04 | https://www.pexels.com/video/cinematic-timelapse-of-misty-morning-sunrise-34142319/ | https://cdn.creativeclaw.co/u/cfe41e70/videos/35dacb83-987e-4191-a73e-5d264ade96c4.mp4 | 349f6fa3-7e09-42ef-a421-ca82f63b0743 | video/mp4 | 2160×3840 | 15.015 s | pendente | NÃO LIBERADO |

## QA já confirmado

- Todos os quatro assets foram importados por rota cloud persistente.
- Todos foram identificados como `video/mp4`.
- S13-V01, S13-V02 e S13-V03 estão em 1080×1920; S13-V04 está em 2160×3840.
- Todos são verticais 9:16.
- S13-V04 exige revisão estética adicional para evitar aparência literal ou excessivamente religiosa.
- Nenhum asset foi publicado, vendido, redistribuído isoladamente ou usado como prova de endosso.

## Pendências bloqueantes

1. calcular e registrar hash dos arquivos persistidos;
2. revisar visualmente cada asset dentro da composição 9:16 e área segura de legendas;
3. confirmar ausência de logos, marcas ou elementos sensíveis;
4. harmonizar temperatura, contraste e velocidade;
5. selecionar os planos definitivos para a narrativa;
6. liberar apenas o conjunto aprovado para montagem.

## Estado de decisão

- `S13-V01..V04`: DURABLE_IMPORTED_AND_TECHNICALLY_INSPECTED.
- `S13-V01..V04`: RIGHTS_SOURCE_REVIEWED.
- `S13-V01..V04`: HASH_PENDING.
- `S13-V01..V04`: PUBLICATION_BLOCKED.
- Piloto Salmo 13: MULTI_SHOT_ASSET_GATE_READY_FOR_VISUAL_QA.
