# E01 / S02 — Continuidade de luz e cor a partir da S01 aprovada

**Data:** 19/11/2026 • **Canal:** VERBO_NO_CHAO_EXCLUSIVO • **Escopo:** somente S02 • **Estado:** `PHYSICALLY_VERIFIED_S02_COLOR_QA_EDITORIAL_PENDING`.

## Conclusão da intervenção

A S01 (chuva noturna Pexels #31069867) recebeu aprovação estética específica do usuário; a S02 (relógio analógico real Pexels #7034348) ainda não recebeu. O principal problema do corte S01→S02 era o mostrador branco, com brilho médio visualmente muito acima da S01. Testei **duas graduações simples feitas apenas por FFmpeg**, preservando o vídeo temporal real, sem IA, sem nova aquisição e R$0. Selecionei **S02 GRADE A** por combinar mais com a S01 azul-noturna.

Não modifiquei os arquivos da S01 aprovada; o composto é **uma nova recodificação de QA**, e portanto não alego identidade de pixels entre sua parte S01 e a referência originalmente aprovada. A montagem mantém a composição e o recorte S01 (172 frames), sem correção tonal aplicada nela.

## Dados físicos e prova independente

Vídeos de referência originais: S01 SHA-256 `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`; S02 SHA-256 `31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786`. As entradas estão fisicamente preservadas na Biblioteca privada. A S02 vem de filme stock original nativo 1080×1920, mas esta variação usa **apenas a prévia de 720×1280**; **NÃO** é fonte de master em 1080×1920 e não deve ser ampliada para fingir qualidade nativa.

Tratamento S02 selecionado (sem aplicar ao vídeo S01):

```text
eq=contrast=0.88:brightness=-0.035:saturation=0.65:gamma=0.64,colorbalance=bs=0.10:gs=0.04:rs=-0.01,vignette=PI/7
```

Medidas com frame central amostrado em 2,3 segundos de cada fonte (escala comum, não equivalentes a aferição científica de exposição fotográfica):

| Amostra | Luma média no quadro |
|---|---:|
| S01 aprovada, 2,3s | 29,60 |
| S02 original, 2,3s | 70,16 |
| S02 corrigida A, 2,3s | **34,28** |
| S02 B (mais clara, **não selecionada**), 2,3s | 48,92 |
| Corte conjunto antigo, 5,95s | 61,79 |
| Corte conjunto corrigido, 5,95s | **30,69** |

**S02 corrigida A:** 720×1280, **147 frames**, 30 fps, 4,900 s, H.264, sem áudio, 277.678 bytes, SHA `0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3`. Amostras de movimento entre 0,5→2,4 e 2,4→4,5 s: luma de diferenças **12,49** e **12,94**, confirmando mudança de quadros (não uma foto fixa).

**Corte S01 + S02 A:** 720×1280, **319 frames**, 30 fps, 10,633333 s, H.264, sem áudio, 2.906.687 bytes, SHA `598675e1e00b2a27880080bdd0052f6bc8ab8ae408d80be2272aeabd1eeae4ae`. Mapeamento exato: S01 [frame 0,172) + S02 [frame 0,147); **não** somar as prévias sem adequar a S01 ao corte de 5,74 s da locução.

**Comparação de quadros:** `S01_S02_GRADE_A_CUT_COMPARISON.jpg`, SHA `0f2f24d81927fb5fbe16b1c216d3b89c5218967b0c9c7012ebabf95aeb8fe146`. Hashes de entradas, hashes dos derivados, duração, FPS, contagem de quadros e decodificação FFmpeg integral **verificados no ambiente local**, com relatório `S02_GRADE_A_PHYSICAL_QA.json`.

## Riscos identificados e não mascarados

- A S02 continua um relógio com mostrador e numerais; **a palavra `QUARTZ` ainda aparece**, e o centro/lower-center deve ser testado com as legendas reais.
- Mudança do storyboard original (mão no relógio/mesa) ainda está pendente de aprovação S02; a aprovação dada para S01 **não é aprovação automática da S02**.
- Escurecer as altas luzes melhora a transição, mas não equivale a verificação legal de direitos de pessoas, marcas, tipografia ou uso específico da licença Pexels.
- Não foi realizada auditoria quadro a quadro, nem sincronização das 28 legendas ou mix da locução. Não declarar master, licenças, publicação nem merge.
- A alternativa encontrada na pesquisa, [Pexels #30084927](https://www.pexels.com/video/vintage-alarm-clock-ticking-in-darkness-30084927/), é horizontal 1920×1080, **sem 1920 px de altura nativa para entregar 1080×1920 sem upscale**, então não foi preferida ao stock vertical real existente.

## Reprodutibilidade e arquivos preservados

`agents/e01_s02_color_continuity_qa_v1.py` oferece **reprodução local a partir das entradas MP4 físicas** com SHA obrigatório, FFprobe para confirmar único stream de vídeo sem áudio, FFmpeg para grade exclusiva na S02, recorte em quadros e decodificação integral. O arquivo não faz download, não muda o branch operacional e não pede credenciais ou upload. Os testes de regressão de `tests/test_e01_s02_color_continuity_qa_v1.py` incluem falsificação de SHA, direitos, flag de master, aprovações e ausência de fontes. Execução do **motor novo** de ponta a ponta deve ser validada no ambiente que tiver acesso aos dois MP4s; a montagem física anterior foi validada localmente com os mesmos parâmetros.

Persistência **privada e comprovada** na Biblioteca pessoal ChatGPT:

```text
/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_WAITING_CLOCK_REVIEW/S02_COLOR_MATCH_V1/
  S02_CLOCK_COLOR_GRADE_A_UNAPPROVED.mp4
  S01_S02_TRANSITION_GRADE_A_UNAPPROVED.mp4
  S01_S02_GRADE_A_COMPARISON.jpg
  S02_GRADE_A_PHYSICAL_QA.json
```

A branch da pesquisa e sua PR permanecem em **DRAFT / NO MERGE**. Próxima decisão: avaliação estética desta **nova S02 graduada**, não do seu contrato ou autorização de publicação. Se o relógio continuar excessivamente literal, buscar outra cena de tempo/espera antes de iniciar a S03.

**Critérios invariáveis:** conceito S01 aprovado; S02 candidata, direitos pendentes, master bloqueada, publicação bloqueada.
