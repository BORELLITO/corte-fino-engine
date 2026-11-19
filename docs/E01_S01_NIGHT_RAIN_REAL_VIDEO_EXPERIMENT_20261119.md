# E01 / S01 — chuva noturna como alternativa cinematográfica (pesquisa física)

**Data:** 19/11/2026. **Escopo:** VERBO_NO_CHAO_EXCLUSIVO, Habacuque 1:2–4. **Resultado:** PR candidata de revisão, **nenhum master aprovado ou publicado**.

## Decisão e motivo

O storyboard canônico mantém a cena S01 0–5,74 s com pessoa anônima, quarto escuro, janela chuvosa e caderno fechado. Depois de testes e rejeições de stock independentes (PRs #57, #59, #60), foi investigada **uma alternativa deliberadamente simbólica**: um take de chuva noturna pelo vidro de uma janela do metrô, sem apresentar personagens ou objetos que finjam estar no mesmo quarto. Essa alternativa não substitui o storyboard enquanto não houver aprovação estética do proprietário.

Fonte oficial: [Pexels #31069867, Zeki Okur — Raindrop Reflections on Nighttime Metro Glass](https://www.pexels.com/video/raindrop-reflections-on-nighttime-metro-glass-31069867/). Página: uso livre indicado, vertical 2160×3840, duração 24 s, 50 fps. Licença geral: https://www.pexels.com/license/; **direitos individuais de marcas, pessoas e demais elementos seguem sem liberação**. O site não comprova independentemente a origem de captura por câmera; o teste prova bytes reais de vídeo temporalmente decodificáveis, não método de produção anterior do autor.

## Produção física (sem geração de IA pelo motor)

- [GitHub Actions run 44638759167](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44638759167) — `SUCCESS`.
- Download com Pexels strict redirect allowlist existente e limitação a 160 MB; **93.575.530 bytes**.
- SHA-256 do original: `fc36bb6b4039e307828d9ad0acabdb54a1baa4cb6e9d41f2889d2278be7c6df8`. H.264, 2160×3840, 24,000s. FFmpeg **decodificou o stream completo**.
- Três instantes reais de 0,5 / 2,8 / 5,4 s, diferenças médias de luma de frame 14,09 e 12,57, indicando mudança temporal perceptível. **Isso não equivale a auditoria visual segundo a segundo**.
- Prévia derivada e com marca **PREVIA DE QA - NAO PUBLICAR**, sem áudio/legendas: **720×1280, 30 fps, 173 frames, 5,766667 s, 1.516.275 bytes**.
- SHA-256 da prévia: `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`.
- SHA-256 da folha de contato: `35638af1e60c9c450140175965033a809e2ade83b6893cb28ff82cf2d10147ba`.
- Após baixar o artefato, **ffprobe, hash e decodificação completa da prévia também foram repetidos em execução local independente, com PASS**. ZIP testado sem erro; nenhum MP4 original foi colocado em GitHub ou Library.

## Avaliação editorial independente dos três quadros

**Pontos positivos:** chuva no vidro em movimento real, noite de cores azuladas, áreas de sombra adequadas ao texto introspectivo, único ambiente visual, sem troca de ator. Formato fonte vertical nativo.

**Riscos e divergências:** vista de transporte urbano, não `ROOM_A`; ausência de pessoa sentada e de caderno fechado; ênfase em luzes azuis da cidade pode afastar a paleta original; silhuetas ou marcas precisam de revisão integral. **CANDIDATO PARA ANÁLISE ESTÉTICA**, e NÃO liberação de direitos/master.

O contraste visual deve resultar de arte final e do roteiro, nunca fingir que o metrô é a mesma residência das demais cenas, nem inserir referências bíblicas históricas sem base.

## Estado imutável e travas

`contracts/e01_s01_night_rain_physical_visual_review_20261119_v1.json` contém hashes, contagens e identificação da prova física. O storyboard, locução, 28 legendas, roteiro e áudio v2 **não foram alterados**. Os testes de identidade/publicação/rights/frames exigem `publication_authorized=false` e `master_allowed=false`.

Arquivos de evidência preservados na **Biblioteca pessoal privada do ChatGPT**:

`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S01_31069867_PREVIA_SIMBOLICA_NAO_APROVADA.mp4`

`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S01_31069867_FOTOGRAMAS_QA.jpg`

`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S01_31069867_RELATORIO_FISICO.json`

**Próxima ação:** testar a aceitabilidade artística desta nova tese ANTES de aplicá-la às demais cenas; somente após decisão humana expressa considerar storyboard alternativo versionado, direitos específicos, mix/legendas e master final. Não realizar merge/publicação/gastos sem autorização. O ramo é descartável (rollback: fechar PR sem merge).
