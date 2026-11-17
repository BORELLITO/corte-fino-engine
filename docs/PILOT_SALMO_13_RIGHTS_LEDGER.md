# Rights ledger — piloto Salmo 13

Estado: EXPANDED_LEDGER_PENDING_HASH_AND_FINAL_VISUAL_REVIEW
Data: 2026-11-17 (America/Sao_Paulo)

## Regra

Este ledger controla a origem e a elegibilidade operacional dos assets do piloto. Importação persistente e licença pública da fonte não equivalem, sozinhas, a autorização de publicação.

## Fonte licenciada

- Provedor dominante: Pexels.
- Licença consultada: Pexels License, uso comercial permitido sem atribuição obrigatória, sujeito às restrições da licença e a direitos de terceiros.
- Página da licença: https://www.pexels.com/license/
- Estado de direitos do lote: SOURCE_LICENSE_REVIEWED_PENDING_ASSET_HASH_AND_FINAL_QA.
- Regra operacional: não usar cópia isolada sem tratamento editorial; não sugerir endosso; evitar marcas, logos, pessoas identificáveis em contexto sensível e associações indevidas.

## Assets persistidos

| ID | Página de origem | Identificador durável | MIME | Dimensões | Duração | Hash | Publicação |
|---|---|---|---|---|---:|---|---|
| S13-V01 | https://www.pexels.com/video/a-sunrise-over-a-city-with-fog-and-trees-18310302/ | `e4f8059a-5773-487d-8fb5-a769bf1dbf22` | video/mp4 | 1080×1920 | 17,045 s | pendente | NÃO LIBERADO |
| S13-V02 | https://www.pexels.com/video/a-sunrise-over-a-field-with-trees-and-houses-18675414/ | `096d4719-2826-4cce-ab34-456a75b40cd8` | video/mp4 | 1080×1920 | 34,027 s | pendente | NÃO LIBERADO |
| S13-V03 | https://www.pexels.com/video/the-sun-is-shining-through-the-trees-and-fog-18675419/ | `75ad51e6-333a-4a65-ab9f-432fa929fb64` | video/mp4 | 1080×1920 | 46,100 s | pendente | NÃO LIBERADO |
| S13-V04 | https://www.pexels.com/video/cinematic-timelapse-of-misty-morning-sunrise-34142319/ | `349f6fa3-7e09-42ef-a421-ca82f63b0743` | video/mp4 | 2160×3840 | 15,015 s | pendente | NÃO LIBERADO |
| S13-V05 | https://www.pexels.com/video/tranquil-water-surface-with-gentle-ripples-32241480/ | `a033e3ed-2ff5-40c5-be64-a7b7f2f8b938` | video/mp4 | 1080×1920 | 15,283 s | pendente | NÃO LIBERADO |
| S13-V06 | https://www.pexels.com/video/serene-water-ripples-with-reflective-textures-34922859/ | `96b00bc6-2f6d-4928-960f-183c50d0a2b9` | video/mp4 | 1080×1920 | 11,960 s | pendente | NÃO LIBERADO |
| S13-V07 | https://www.pexels.com/video/serene-misty-forest-morning-38731245/ | `9b5776a3-7077-435d-929a-e803f4cc9311` | video/mp4 | 1080×1920 | 37,333 s | pendente | NÃO LIBERADO |
| S13-V08 | https://www.pexels.com/video/morning-sunlight-shining-through-tree-branches-in-the-countryside-15365452/ | `54a69792-811b-499c-8578-96fb3ca74379` | video/mp4 | 1080×1920 | 12,415 s | pendente | NÃO LIBERADO |
| S13-V09 | https://www.pexels.com/video/misty-forest-pathway-in-early-morning-light-31808103/ | `6084c1ca-c0b8-4435-830b-0d8b3445bcf3` | video/mp4 | 1920×1080 | 24,658 s | pendente | NÃO LIBERADO |
| S13-V10 | https://www.pexels.com/video/foggy-forest-during-early-sunrise-5487156/ | `3be67dab-9912-4049-b197-7300ffdb8489` | video/mp4 | 1920×1080 | 17,493 s | pendente | NÃO LIBERADO |
| S13-V11 | https://www.pexels.com/video/forest-path-on-misty-morning-5518075/ | `fed92381-3ebc-49f3-9058-713515f7a546` | video/mp4 | 3840×2160 | 10,432 s | pendente | NÃO LIBERADO |
| S13-V12 | https://www.pexels.com/video/view-of-an-empty-road-at-dawn-3150352/ | `cedae517-719a-47ae-b202-c4e24e592c0b` | video/mp4 | 4096×2160 | 10,645 s | pendente | NÃO LIBERADO |

## QA técnico confirmado

- 12 assets importados por rota cloud persistente.
- Todos identificados como `video/mp4`.
- 8 assets verticais nativos 9:16.
- 4 assets horizontais, utilizáveis somente após reenquadramento controlado.
- Durações confirmadas pela biblioteca cloud.
- S13-V04 é vertical 2160×3840 e precisa ser normalizado para o master.
- S13-V09–V12 exigem teste de crop para preservar assunto e espaço de legenda.

## Pendências bloqueantes

1. calcular e registrar hashes dos arquivos persistidos;
2. revisar visualmente cada asset na composição 9:16;
3. confirmar ausência de logos, marcas e elementos sensíveis;
4. harmonizar temperatura, contraste e velocidade;
5. eliminar planos redundantes ou visualmente fracos;
6. selecionar 10–12 planos definitivos;
7. liberar somente o conjunto aprovado para montagem.

## Estado de decisão

- `S13-V01..V12`: DURABLE_IMPORTED_AND_TECHNICALLY_INSPECTED.
- `S13-V01..V12`: RIGHTS_SOURCE_REVIEWED.
- `S13-V01..V12`: HASH_PENDING.
- `S13-V01..V12`: PUBLICATION_BLOCKED.
- Piloto Salmo 13: EXPANDED_MULTI_SHOT_BANK_READY_FOR_VISUAL_QA.
