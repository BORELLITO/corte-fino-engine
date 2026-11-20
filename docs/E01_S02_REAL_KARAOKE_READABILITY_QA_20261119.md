# E01 S02 — QA físico de legibilidade com as 28 legendas reais

**Estado:** S01 visual aprovado; S02 **CANDIDATA NÃO APROVADA**.  
**Data:** 19/11/2026, America/Sao_Paulo · **Escopo:** VERBO NO CHÃO E01 (Habacuque 1:2–4).

## Decisão operacional

A S02 com relógio (#7034348) na GRADE A tem iluminação mais coerente com S01 que alternativas testadas, mas o mostrador claro atravessa a região inferior em que as legendas se apoiam. Não adivinhar legibilidade por luminância média, nem simplesmente continuar escurecendo a imagem inteira.

Foi recuperado o **artefato real do E01 v2 de ASR/legendas**: [Actions run 44208934506](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44208934506), artifact #14385236602, ainda válido em 19/11/2026. ZIP SHA256 `2ea85dba50b4b91d71e4ff53a99b80cf0170ba042080322d435379686d0f8e64` e integridade ZIP **PASS**. Arquivos originais físicos confirmados por hash:
- ASS karaoke QA, **28 cues**, `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`;
- SRT, `503eb0119c386096fbdb7e6c671828682b3390328d15cfded95b2d0ae383556d`;
- timeline JSON, `cac98a9c82dfbcdc0d77c204733d31f3568bc1b5991bcbe2d5b5fc0c9aa5d53e`.

A **versão original do ASS foi aplicada SEM ALTERAÇÃO** à transição validada S01+S02 Grade A, exatamente 172+147=319 frames / 10,633333 s a 30 fps. A prévia resultante (720×1280, sem áudio, com dupla marca de QA) teve SHA `8ce132728c27db5dd1ce2cc6717d51ee3cd8d47cbb989081adc5c36ef2b27f3f`. Rehash, FFprobe, 319 frames, um único stream vídeo e decodificação FFmpeg integral **PASS**. Sem falsa afirmação de sincronização definitiva com áudio, pois o WAV não foi inserido.

**Diagnóstico visual:** nos instantes 6,2, 7,0, 7,7, 8,5, 9,15 e 9,8 segundos o texto karaoke real incide diretamente sobre o mostrador claro. A fonte `QUARTZ` permanece legível e compete visualmente; a faixa inferior da imagem contém números e ponteiros do relógio. A legibilidade precisa de correção específica, especialmente em tela pequena.

## Comparativo A/B/C no vídeo real

Foi testado tratamento **SOMENTE na S02**, mantendo MP4 aprovado S01 como fonte de entrada byte-identificada e ASS imutável. Overlay transparente preto com transição gradual (`smoothstep`) na faixa y=620..1279 do vídeo QA 720×1280. Duas alternativas de escurecimento do último pixel: **35%** e **55%**. O gradiente é contínuo, sem quadro opaco ou objeto adicionado. É um recurso de cor para sustentar a tipografia, não geração de cena por IA.

| Amostra (região da legenda) | Sem gradiente | 35% | 55% |
|---|---:|---:|---:|
| 6,40s, luma média | 61,87 | 49,36 | **42,67** |
| 8,60s, luma média | 66,96 | 54,40 | **47,50** |
| 9,65s, luma média | 69,86 | 57,13 | **50,04** |

Os números representam luminância média de uma faixa de análise que **inclui imagem e texto**, não são pontuação objetiva de acessibilidade. O comparativo real de nove quadros (3 tempos × 3 variações) e a prévia reproduzível sustentam uma **preferência editorial provisória por 55%**, mas **a S02 continua sem aprovação** e o relógio ainda ocupa a área da legenda. Não declarar a leitura universalmente perfeita.

**Prévia 55% com karaoke real:** 720×1280, 319 frames, 30fps, 10,633333s, 2.066.424 bytes, H.264, 1 stream de vídeo, sem áudio; SHA256 `f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c`. Full decode e SHA local PASS. Comparativo JPG SHA `89fe5ad902652167178dae58260841d0c5782747be54ea75c9072b3c095de87e`. S02-only QA video SHA `f1619ddf0857ab69b195ab81542827cc380610a10ef4a5c647ad6257e9005f3d`.

## Código para reprodução segura

- `contracts/e01_s02_real_caption_safezone_qa_20261119_v1.json`: hashes de entrada, 28 cues, geometria e flags de release bloqueadas.
- `agents/e01_s02_real_caption_safezone_qa_v1.py`: recebe `--s01`, `--s02` (GRADE A 720p), `--ass` (original da narração) e `--out`; verifica SHA de cada entrada, aprovado apenas S01, recursos, duração/frames, fonte única, gera o gradiente e o composto sem áudio; preserva ambos os originais. **Sem downloads e sem master**.
- `tests/test_e01_s02_real_caption_safezone_qa_v1.py`: rejeita falsificação de aprovação, direitos, hash, cue count, reframe, gasto, publicação e ausência de arquivos. As suites do GitHub executam testes offline; **a prévia física foi gerada e validada no contêiner do ChatGPT**. Não declarar que CI baixou conteúdos privados ou executou esse render.

A source Pexels (licença geral: https://www.pexels.com/license/) permite uso gratuito e modificação, mas direitos individuais de terceiros, marcas e representação ainda não foram homologados.

## Resiliência — preservação na Biblioteca privada

O ZIP original de QA e seus arquivos ASS/SRT/timeline (para evitar perda após retenção do GitHub Actions) foram salvos em:

`/VERBO_NO_CHAO/E01_CAPTIONS_CANONICAL_V2/`

A prévia com gradiente 55%, o JPEG A/B/C e o relatório da execução foram salvos em:

`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_CAPTION_READABILITY_20261119/`

Além disso, o bruto de vídeo Pexels #29862379 foi rejeitado especificamente para S02 na PR #64, sem afetar a S01 ou outra cena.

## Gates preservados

**APROVADO:** direção visual S01 chuva noturna, exclusivamente.  
**VALIDADO:** existência física da fonte de legendas, seus hashes, aplicação em QA, 319 quadros sem áudio e comparação de contraste.  
**PENDENTE:** S02 artística, verificação legal por fonte, master 1080×1920 a partir dos originais nativos, áudio real, sincronização final e publicação.

**Próxima decisão necessária:** avaliar a versão de 55% no vídeo completo. Sem autorização explícita de S02, manter o motor em prévia e investigar outros planos que ofereçam área de legendas menos ocupada, se preciso. Sem merge, gasto ou postagem.
