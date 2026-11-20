# ESTADO_ATUAL.md — CANAL VERBO NO CHÃO

**Corte de continuidade:** 19/11/2026 — America/Sao_Paulo.  
**Natureza:** checkpoint documental auditado; **não é aprovação de arte, master, merge ou publicação**.  
**Projeto:** VERBO_NO_CHAO_EXCLUSIVO. Não misturar com Corte Fino, CaptaPronto ou outros motores.  
**Fonte de verdade técnica para esta fotografia:** GitHub conectado, repositório atualmente denominado [BORELLITO/verbo-no-chao-engine](https://github.com/BORELLITO/verbo-no-chao-engine).  
**Branch operacional observada:** verbo-no-chao/e01-stock-curation-gate-v1, HEAD db6e1d4acf23e82793f6230535a1716842ba5cd0.  
**Branch deste documento:** verbo-no-chao/continuity-state-20261119-v1, derivada do HEAD operacional; PR documental em rascunho, sem merge.

> ATENÇÃO: este arquivo é uma fotografia com fontes e limites; os contratos, a mídia física e as decisões humanas validadas prevalecem sobre qualquer resumo. Atualizar após novas aprovações, merges ou provas.

## 1. Missão, identidade e regras preservadas

- Conteúdo cristão original, sóbrio, contextualizado biblicamente, sensível à dor humana, sem prometer milagre ou resposta garantida.
- Vídeos cinematográficos **reais em movimento**, não slides com zoom/pan vendidos como vídeo capturado; texto bíblico, paráfrase e opinião interpretativa devem ser diferenciados.
- Prioridade atual de aquisição indicada pelo usuário: **vídeos prontos de bancos de filmagem**, gratuitos e legalmente utilizáveis. Geração por IA não é necessária neste estágio.
- Preferir R$0, sem chave/API paga, sem assinatura, sem login automatizado como dependência, e não depender do TinyFish.
- Não efetuar gasto, postagem, contato externo, mudança sensível, autorização de rights ou merge de produção sem aprovação específica. Nunca inferir autorização de CI verde, prova física ou ausência de objeção.
- Salmo 13 é piloto/outro conteúdo e deve permanecer isolado do E01 sobre Habacuque.

## 2. Inventário editorial e contrato existente

- E01: **Quando você pergunta e nada muda**, Habacuque 1:2–4.
- E01 v2: **12 janelas de cena de 0 a 70,425 s**, **28 cues** de legenda; narração preservada no contrato.
- SHA-256 do roteiro registrado no contrato: c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6.
- SHA-256 do WAV registrado no contrato: 4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e.
- SHA-256 ASS registrado no checkpoint anterior: 0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a. **Este registro não substitui rehash físico atual**.
- Meta final registrada: **1080 × 1920, 9:16, 30 fps**; reservar **380 px inferiores** para safe zone de legendas, e auditar legibilidade e cortes reais.
- Rough cut antigo: vídeo 720×1280 com imagens e zoom/pan simulado; foi documentado como prova de montagem, **não** master de filmagens reais.
- Plano visual da branch operacional: oito tomadas ROOM_A com mesmo ator/casaco/caderno/mesa/janela e quatro exceções; ativo ainda como **referência aprovada/planejada**, não como stock obtido. O contrato de cenas registra fontes como não liberadas.
- Rota alternativa da PR #57: montagem simbólica com vídeos independentes, **PROPOSTA EDITORIAL NÃO APROVADA**. A preferência do usuário por bancos prontos não aprova automaticamente romper a continuidade do storyboard.

## 3. Histórico reconciliado (não confundir evidência com intenção)

1. **17–18/11 — PR #41:** curadoria e QA de MP4 Pexels, FFprobe, hashes, decodificação, direitos e rejeições explícitas. Stock genérico foi testado fisicamente, mas não aprovado para master.
2. **18/11 — E01 v2:** rough cut de 12 cenas com fontes visuais parcialmente derivadas de imagens; prévia técnica, não filmagem real nem final.
3. **19/11 às 09:51:44Z — PR #49 MERGED** exclusivamente na branch operacional VNC, commit db6e1d4acf23e82793f6230535a1716842ba5cd0. Reúne gates de integridade/anti-replay, correções de mídia e rejeições editoriais S03/S04/S10; **não equivale a merge em main ou à publicação**.
4. **19/11 — PRs #50–#56:** pesquisas e tentativas isoladas (Flow, Agnes, LTX, stock S01 e contenção de workflows legados). Em consulta atual permaneceram em DRAFT/OPEN. Seus resultados não substituem o HEAD operacional.
5. **19/11 às 21:11Z — PR #57 DRAFT/OPEN:** shortlist de stock para 12 cenas; código para ingestão e montagem real da abertura. Base db6e1d4a, head **1db7a29f027d551d81bfd6a5e83fed8c1b66f06d** após reconciliação documental, **não mesclada**.
6. **19/11 — opção reafirmada pelo usuário:** priorizar vídeos prontos de bancos online, preservando R$0 e qualidade cinematográfica. Aprovação de fonte de mídia ≠ aprovação de uma nova linguagem de montagem.

**Mudança de nome do repositório:** a consulta ao identificador legado BORELLITO/corte-fino-engine retornou via redirecionamento o repositório 1400839762, atualmente **BORELLITO/verbo-no-chao-engine**. Atualizar referências operacionais futuras; **não editar URLs/arquivos históricos automaticamente**.

## 4. Provas recentes — o que foi executado e o que não foi

### PR #57 — abertura S01 com stock real

- V1: três fontes reais em 5,767 s, 720×1280/30fps, prova no [GitHub Actions run 44614902739](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44614902739), conclusão **SUCCESS**. **REJEITADO VISUALMENTE**: escrita na parede e caderno muito claro.
- V2: duas fontes reais em 5,767 s, 720×1280/30fps, SHA-256 registrado **2c099db52b219cb901977d98fac29f91579a4be1d9a2126f4ff6ba0cbcc7c1e5**, prova no [run 44615672379](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44615672379), conclusão **SUCCESS**. **REJEITADO PARA MASTER**: janela clara/diurna versus chuva noturna, caderno ausente e mundo visual incoerente.
- S01 V2 **não** contém locução nem legendas incorporadas, não tem licenças individuais totalmente concluídas, não corresponde à dimensão final e não é um master.
- [Engine Gates run 44616216856](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44616216856) e Eight Specialist Audits run 44616216850 no HEAD PR #57: **SUCCESS**. Prova CI técnico, não aprovação artística.
- Um ZIP V2 foi confirmado por metadados no **Drive privado em quarentena**, propriedade do usuário, não compartilhado publicamente naquele snapshot. Não publicar link/ID de Drive privado em código público.
- Antes da correção, Engine Gates falhou no commit f85660b; commits seguintes em PR #57 tiveram sucesso. Não reabrir erro passado como falha corrente sem evidência.

### Direito e QA

- A licença geral de Pexels/Mixkit permite certos usos comerciais, mas não libera automaticamente marcas, rostos, retratos em contextos negativos, vozes e músicas. Revisão por asset ainda **PENDENTE**.
- Correção estética e continuidade de S01 e demais onze cenas **PENDENTES**. O sucesso do download/FFmpeg não autoriza montagem final.
- MASTER_1080X1920 = BLOQUEADO. PUBLISH = BLOQUEADO. Direitos de voicepack/trilha e QA do áudio final = PENDENTES.

## 5. Auditoria de riscos priorizada

| ID | Gravidade | Classificação | Evidência / falha | Ação mínima |
|---|---|---|---|---|
| VNC-P0-01 | P0 | COMPROVADA | Sem master, direitos de terceiros/voz/trilha e aprovação de publicação | Manter publicação bloqueada, revisar todos os direitos antes de lançamento |
| VNC-P1-01 | P1 | COMPROVADA | S01 V1 e V2 fisicamente renderizadas, mas rejeitadas visualmente | Curar nova abertura REAL com coerência de noite/chuva/personagem/ação |
| VNC-P1-02 | P1 | COMPROVADA | PR #57 propõe multi-stock simbólico enquanto contrato anterior fixa ROOM_A com personagem único | Não promover plano alternativo sem aprovação estética expressa |
| VNC-P2-01 | P2 | COMPROVADA — **CORRIGIDA EM PR #57 DRAFT** | Shortlist antes citava Pexels 32788087; código piloto V2 usa IDs **8860242 e 4458845** | Shortlist alinhada + teste anti-regressão; ainda não é aprovação de mídia ou merge |
| VNC-P2-02 | P2 | COMPROVADA | Prévia S01 real tem 720×1280 e 5,767s, versus meta final 1080×1920 e janela S01 de 5,74s | Separar preview técnico e master; validar cortes exatos e material nativo na seleção final |
| VNC-P2-03 | P2 | HIPÓTESE | Link/ID de Drive privado consta na descrição pública da PR #57; metadados indicam acesso restrito | Revisar necessidade de expor o identificador, sem mudar permissões da pasta |
| VNC-P2-04 | P2 | HISTÓRICA | Áudio v2 tinha alerta de ASR sobre uma palavra, ainda sem prova de erro acústico ou aprovação final | Revalidar audição e licença quando chegar ao mix final |

## 6. Fonte de verdade por camada

- **Código e branches:** repositório GitHub atual; PR #41 HEAD db6e1d4a e PR #49 integrada; PR #57 apenas proposta.
- **Plano de cenas:** contracts/e01_v2_12_scene_visual_plan_v1.json e contracts/e01_v2_visual_single_world_acquisition_v1.json.
- **Shortlist nova / alternativa:** docs/VNC_E01_STOCK_FIRST_EDITORIAL_SHORTLIST_20261119.md na PR #57, **não** canônica.
- **Render piloto:** agents/e01_s01_multi_stock_pilot_v1.py, workflow dedicado e testes no HEAD da PR #57.
- **Evidência física antiga:** docs/E01_V2_REAL_VISUAL_ROUGHCUT_AND_BACKUP.md; não afirmar que todos os arquivos privados estejam montados no runner.
- **Contexto normativo:** arquivo 05_PROMPT_MASTER_VERBO_NO_CHAO_V2.txt presente na biblioteca, SHA histórico registrado no GitHub 28cba0f640cad30d30e194304bd0963b8761158b4200a7d29efe8cf7e032632e. O PROTOCOLO MASTER V4 desta conversa governa **recuperação/continuidade**, não reescreve sozinho o MASTER OPERACIONAL V2.
- **Drive:** mídias e prévias privadas, sem presumir que URLs ou arquivos estejam acessíveis externamente.
- **Automação antiga:** tarefa VERBO NO CHÃO • S01 reteste gratuito foi encontrada **desativada**; não reativar nem criar retries sem objetivo e autorização.

## 7. Próximo passo prioritário e critérios de aceitação

**Prioridade única:** desenvolver **uma S01 stock-first cinematograficamente coerente** usando material real de mesma sessão/fonte (ideal), ou montagem simbólica deliberada e aprovada; **não** repetir a V1/V2 rejeitada, não gastar créditos em IA e não abrir fase de montagem das 12 cenas antes de validar o look.

1. Corrigir, na branch candidata da PR #57, a divergência entre shortlist antiga e fontes efetivas do código; manter registro das rejeições e hashes dos candidatos anteriores.
2. Curar uma nova abertura 0–5,74s que transmita pergunta/espera; conferir movimento, cor, janela/noite/chuva, personagem não identificável e caderno quando o plano assim requerer.
3. Antes de promover: links originais, direito comercial, download seguro, SHA-256, FFprobe, decodificação integral, fotogramas de início/meio/fim, corte 9:16, área de legenda e **revisão estética expressa**.
4. Somente após aprovação artística: escolher se as demais cenas seguem o mundo ROOM_A ou a proposta simbólica; preparar então 12 clipes reais, direitos, áudio e render final.
5. Qualquer aprovação técnica de S01 permanece **PREVIEW_ONLY** até prova da master 1080×1920, dos direitos e da autorização de publicação.

## 8. Segurança, escopo de alteração e rollback

- O checkpoint em PR #58 modifica **apenas o arquivo ESTADO_ATUAL.md em branch isolada**. Correção adicional autorizada, reversível e **somente documental/teste**, foi aplicada à PR #57; workflows, contracts, engine, áudio, artes, outros projetos e branch operacional permanecem inalterados.
- Não efetuar merges automáticos, geração de IA, publicação, alteração de permissões de Drive ou reativação de automação.
- Rollback: fechar a PR documental sem merge, preservando íntegros HEAD operacional e PR #57.
- **Lacunas indisponíveis:** transcrição integral do CHAT 03; verificação acústica e dos bytes completos do WAV/trilha privados na sessão; revisão de cada segundo das 12 futuras filmagens; aprovação humana da direção visual alternativa.

### 8.1 Registro de intervenção posterior ao snapshot da PR #57

- **PR #57 atualizada sem merge:** shortlist S01 substituiu fonte obsoleta por Pexels IDs 8860242 e 4458845 usados pelo código; o texto distingue material experimental das versões rejeitadas.
- Adicionado teste **test_shortlist_s01_provenance_matches_runtime** para proteger contra divergência entre tabela e código.
- Commits PR #57: 43cce9ab85da1faa0acec3199d5aecba6fb2af13 (documentação) e 1db7a29f027d551d81bfd6a5e83fed8c1b66f06d (teste).
- **Engine Gates SUCCESS** no HEAD da PR #57 após correção: [run 44625149040](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44625149040). Auditoria de especialistas estava em execução no momento da consulta; não declarar PASS sem nova verificação.
- A montagem S01 V2 permanece **REJEITADA PARA MASTER**. Novo teste documental não comprova direitos de mídia, aprovação estética nem render final.

### 8.2 Proteção pós-curadoria S01 — PR #59 (19/11/2026)

- **Nova PR #59 DRAFT, empilhada sobre a PR #57**, branch `verbo-no-chao/e01-s01-stock-rejection-lock-20261119-v1`, head `3b465af0c55ad2c3822e7e6aa00e42668273641a`. Nenhum merge em branch operacional.
- Registro JSON dos SHAs S01 stock V1 `3653dd73575446533b1f47512b3c236b9184bba150fec5116c5526ba0ee1013e` e V2 `2c099db52b219cb901977d98fac29f91579a4be1d9a2126f4ff6ba0cbcc7c1e5`, com conjuntos de fontes respectivos. Ambas as prévias continuam **REJEITADAS** por coerência cinematográfica.
- `agents/e01_s01_stock_rejection_gate.py` mais integração ao piloto existente: detecta resultado anteriormente reprovado por hash ou reaproveitamento do mesmo conjunto de fontes, sinaliza `REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_REJECTED_EDITORIAL` e mantém liberação de master e publicação negadas.
- 10 métodos de teste adversarial offline no módulo `tests/test_e01_s01_stock_rejection_gate.py`, além da suíte geral. [Engine Gates run 44627983647](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44627983647) **SUCCESS** e [Eight Specialist Audits run 44627983601](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44627983601) **SUCCESS** no mesmo SHA.
- Nenhuma nova filmagem foi encontrada, baixada, gerada, montada ou aprovada nesta intervenção. O novo gate é proteção editorial, **não avalia conteúdo visual autonomamente**.
- **Próxima prioridade inalterada:** encontrar uma S01 com filmagem real e visual coerente (preferir sessão/ator único e noite chuvosa com caderno fechado), conferir licença e quadros, provar os bytes; se impossível, submeter direção simbólica alternativa a revisão estética. NUNCA reciclar V1/V2 como master.

### 8.3 Resolução de fonte S01 auditada, PR #59 atualizada (19/11/2026)

- PR #59 segue **DRAFT**, HEAD `3cc57e3a49ccc5c386b61ae371d824513466325b`, base PR #57 não mesclada.
- Fonte Pexels 4458845 usada para chuva da S01 V2 anuncia **1920×1080 horizontal**. Recorte 9:16 sem expansão alcança apenas aproximadamente **608×1080** de pixels físicos; por isso não pode fundamentar master vertical nativa 1080×1920.
- Gate introduz `source_native_1080x1920_dimensions_sufficient`, calculado a partir das dimensões FFprobe das fontes, para registrar explicitamente insuficiência e manter MASTER_BLOCKED. Um PASS dimensional isolado nunca prova direitos, composição, conteúdo ou autorização.
- Novo teste adversarial diferencia fonte 4096×2160 com crop nativo suficiente da fonte 1920×1080 inadequada; também rejeita largura booleana falsificada. [Engine Gates run 44628425836](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44628425836) **SUCCESS** no HEAD; a auditoria de especialistas estava em execução na última consulta.
- **Nenhum download novo, master, publicação, gasto ou aprovação estética**. Reavaliação visual da S01 com filmagem real nova permanece prioridade.

### 8.4 Pesquisa física de stock S01 — PR #60 DRAFT (19/11/2026)

- **PR #60** `verbo-no-chao/e01-s01-single-take-research-20261119-v1`, head `563731b6b2302bbb208786d5c7cc41f1406f6057`, base PR #59 (também DRAFT). **Sem merges ou alteração operacional.**
- **Pexels 4510748:** MP4 H.264 real, 2160×3840, 9,958s, 27.473.889 bytes, SHA `c9893c53a3c51d9e6244e772ad16553ff3319db8b7bd070a9744800f316a2fa0`. Decodificação integral passou. Três fotogramas (0,5 / 2,8 / 5,4s) exibiram janela extremamente clara e ausência de caderno fechado; movimento de quadros muito pequeno. **REJEITADO EDITORIALMENTE PARA S01**, apesar da prova técnica positiva.
- **Pexels 28174743:** download `oversized_source` (> limite 160 MB existente); sem bytes completos nem opinião estética. **BLOQUEADO TECNICAMENTE, NÃO REJEITADO POR CONTEÚDO**.
- **Pexels 7026683:** MP4 H.264 real, 2160×3840, 10,01s, 25.994.187 bytes, SHA `53bc1ff9d0a34528b12c7f0095e2ed61797943391ddf900ab740b1949c38a7dc`. Decodificação integral passou, três quadros (0,5 / 2,8 / 5,4s) mostram rosto visível, paredes claras, laptop e caderno aberto. **REJEITADO EDITORIALMENTE PARA S01**, não globalmente.
- Provas: [Actions V1 parcial 44630728010](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44630728010), [Actions V2 sucesso físico 44631386851](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44631386851). [Engine Gates 44632337377](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44632337377) e [Eight Specialist Audits 44632337403](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44632337403) **SUCCESS** no HEAD da PR #60.
- Folhas de contato JPEG e relatórios JSON físicos foram preservados **na Biblioteca privada do ChatGPT**, caminho `/VERBO_NO_CHAO/E01_STOCK_QA_20261119/`. Não alegar que arquivos originais MP4 ou ZIP foram preservados no Drive; tentativa de handoff GitHub→Drive falhou. Um subdiretório vazio no Drive foi criado como tentativa de backup, sem arquivos enviados; **não confundir com backup efetivo**.
- Fonte de verdade do parecer atualizado: `contracts/e01_s01_single_take_physical_editorial_decisions_20261119_v1.json` e `docs/E01_S01_REAL_STOCK_PHYSICAL_VISUAL_REVIEW_20261119.md` da PR #60. As fotos dos quadros são evidências de **três instantes**, não de auditoria visual segundo a segundo.
- **Próxima ação prioritária:** deixar de testar cenas visualmente genéricas e buscar take verdadeiramente coerente (sombra, noite/chuva, pessoa não identificável e caderno fechado), sempre inspecionar frames antes de montar, ou obter aprovação explícita de direção simbólica alternativa. Sem gastos, geração de IA, master ou publicação.

### 8.5 Nova direção cinematográfica simbólica real — PR #61 (19/11/2026)

- **PR #61 DRAFT** (branch `verbo-no-chao/e01-s01-night-rain-motif-probe-20261119-v1`, head `cc261f3a1950f44113b60097c623c181841e8ba8`), empilhada sobre PR #60. Nenhum merge em PR #60, PR #59, PR #57 ou branch operacional.
- **Abertura S01 candidata como metáfora**, não substituição aprovada: vídeo stock Pexels #31069867, chuva noturna por vidro de metrô, luzes desfocadas, sem fingir mesma pessoa/ambiente `ROOM_A`. Divergências: ausência de ator e caderno fechado, cenário externo urbano. **Aprovação estética do conceito pelo usuário pendente.**
- Fonte física temporariamente baixada na CI: **93.575.530 bytes**, **2160×3840**, **24,000 s**, H.264, SHA-256 `fc36bb6b4039e307828d9ad0acabdb54a1baa4cb6e9d41f2889d2278be7c6df8`; FFmpeg full decode **PASS**. [Actions run 44638759167](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44638759167) **SUCCESS**.
- Artefato gerado em vídeo temporal real (não foto com zoom): **5,766667 s, 173 frames, 30 fps, 720×1280**, sem áudio/legendas e com marca `PREVIA DE QA - NAO PUBLICAR`. SHA-256 `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`. Decodificação de todos os quadros e rehash **confirmados novamente em ambiente local independente**.
- Três fotogramas físicos de **0,5 / 2,8 / 5,4 s** (médias de diferença 14,09 e 12,57) exibem movimento e noite/chuvoso. Não constituem auditoria quadro a quadro nem provam origem de captura por câmera ou direitos de terceiros.
- **Três arquivos preservados com sucesso na Biblioteca privada do ChatGPT:** `/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S01_31069867_PREVIA_SIMBOLICA_NAO_APROVADA.mp4`, `S01_31069867_FOTOGRAMAS_QA.jpg` e `S01_31069867_RELATORIO_FISICO.json`. Original MP4 não publicado/arquivado. Download da prévia e contato acessíveis também nos anexos desta conversa.
- Verdade por camadas: `contracts/e01_s01_night_rain_physical_visual_review_20261119_v1.json`, `docs/E01_S01_NIGHT_RAIN_REAL_VIDEO_EXPERIMENT_20261119.md` e teste `tests/test_e01_s01_night_rain_physical_evidence_lock_v1.py` na PR #61. Engine Gates **SUCCESS** no HEAD `cc261f3a` ([run 44639382675](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44639382675)). Eight Specialist Audits estava em execução na última leitura, verificar novamente antes de qualquer merge.
- **MASTER_1080x1920 BLOQUEADA; direitos visuais de terceiros, áudio, trilha, legenda e publicação NÃO aprovados.** O storyboard V2 original (12 cenas, 70,425s e 28 legendas) permanece intacto.
- **Próxima prioridade:** avaliação humana do **vídeo completo de 5,767s** para aprovar ou rejeitar explicitamente a DIREÇÃO SIMBÓLICA, não a publicação; somente se aprovada, desenhar visual das demais cenas e validar fontes individualmente. Não expandir às cegas nem produzir outro preview apenas para testar plataforma.

### 8.6 Aprovação da S01 e QA físico S02 — PRs #61/#62 (19/11/2026)

- **Decisão humana recebida:** usuário respondeu **“Aprovado”** à apresentação do vídeo S01 simbólico de chuva noturna Pexels #31069867. A **direção visual da S01** está agora formalmente **APROVADA**, delimitada pelo SHA da prévia `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`. **Não** aprova direitos de terceiros, master, publicação, gastos, merge, S02 ou demais cenas. Fonte: `contracts/e01_s01_owner_visual_approval_20261119_v1.json` na **PR #61 DRAFT**, HEAD `c2bb2e982700fb35fe251b48e39e69d23553953c`; [Engine Gates 44643892934](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44643892934) e [Eight Specialist Audits 44643892840](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44643892840) **SUCCESS**.
- **Novo experimento S02** (`A dor da espera`, 5,74–10,62s), PR #62 DRAFT, branch `verbo-no-chao/e01-s02-waiting-clock-qa-20261119-v1`, HEAD `90fac98cae9e5c68abfc0cc70ba937f514886919`, base PR #61. Metáfora proposta: chuva S01 → ponteiros de relógio analógico em movimento, fundo escuro, sem alegar mesmo personagem/ambiente.
- Stock Pexels **#7034348**, original físico 1080×1920, H.264, 20,2s, **6.202.873 bytes**, SHA `6a8f877c0e57a1397f4eb96ffc9a86d25e173019fb298ec0a6945b73973f2a40`. Fonte completa decodificada FFmpeg **PASS**. [Actions 44644297546](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44644297546) **SUCCESS**.
- Prévia S02 **720×1280, 30 fps, 147 frames, 4,900s**, sem áudio/legendas, com marca de revisão; SHA `31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786`, 203.410 bytes. SHA, FFprobe (147 frames) e FFmpeg full-decode **novamente verificados localmente**. Três frames de 0,5/2,4/4,5s mostraram relógio preto em fundo escuro **com mostrador branco muito luminoso**; S02 **CANDIDATA, NÃO APROVADA** para linguagem da S01, parecer de licenças também pendente.
- **QA de transição S01+S02 gerado fisicamente no contêiner**: 172 frames de S01 + 147 frames de S02 = **319 frames**, 30 fps, **10,633333s**, 720×1280, H.264, sem áudio, com marca; SHA `31ea65a045bbe067a66837b85c03ccc9fdf20bf93ac6b15603c6f4c7bf66156b`, 1.840.317 bytes, rehash/FFprobe/full decode **PASS**. O trim de S01 de 173 para 172 frames segue fronteira nominal 5,74s (frame 172 ≈5,733s) para não introduzir desvio no corte 10,62s. É prévia, não master. A comparação nos frames 5,65 e 5,95 confirma contraste visual abrupto chuva azulada → mostrador branco.
- **Evidências preservadas na Biblioteca privada do ChatGPT:** `/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_WAITING_CLOCK_REVIEW/` contém o MP4 de S02, contato JPEG, relatório físico, MP4 de transição, comparação e relatório conjunto (seis arquivos). Não arquivados MP4s brutos no GitHub.
- **Verdade da PR #62:** `contracts/e01_s02_waiting_clock_physical_visual_review_20261119_v1.json`, `contracts/e01_s01_s02_transition_qa_20261119_v1.json`, `docs/E01_S02_WAITING_CLOCK_PHYSICAL_QA_20261119.md`. [Engine Gates no HEAD 90fac98c, run 44645166140](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44645166140) **SUCCESS**. A execução Eight Specialist Audits final estava em fila na última consulta; verificar depois antes de qualquer merge.
- **Próxima prioridade:** conferir visualmente a transição S01→S02 e decidir se a S02 merece aprovação estética; se não, procurar outro take com luz menos intensa. Não há autorização para produção/master/publicação e nenhuma mudança ao storyboard canônico foi aplicada.

### 8.7 S02 com continuidade luminosa — prévia real graduada e PR #63 (19/11/2026)

- **S01 aprovada** pelo usuário permanece intacta; vídeo de chuva noturna identificado por SHA `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`. **S02 ainda sem aprovação artística**.
- A S02 candidata do Pexels #7034348 (#62) apresentava mostrador excessivamente claro para a S01 aprovada. Pesquisa de alternativa Pexels #30084927 mostrou original 1920×1080 **horizontal** insuficiente em altura nativa para master 1080×1920 vertical, então foi priorizada **pós-produção gratuita do stock vertical existente** em vez de sacrificar resolução nativa.
- Em ensaio **offline com os dois MP4s físicos** (S01 SHA acima; S02 SHA `31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786`) foram testados dois graus de iluminação/cor, escolhendo **GRADE A**: `eq=contrast=0.88:brightness=-0.035:saturation=0.65:gamma=0.64,colorbalance=bs=0.10:gs=0.04:rs=-0.01,vignette=PI/7`. Aplica-se apenas à S02; S01 no combinado é **recodificada sem grade**, portanto não confundir referência aprovada com identidade pixel a pixel no render combinado.
- Amostras de luminância média na escala 0–255, 2,3s: S01 **29,60**, S02 original **70,16**, S02 GRADE A **34,28**; no composto em 5,95s: antes **61,79**, depois **30,69**. Medidas descrevem amostra de quadros, **não** certificam estética, continuidade de toda a sequência ou qualidade 1080×1920.
- **S02 graduada A:** 720×1280, 30 fps, 147 frames, 4,9s, SHA `0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3`, 277.678 bytes; FFprobe, SHA e decodificação integral **PASS** no contêiner.
- **Corte S01 + S02 A:** S01 172 frames + S02 147 frames = 319 frames, 30 fps, 10,633333s, 720×1280, H.264 sem áudio, SHA `598675e1e00b2a27880080bdd0052f6bc8ab8ae408d80be2272aeabd1eeae4ae`, 2.906.687 bytes, FFprobe/hash/full decode **PASS**. Comparativo JPEG SHA `0f2f24d81927fb5fbe16b1c216d3b89c5218967b0c9c7012ebabf95aeb8fe146`.
- **PR #63 DRAFT** (`verbo-no-chao/e01-s02-color-continuity-qa-20261119-v1`, HEAD `3da7e0300fb17f867d4c30fe9b2dadff88483cf2`, sobre PR #62) registra o contrato `contracts/e01_s02_color_continuity_qa_20261119_v1.json`, script offline hash-locked `agents/e01_s02_color_continuity_qa_v1.py`, testes adversariais, documento `docs/E01_S02_COLOR_CONTINUITY_GRADE_A_20261119.md`. Code CI [Engine Gates 44657111525](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44657111525) **SUCCESS**; Eight Specialist Audits no HEAD estava em execução na última leitura (verificar antes de qualquer merge). A composição física local foi testada; **não** afirmar que CI reexecutou a renderização real usando arquivos privados.
- Quatro evidências persistiram **na Biblioteca privada ChatGPT**, pasta `/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_WAITING_CLOCK_REVIEW/S02_COLOR_MATCH_V1/`: S02 corrigida MP4, composição S01+S02 MP4, comparativo JPG e QA JSON. Nenhum original stock foi enviado ao GitHub.
- **Riscos restantes:** `QUARTZ` e numerais visíveis, possível concorrência com legendas na área inferior, e origem dos direitos individuais não homologada; direção artística S02 **não aprovada**, áudio/ASS/master 1080×1920/publicação **bloqueados**, sem merge ou gasto.
- **Próxima prioridade:** avaliar o vídeo **completo** de transição S01→S02 graduada A para decidir estética; não iniciar S03 ou master automaticamente enquanto S02 estiver pendente.

### 8.8 S02 — rejeição 4K e caption QA real com 28 legendas (19/11/2026)

**Decisão editorial preservada:** S01 chuva noturna (#31069867) continua **aprovada na direção visual** pelo usuário. Não houve aprovação de S02, das outras cenas, direitos, master, merge ou publicação.

- **PR #64 DRAFT**, `verbo-no-chao/e01-s02-dark-clock-alt-qa-20261119-v1`, HEAD `5604ec134e85b5120b81d53adb4f18ff5ca976af`, base PR #63. Fonte alternativa Pexels **#29862379**: MP4 físico **3840×2160, 11,74s, 57.975.096 bytes, H.264**, original SHA `a6058b295f21cbfa5381d6a19263a1ed5606dcfb87a6579ae0aa4611e5130052`, full decode PASS. Recorte nativo central **1214×2160** tem resolução suficiente para 1080×1920 sem upscale, mas os quadros revelaram **quase escuridão em 0,5s → carcaça vermelha/fundo verde e relógio muito iluminado aos 4,5s**. **REJEITADA ESPECIFICAMENTE PARA S02** por contraste e paleta instáveis, não por incapacidade técnica. MP4 QA 720×1280, 147 frames, 4,9s SHA `3bb1c6efced29fbd5d48b235aec69af20d7e5c7bebf0b03fc8d09488d020ae94`. [Run 44660021135](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44660021135) SUCCESS. Rejeição `contracts/e01_s02_dark_clock_29862379_editorial_decision_20261119_v1.json`. [Engine Gates 44660921253](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44660921253) e [Eight Specialist Audits 44660921229](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44660921229) **SUCCESS** no HEAD final.
- A S02 GRADE A anterior (#7034348) **continua candidata não aprovada**. Uma inspeção de **nove quadros** confirmou o texto `QUARTZ` legível no relógio e mostrador claro sob a zona inferior onde as legendas aparecem. JPEG QA SHA `a589e5c417840ba9db31e665adf1a7c23ab6142b5dfde9db7108234563cf2b8c`. Texto QUARTZ não é presumido automaticamente problema de marca; é um problema potencial de elegância/legibilidade. Guardado na Biblioteca privada.
- **PR #65 DRAFT**, branch `verbo-no-chao/e01-s02-real-caption-safezone-qa-20261119-v1`, HEAD `568dbfe0e57ef4445fd7c8cc665fe57843212cd9`, base PR #63 (independente da rejeição #64). **Recuperado fisicamente** o pacote original do E01 com 28 cues de karaoke e timing do ASR, [Actions 44208934506](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44208934506), artifact #14385236602: ASS SHA `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`, SRT SHA `503eb0119c386096fbdb7e6c671828682b3390328d15cfded95b2d0ae383556d`, ZIP SHA `2ea85dba50b4b91d71e4ff53a99b80cf0170ba042080322d435379686d0f8e64`. ZIP e arquivos rehash verificados; pacote e ASS/SRT/timeline guardados em `/VERBO_NO_CHAO/E01_CAPTIONS_CANONICAL_V2/` para evitar expiração de artifact.
- **Nova prévia física S01+S02 GRADE A com ASS real intacto**: 720×1280, **319 frames, 30fps, 10,633333s**, sem WAV/áudio, com avisos de QA, SHA `8ce132728c27db5dd1ce2cc6717d51ee3cd8d47cbb989081adc5c36ef2b27f3f`, full decode/ffprobe/hash PASS. Foram testados gradientes discretos de escurecimento **somente na parte inferior da S02**, 35% e 55%, usando as **mesmas 28 legendas**. Preferência criativa **provisória 55%** com menor brilho medido na faixa das legendas, não aprovação humana. Prévia 55% SHA `f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c`, 2.066.424 bytes, 319 frames, 30fps, full decode PASS; comparativo A/B/C JPG SHA `89fe5ad902652167178dae58260841d0c5782747be54ea75c9072b3c095de87e`. Aviso QA duplicado na tela é intencional (fonte + ASS), **não o produto final**. Salvo em `/VERBO_NO_CHAO/E01_STOCK_QA_20261119/S02_CAPTION_READABILITY_20261119/`.
- **PR #65 implementa reproducibilidade offline** em `agents/e01_s02_real_caption_safezone_qa_v1.py`, contrato de SHA `contracts/e01_s02_real_caption_safezone_qa_20261119_v1.json`, testes e documentação `docs/E01_S02_REAL_KARAOKE_READABILITY_QA_20261119.md`. O pipeline de QA valida os hashes, 28 cues, quadros, formato e publicação desautorizada; os **MP4s privados não foram executados dentro da CI**. A prévia física foi processada no contêiner. Uma falha inicial de regressão por teste que tentava desembrulhar retorno `int` foi diagnosticada pelos logs e **corrigida** antes da entrega. No HEAD final, [Engine Gates 44662437040](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44662437040) e [Eight Specialist Audits 44662437030](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44662437030) **SUCCESS**.
- **Limites permanecem:** S01 aprovada somente visualmente; S02 e demais cenas ainda não aprovadas; a nova prévia de legendas é **720p de QA**, não fonte 1080×1920; direitos de fontes/terceiros, master e sincronização final com WAV não liberados. **Sem merge, gasto, publicação ou alteração do storyboard/cues.** Fontes Pexels permitem uso/modificação em geral, mas revisão individual de direitos não foi concluída.
- **Próxima prioridade:** inspecionar o vídeo com karaoke real e gradiente 55% em tela móvel para decidir estética S02; se rejeitada, localizar alternativa que mantenha legibilidade sem fundo/mostrador claro. Não avançar para master ou S03 por aprovação automática implícita.

### 8.9 E01 S01 + S02 — áudio físico real recuperado, vídeo com karaoke e voz (20/11/2026)

- **AVANÇO FÍSICO:** após a PR #65 anterior produzir uma transição 720p de 10,633s com 28 legendas reais porém sem áudio, foi recuperado pelo GitHub o **WAV v2 exato da narração**, run [44204100486](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44204100486), artifact **14383520578**. Fonte **70,425s / PCM16 mono / 24 kHz / 3.380.444 bytes / SHA `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`** — arquivo/reporte do ZIP verificadamente íntegros. Não foi sintetizada uma nova voz, alterado o texto nem usada API paga.
- **MP4 novo com imagem real + karaoke + áudio da fonte:** `S01_S02_REAL_KARAOKE_AND_ORIGINAL_VOICE_10S_QA_NOT_MASTER.mp4`, **720×1280**, H.264 com cópia de vídeo, **319 quadros a 30 fps / 10,633333 segundos**, **AAC 48k mono da voz original**, 2.264.744 bytes, SHA `979fcb7d630177efc99e76baa98adc0d34cf0d3a89beaf06484060c7bdd6e5f6`. Fonte de vídeo de QA `f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c`, ASS original `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`. FFprobe, hashes e **decodificação integral dos dois streams PASS**; correlação técnica do áudio AAC reamostrado contra WAV nos primeiros 0,8–5,8s, lag **0 ms**, não substitui escuta humana. Assinatura do relatório JSON local `a9b7c834af06628050e20c4d6005540f67fc8b9f3a0378a18524e777386ee2f3`.
- **Medição objetiva da voz no trecho:** **−22,5 LUFS integrado**, LRA 2,1 LU, true peak **−2,3 dBTP**, sem clipping detectado, sem ganho/normalização, sem trilha/ducking/mix final. Não afirmar áudio final profissional liberado por esse teste. O áudio da prévia é recorte do WAV original, AAC com perdas para MP4.
- **Provas preservadas na Biblioteca privada:** `/VERBO_NO_CHAO/E01_AUDIO_CANONICAL_V2/e01-v2-preview-only-SHA_VERIFIED.wav` e `/VERBO_NO_CHAO/E01_S01_S02_QA_REAL_VOICE_20261120/` (MP4, QA JSON e ZIP de revisão). Evita expiração do artifact de GitHub. Nenhum WAV/MP4 privado subiu ao repositório público.
- **PR #65 DRAFT, sem merge, ampliada** em `verbo-no-chao/e01-s02-real-caption-safezone-qa-20261119-v1` com `contracts/e01_s01_s02_real_voice_sync_qa_20261120_v1.json`, `agents/e01_s01_s02_real_voice_sync_qa_v1.py`, `tests/test_e01_s01_s02_real_voice_sync_qa_v1.py`, `docs/E01_S01_S02_REAL_VOICE_SYNC_PHYSICAL_QA_20261120.md`. CI executa testes adversariais sem MP4/WAV privados; criação e análise física dos MP4 ocorreram no contêiner local e **não devem ser atribuídas ao CI**.
- **PR #66 DRAFT e isolada**, trata quatro workflows legados de geração remota (vídeo/voz) e permanece sem merge. Gates da PR #66 foram confirmados antes deste ciclo: **493 testes, 15 ignorados, sem falhas; oito verificadores CI SUCCESS** no HEAD `a97abac67b459b8c5c46da4c0288a2d5f9fa6ce2`. O default operacional permanece `db6e1d4a` e **os bloqueios da PR #66 não estão ativos no default**.
- **Estado editorial:** S01 **aprovada APENAS visualmente**; S02 **ainda candidata, não aprovada** apesar da melhora de legenda e áudio. Nenhum progresso em S03–S12, direitos individuais, música, mix final ou master 1080×1920 foi declarado. Sem gasto, merge, alteração em outros motores ou publicação.
- **Próxima única ação:** avaliar audição/estética da prévia S01+S02 com voz real em celular, decidir se o mostrador do relógio funciona; somente depois fechar S02 e avançar continuidade narrativa. Nenhuma aprovação S02 inferida de “continuar”.

### 8.10 S02 — tomada física de mesa humana REJEITADA após prova real (20/11/2026)

- **Motivo da pesquisa:** o storyboard E01 v2 para S02 (`A dor da espera`, 5,74–10,62s) exige **mão do mesmo protagonista anônimo em casaco escuro repousando sobre mesa de madeira, relógio discreto e iluminação contida**, com área livre de legendas. A S02 anterior Pexels #7034348 contém relógio grande e a inscrição `QUARTZ` competindo com as legendas, ainda sem aprovação. A S01 de chuva noturna continua aprovada **somente visualmente**, não como passe para qualquer S02.
- **PR #67 DRAFT, sem merge:** [VNC E01 S02 — tomada real de mãos 4K e rejeição editorial](https://github.com/BORELLITO/verbo-no-chao-engine/pull/67), HEAD `02e32e8594cff284942634d9f91026ef98c641df`, branch `verbo-no-chao/e01-s02-human-desk-stock-qa-20261120-v1`, base PR #65, sem alterar a branch operacional. Fonte [Pexels #9903488, Ron Lach](https://www.pexels.com/video/a-man-organizing-the-things-on-his-table-9903488/): **video original realmente baixado 2160×4096, 32,36s, 60.515.189 bytes**, H.264, SHA `ab34b60af5d700e94fc70fc19982ff974a3c52c3a6484ce4a48ce07c965d1d86`. Recorte vertical nativo **2160×3840** (sem upscale); **não** alegar decodificação integral do original de 32s.
- **[GitHub run 44711536426](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44711536426): SUCCESS** no workflow de pesquisa de uma só execução, sem gasto nem modelo de geração. Prévia real **720×1280, 30 fps, 147 quadros / 4,9s, 476.674 bytes**, sem áudio, com aviso QA, SHA `af604d62cc899206e341dd569897a5f5dc82d724f9cd1170cff9948e903a5107`. FFprobe, rehash físico e full decode dessa prévia **PASS**. Três frames aos **0,5/2,4/4,5s** JPEG SHA `0802ca9e6a566c9c0c5cb0d0b8df9a3e9c2cb06c3690b5cf06adf043d64186e3`, mudança visual comprovada; não demonstra origem humana da câmera, licença individual ou personagem igual à S01.
- **VEREDITO DE DIREÇÃO EDITORIAL:** `REJECTED_FOR_S02_SCENE_FIDELITY` (apenas esta fonte nesta cena, **não rejeição do usuário**). A filmagem é de **mesa clara e carregada de objetos, pessoa executando tarefas de trabalho, roupa mostarda/marrom, relógio distante na borda**; difere da espera contemplativa noturna e do figurino carvão. Como a falha é de narrativa, mais color grading não a corrige. Registro em `contracts/e01_s02_9903488_editorial_rejection_20261120_v1.json`, script/contrato/testes de QA em PR #67.
- **QA da PR #67 no commit final `02e32e85`:** [Engine Gates 44712472075](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44712472075) **SUCCESS, 568 testes, 15 skipped, 0 falhas**; [Eight Specialist Audits 44712472034](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44712472034) **SUCCESS** (verificadores determinísticos, não aprovação cinematográfica). O workflow de prova física está protegido por commit único e não possui `workflow_dispatch` ou cron.
- **Backup privado:** `/VERBO_NO_CHAO/E01_STOCK_QA_20261120/S02_HAND_DESK_9903488_REJECTED/` contém MP4 QA e três frames em JPEG, JSON de prova. Nenhuma cópia do original stock Pexels foi adicionada ao repositório público.
- **Estado preservado:** S01 visual aprovada; **S02 não aprovada**, antiga #7034348 com voz+legendas continua candidata não descartada, mas falha semântica do relógio dominante identificada. Direitos individuais, master 1080p, S03–S12 e publicação seguem BLOQUEADOS. **PR #66 de segurança permanece DRAFT sem merge**.
- **Próxima ação única:** curadoria de fonte real **noturna com mão em repouso e referência temporal discreta**, sem supor que a listagem de stock garante composição. Só gerar novo preview se a fonte passar em quadro/figurino/luz; nada de repetir #9903488 para a S02. Não promover fontes sem autorização, direitos ou aprovação artística.

## 9. Links de verificação

- [PR #41 — branch operacional](https://github.com/BORELLITO/verbo-no-chao-engine/pull/41)
- [PR #49 — integração merged em VNC](https://github.com/BORELLITO/verbo-no-chao-engine/pull/49)
- [PR #57 — shortlist e montagens stock](https://github.com/BORELLITO/verbo-no-chao-engine/pull/57)
- [CI recente do HEAD PR #57](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44616216856)
- [Prova física de render real S01 V2](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44615672379)

**Regra de continuidade:** uma nova conversa deve abrir ESTE estado, conferir HEAD/PRs/run IDs no GitHub atual, recuperar o contrato editorial e **só então** editar a próxima cena ou a branch candidata. Nunca converter sucesso técnico em aprovação estética/direitos/publicação.
