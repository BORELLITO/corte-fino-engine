# E01 v2 — Layout de legenda v3c (lilás, fonte grande, zona segura)

Estado: **IMPLEMENTADO e TESTADO (unitário + render libass com tempos simulados). NÃO APROVADO. NÃO PUBLICADO.**
Cor lilás `#C4B0F2` é provisória; a cor final de identidade é decisão do usuário.

## Especificação
- PlayRes 1080×1920; fonte Atkinson Hyperlegible Next Bold (OFL, `assets/fonts/`, sha pinado), ASS 107 (em 76 px).
- Texto até 700 px por linha, margens laterais 180 px (x útil 180–900), margem inferior 576 px.
- Máx. 2 linhas, até 7 palavras por legenda (média ≈ 4); 1 linha só com ≤ 3 palavras.
- Karaokê `\kf` por palavra: duração = fim − início ASR; lacunas em `\k`; arredondamento a partir do tempo absoluto (sem deriva).
- Cores ASS: cantado `&H00F2B0C4`, a cantar `&H00EEF1F2`, contorno `&H00141210`.

## Provas (esta branch)
- 487 testes unitários passam.
- Render libass (tempos SIMULADOS): preenchimento lilás = 0 antes de cada palavra, cresce só durante ela, estável nas pausas, completo no fim; bbox x 199–878; base do texto ≥ 593 px da borda inferior.

## NÃO VERIFICADO
- Sincronia com a voz real (artefato ASR `e01-v2-caption-timeline.json` não baixado; egress bloqueado).
- Mapeamento Reels/Shorts (cover-fit assumido) e outros tamanhos de celular.
- Leitura por idosos em aparelho real.

## Mudanças que afetam decisões anteriores
- As 28 legendas originais viram ~44 com a fonte maior (evidência antiga em `contracts/e01_v2_caption_qa_real_evidence_v1.json` mantida intacta, é histórica).
- Legenda ocupa até ~y 1080–1344; o gate visual (`safe_zone_bottom_px=380`, "420px") NÃO foi alterado: decisão pendente do usuário.
