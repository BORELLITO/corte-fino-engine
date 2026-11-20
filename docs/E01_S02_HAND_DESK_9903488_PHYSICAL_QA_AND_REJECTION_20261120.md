# VERBO NO CHÃO — E01 S02: pesquisa física Pexels #9903488 e veto editorial

**Data:** 20/11/2026 · **Projeto:** `VERBO_NO_CHAO_EXCLUSIVO` · **Fonte operacional histórica:** `verbo-no-chao/e01-stock-curation-gate-v1` · **Estado:** QA em branch isolada, sem master, merge, gasto ou publicação.

## A pergunta correta

A cena S02 do storyboard canônico, **“A dor da espera” (5,74–10,62 s)**, pede **mão do mesmo protagonista anônimo, casaco escuro, repousando sobre mesa de madeira gasta, relógio analógico discreto, luz quente nas pontas dos dedos**, com um movimento lateral sutil e espaço limpo para legendas. A S01 de chuva noturna é uma exceção simbólica aprovada visualmente; esse aceite não se estende para S02.

A opção anterior #7034348 oferece relógio preto real em movimento, mas é um primeiro plano dominado por números e `QUARTZ`, atravessando a zona de legendas. A gradiente 55% melhorou leitura; **a S02 permanece sem aprovação do proprietário**. O novo objetivo foi procurar atividade humana real, não outra foto/slideshow de relógio.

## Fonte externa verificada, mas não aprovada como conteúdo

[Pexels, Ron Lach — “A Man Organizing the Things on His Table”, vídeo #9903488](https://www.pexels.com/video/a-man-organizing-the-things-on-his-table-9903488/). Listagem consultada: **Free, 2160×4096, 25fps, 0:32**, datada de 15/10/2021. A [licença Pexels](https://www.pexels.com/license/) informa uso e edição gratuitos em geral; não atesta especificamente direito de imagem, marcas, eventual direito de propriedade, nem igualdade de personagem.

O arquivo **foi efetivamente transferido** no [GitHub Actions run #44711536426](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44711536426), workflow one-shot, sem credenciais nem serviço de geração. A origem HTTPS foi limitada por `StrictPexels` ao redirecionamento `videos.pexels.com/video-files/9903488/...mp4`. Source: **60.515.189 bytes, H.264, 2160×4096, 32,36s**, SHA `ab34b60af5d700e94fc70fc19982ff974a3c52c3a6484ce4a48ce07c965d1d86`. Por estar vertical, o recorte nativo 9:16 é **2160×3840**, suficiente para 1080×1920 sem upscale (isso não autoriza exportar master de fonte ainda não liberada). **Não foi executado um decode integral do original de 32,36 s**: o que foi validado integralmente é a prévia curta.

**Preview físico isolado:** `S02_HAND_DESK_9903488_QA_NOT_MASTER.mp4`, **720×1280, 30fps, 147 frames, 4,9s, 476.674 bytes**, sem áudio e com aviso de QA. SHA `af604d62cc899206e341dd569897a5f5dc82d724f9cd1170cff9948e903a5107`. Repetida inspeção local FFprobe/SHA e decodificação completa FFmpeg `-xerror`: **PASS**.

**Prova visual em 3 quadros reais** extraídos aos 0,5, 2,4 e 4,5 s: JPEG SHA `0802ca9e6a566c9c0c5cb0d0b8df9a3e9c2cb06c3690b5cf06adf043d64186e3`. Diferenças médias entre amostras 38,988 e 96,384, comprovando que a tomada muda visualmente (não prova autoria nem tipo de câmera). Luminâncias médias 142,97 / 145,80 / 101,42.

## Veto editorial específico: por que não avançar

Visualmente, os quadros mostram mesa **muito clara e carregada de objetos, documentos, ferramentas e frascos**, mãos escrevendo/organizando, um relógio pequeno na extremidade esquerda e pessoa com **roupa mostarda/marrom**, aparecendo também parte da cabeça/costas no último quadro. Os fatos da imagem são incompatíveis com a **noite azul/preto da S01** e com o **casaco carvão, mão repousada e ritmo contemplativo** exigidos pela S02. A atividade mostrada sugere produtividade de escritório/oficina, não espera interior. Escurecer com filtros não resolve figurino, objetos e intenção corporal.

**Veredito profissional deste candidato:** `REJECTED_FOR_S02_SCENE_FIDELITY`. É uma rejeição de curadoria **para esta cena**, não uma negativa de licença e **não é uma rejeição emitida pelo usuário**. O MP4 físico passou na engenharia, mas não se torna aceitável por causa disso. **Não aplicar essa tomada no E01 por conta própria.**

## Implementação e recuperação

- `contracts/e01_s02_human_desk_stock_preflight_20261120_v1.json`: scene_id, dados de fonte, título, plano visual, autoria, limites e flags congeladas.
- `agents/e01_s02_human_desk_stock_qa_20261120_v1.py`: download estritamente limitado, SHA, ffprobe, crop real, 3 frames, movimento amostrado, prévia marcada, full decode e JSON. Fonte original apagada do runner por diretório temporário; nunca enviada ao GitHub.
- `tests/test_e01_s02_human_desk_stock_qa_20261120_v1.py`: falsificação de direitos, aprovação, credenciais, projeto, source, sample, resolução, frames; sem rede nos testes.
- `.github/workflows/verbo-no-chao-e01-s02-human-desk-one-shot-20261120.yml`: apenas `push` na branch exata e inclusão inédita do workflow; `rev-list --count == 1` e `diff-tree` impedem replay/modificação para executar novamente, token leitura, Actions pinadas, sem cron ou `workflow_dispatch`.
- `contracts/e01_s02_9903488_editorial_rejection_20261120_v1.json`: prova e rejeição específicos, sem confundir com o histórico de outras fontes.
- `tests/test_e01_s02_9903488_editorial_rejection_20261120_v1.py`: trava de decisão e preservação de S01 e S02 anterior.

Os derivados e o JSON foram armazenados na **Biblioteca pessoal privada**, caminho `/VERBO_NO_CHAO/E01_STOCK_QA_20261120/S02_HAND_DESK_9903488_REJECTED/`. O ZIP temporário de Actions é retido por **1 dia**; o arquivo original Pexels não foi persistido.

A S01 continua aprovada **apenas visualmente**, SHA `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`. A S02 anterior #7034348 com gradiente e voz permanece em PR #65, candidata e **sem aprovação**; o resultado `979fcb7d630177efc99e76baa98adc0d34cf0d3a89beaf06484060c7bdd6e5f6` não foi modificado.

## Próxima ação independente

Pesquisar uma filmagem **noturna**, preferencialmente vertical, de mão em repouso sobre mesa, com objeto discreto que sugira passagem do tempo e sem texto/logotipos ou props modernos chamativos. A página [Pexels #36017452](https://www.pexels.com/video/nightstand-scene-with-phone-charging-and-hand-interaction-36017452/) descreve mesa de cabeceira com livro, interação de mão e iluminação noturna (listagem 3840×2160, 60fps, 10s); **apenas metadados pesquisados, sem arquivo físico examinado ou aprovação de direitos**. O foco na tela de celular e o corte vertical horizontal→9:16 podem desqualificar essa opção; não promover antes de frames reais.

**Fora de escopo:** S03–S12, IA de vídeo, assinatura paga, troca de narrador, novo roteiro, master 1080p, merge, postagem, outros motores.
