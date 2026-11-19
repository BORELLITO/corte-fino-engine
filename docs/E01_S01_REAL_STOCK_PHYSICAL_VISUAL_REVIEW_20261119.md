# VERBO NO CHÃO — S01: curadoria stock com prova física (19/11/2026)

**Protocolo:** VERBO_NO_CHAO_EXCLUSIVO • E01 Habacuque 1:2–4, 12 cenas, 70,425 segundos, 28 legendas.  
**Fase:** `S01_REAL_STOCK_EDITORIAL_SEARCH_PHYSICAL_QA_NO_MASTER`.  
**Decisão:** zero clipes liberados para a S01; duas fontes novas avaliadas fisicamente e rejeitadas para **este contexto específico**. Uma fonte bloqueada por limite de transferência não teve parecer estético.  
**Regra:** vídeo de câmera real, R$0, fonte legal, sem gerar IA, preservar narração/roteiro/ASS, sem publicar ou mesclar produção.

## Resultado executado

| Fonte Pexels | Prova | Inspeção de quadros (0,5 / 2,8 / 5,4s) | Decisão |
|---|---|---|---|
| [4510748 — Yaroslav Shuraev](https://www.pexels.com/video/woman-sitting-by-the-window-4510748/) | MP4 físico H.264, 2160×3840, 9,958 s, 27.473.889 bytes, SHA `c9893c53a3c51d9e6244e772ad16553ff3319db8b7bd070a9744800f316a2fa0`, decode completo | Janela branca iluminada como dia, não ambiente chuvoso noturno; sem caderno fechado; variações médias de quadros 0,78/0,83 (praticamente estático nesses intervalos) | **REJEITADO PARA S01** |
| [28174743 — PinkWitch](https://www.pexels.com/video/a-woman-is-sitting-at-a-desk-in-front-of-a-window-28174743/) | Download excedeu limite vigente de 160 MB; nenhum arquivo íntegro/sha final; erro `oversized_source` | **Não avaliável**: não afirmar que é visualmente inadequado nem que o vídeo é falso | **BLOQUEADO TECNICAMENTE / INDETERMINADO** |
| [7026683 — George Milton](https://www.pexels.com/video/a-woman-writing-on-the-notebook-7026683/) | MP4 físico H.264, 2160×3840, 10,01 s, 25.994.187 bytes, SHA `53bc1ff9d0a34528b12c7f0095e2ed61797943391ddf900ab740b1949c38a7dc`, decode completo | Rosto frontal visível, paredes claras, laptop, caderno aberto; vela pequena não torna a cena noturna; movimento físico entre os três frames (diferenças 7,51/8,81) | **REJEITADO PARA S01** |

**Provas nos GitHub Actions:** [run 44630205186](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44630205186) falhou na segunda fonte (reportou primeira física); [run 44630728010](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44630728010) preservou a primeira folha de contato com status `BLOCKED_PARTIAL_PHYSICAL_QA_EDITORIAL_RIGHTS_PENDING`; [run 44631386851](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44631386851) concluiu `SUCCESS` técnico para #7026683 com status `PHYSICAL_SINGLE_TAKE_CANDIDATES_READY_FOR_HUMAN_FRAME_REVIEW_ONLY`. Esta revisão editorial foi feita **depois**, observando a folha de contato real, e consta em `contracts/e01_s01_single_take_physical_editorial_decisions_20261119_v1.json`.

**Guardião de direitos:** a [licença Pexels](https://www.pexels.com/license/) permite usos gratuitos, incluindo redes sociais e modificação, mas proíbe retratar pessoas identificáveis ofensivamente ou implicar endosso. A utilização específica de qualquer item, voz e trilha ainda requer avaliação — **nenhum direito individual foi declarado liberado**.

## Evolução técnica mínima na branch candidata

- `contracts/e01_s01_single_take_stock_candidates_20261119_v1.json`: fotografia original da pesquisa, duas fontes, sem prova antecipada.
- `contracts/e01_s01_single_take_stock_candidates_20261119_v2.json`: única alternativa curta #7026683, fotografia pré-QA preservada, não autorização.
- `agents/e01_s01_single_take_stock_qa.py`: reutiliza o downloader Pexels com redirect estrito do motor; calcula recorte físico nativo, FFprobe e decodificação integral via FFmpeg. Captura três quadros de um **único take** sem criar câmera falsa, monta contatos reduzidos e registra luma/movimento. Um erro em outra fonte não descarta a evidência da fonte verificada, mas mantém CI vermelho para execução incompleta.
- `.github/workflows/verbo-no-chao-e01-s01-single-take-stock-qa-20261119.yml`: gatilho somente ao alterar o **próprio workflow** na branch isolada; sem cron, `workflow_dispatch`, GPU ou uploader de master. Artefatos têm retenção de um dia; nenhum MP4 bruto vai para GitHub ou Drive.
- `tests/test_e01_s01_single_take_stock_qa.py`: negativos de identidade, URLs, estado de direitos, dimensões/crop nativo, ausência de mídia e autorização inexistente.
- `contracts/e01_s01_single_take_physical_editorial_decisions_20261119_v1.json`: registro final das decisões com hash e fontes. Status deste registro **prevalece** sobre os manifestos de pesquisa pré-QA.

## Mídia probatória durável

As duas folhas de contato e dois relatórios JSON (sem vídeos brutos) foram preservados na **Biblioteca pessoal privada do ChatGPT** em:

`/VERBO_NO_CHAO/E01_STOCK_QA_20261119/`

- `S01_4510748_REJEITADO_FRAMES.jpg`
- `S01_7026683_REJEITADO_FRAMES.jpg`
- `S01_4510748_E_28174743_RELATORIO.json`
- `S01_7026683_RELATORIO.json`

A pasta não é um Drive nem pública. Uma tentativa de transferência dos ZIPs por handoff do conector GitHub → Drive falhou por incompatibilidade do argumento de referência, portanto **não afirmar que esses ZIPs foram enviados ao Drive**. O GitHub armazena hashes, relatórios/dossiês e fontes; a Biblioteca possui os quadros derivados reais.

## Critério de próxima aquisição

**Não gastar mais tempo com cenas já conhecidamente inadequadas:** para S01, buscar um take *real e único* de pessoa anônima junto à janela noturna/chuva, iluminação cálida neutra, **caderno fechado**, rosto não reconhecível, movimento visível, 5,74 s contínuos, recorte 9:16 fisicamente suficiente e sem marca.  
Se a combinação exata não existir em estoque gratuito, documentar uma **alternativa simbólica** para avaliação estética antes de mudar o storyboard. Não misturar autores e afirmar que são o mesmo personagem.  
Priorizar **avaliação de fotogramas antes de render**, não novos sistemas nem sucessivos testes de vídeo inviável. Para fontes imensas, procurar variante segura legal e com pixels suficientes antes de elevar indiscriminadamente o teto do downloader.

**Sem merge ou publicação autorizada.** Master 1080×1920, música, licenças, voz e legenda continuam bloqueados até evidência e aprovação finais.
