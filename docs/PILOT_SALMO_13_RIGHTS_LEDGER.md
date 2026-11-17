# Rights ledger — piloto Salmo 13

Estado: MASTER_PREVIEW_READY_PENDING_FINAL_RIGHTS_REVIEW
Data: 2026-11-17 (America/Sao_Paulo)

## Regra

Importação persistente e licença pública da fonte não equivalem, sozinhas, a autorização de publicação. Cada asset precisa manter origem, identificação durável, metadados, hash, QA visual e revisão final de direitos de terceiros.

## Fonte

- Provedor dominante: Pexels.
- Licença consultada: https://www.pexels.com/license/
- Uso comercial sem atribuição obrigatória, sujeito às restrições da licença e a direitos de terceiros.
- A licença da página de origem não elimina a obrigação de revisar logos, marcas, pessoas identificáveis, propriedades e outros elementos protegidos.
- Publicação permanece NÃO LIBERADA.

## Lote e método de verificação

- 12 assets persistidos na biblioteca cloud.
- 8 verticais nativos 9:16.
- 4 horizontais para reenquadramento.
- Bytes baixados diretamente dos CDN persistidos foram verificados com `sha256sum`.
- QA visual feito por quadros de início/meio/fim com `ffmpeg`; crop 9:16 testado em V09–V11.
- Os hashes abaixo identificam os arquivos baixados no QA local desta execução; qualquer novo download deve ser re-hasheado.
- Nenhum crédito foi consumido.

## Registro de direitos e integridade

| Asset | Página Pexels | Cloud asset ID | Dimensão | Duração | SHA-256 | QA visual |
|---|---|---|---:|---:|---|---|
| S13-V01 | https://www.pexels.com/video/a-sunrise-over-a-city-with-fog-and-trees-18310302/ | e4f8059a-5773-487d-8fb5-a769bf1dbf22 | 1080x1920 | 16.983s | 0cfd29c326baa12095ef001ff02a0cdb789e009435a9ea083393618d7bd49b76 | RESERVE; próximo de V02/V03 |
| S13-V02 | https://www.pexels.com/video/a-sunrise-over-a-field-with-trees-and-houses-18675414/ | 096d4719-2826-4cce-ab34-456a75b40cd8 | 1080x1920 | 33.967s | 2df5b56bd864ac24f4ea8999ff53dee4fb668d940fd712e52b6692abc0a2996d | PRIMARY |
| S13-V03 | https://www.pexels.com/video/the-sun-is-shining-through-the-trees-and-fog-18675419/ | 75ad51e6-333a-4a65-ab9f-432fa929fb64 | 1080x1920 | 46.045s | 3de4ccf81be8b035460a754d181587a78ef1a1673f9e08db5099b8b5038a5732 | PRIMARY |
| S13-V04 | https://www.pexels.com/video/cinematic-timelapse-of-misty-morning-sunrise-34142319/ | 349f6fa3-7e09-42ef-a421-ca82f63b0743 | 2160x3840 | 15.015s | 12196992478243396f3d7dc51fc641febf95ea4dab9c1a88ae24607f5c0f10a2 | RESERVE; normalizar se usado |
| S13-V05 | https://www.pexels.com/video/tranquil-water-surface-with-gentle-ripples-32241480/ | a033e3ed-2ff5-40c5-be64-a7b7f2f8b938 | 1080x1920 | 15.283s | fda2189a525b593d452a70178340c98eaa2fae584f2b1608a07bff14c26e936d | PRIMARY |
| S13-V06 | https://www.pexels.com/video/serene-water-ripples-with-reflective-textures-34922859/ | 96b00bc6-2f6d-4928-960f-183c50d0a2b9 | 1080x1920 | 11.960s | 95d3c8ca9ba96d76872c419fb6a203a61d22381ca662601fc086e6b652c51a33 | RESERVE; alternativa a V05 |
| S13-V07 | https://www.pexels.com/video/serene-misty-forest-morning-38731245/ | 9b5776a3-7077-435d-929a-e803f4cc9311 | 1080x1920 | 37.333s | b0a9a28fa9bd26f095478f07000e0c4f7ccc67b56b358681d9e1d5f5a1b5f6d9 | PRIMARY |
| S13-V08 | https://www.pexels.com/video/morning-sunlight-shining-through-tree-branches-in-the-countryside-15365452/ | 54a69792-811b-499c-8578-96fb3ca74379 | 1080x1920 | 12.412s | 09e02289de47448d10335c48508a542d2683274ba60dabd9ba4bc7f99e0194d8 | PRIMARY |
| S13-V09 | https://www.pexels.com/video/misty-forest-pathway-in-early-morning-light-31808103/ | 6084c1ca-c0b8-4435-830b-0d8b3445bcf3 | 1920x1080 | 24.658s | 4963af9c461d7226684ec04959e436d018c1bd9bd33d58990b9f33a53f02f418 | PRIMARY; crop 9:16 testado |
| S13-V10 | https://www.pexels.com/video/foggy-forest-during-early-sunrise-5487156/ | 3be67dab-9912-4049-b197-7300ffdb8489 | 1920x1080 | 17.483s | 756201f0ccd5d570a1eeeb5f26b0d6ccfa607ea28cbe83658cd3f6884606c388 | PRIMARY; crop 9:16 testado |
| S13-V11 | https://www.pexels.com/video/forest-path-on-misty-morning-5518075/ | fed92381-3ebc-49f3-9058-713515f7a546 | 3840x2160 | 10.427s | 53c2a66751fd64e6ac9c22a2a9c330eae8f72bf090c7e83055ea399a3c80d3dc | PRIMARY; crop 9:16 testado |
| S13-V12 | https://www.pexels.com/video/view-of-an-empty-road-at-dawn-3150352/ | cedae517-719a-47ae-b202-c4e24e592c0b | 4096x2160 | 10.640s | 703163d43b6f35eb4f1a27ae653ea9c275b67233f934516e92075c2c0e2d562f | REJECTED_HARMONY; não usar |

## Invariantes bloqueantes

- Nenhum clipe pode repetir no mesmo vídeo.
- Crop, zoom, velocidade, espelhamento, reversão ou cor não criam um novo clipe.
- Cada plano final deverá registrar asset, origem, hash e intervalo temporal.
- Qualquer repetição ou divergência de hash bloqueia a aprovação.
- Licença Pexels não cobre automaticamente elementos de terceiros dentro do quadro.
- O vídeo só pode seguir para publicação após revisão final de direitos e QA de exportação.

## Pendências

1. escolher a ordem e os intervalos dos oito assets PRIMARY;
2. revisar logos, marcas e pessoas identificáveis nos trechos exatos;
3. normalizar/cortar somente os assets usados;
4. gerar narração comercialmente autorizada;
5. inserir trilha e legendas;
6. executar QA final e manter publicação bloqueada até aprovação do proprietário.


## Master associado

- Arquivo: salmo13_pilot_master_v1.mp4.
- Oito assets PRIMARY usados uma vez cada.
- O master é apenas PREVIEW_READY: o ledger de direitos não autoriza publicação.