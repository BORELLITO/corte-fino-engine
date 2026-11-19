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

## 9. Links de verificação

- [PR #41 — branch operacional](https://github.com/BORELLITO/verbo-no-chao-engine/pull/41)
- [PR #49 — integração merged em VNC](https://github.com/BORELLITO/verbo-no-chao-engine/pull/49)
- [PR #57 — shortlist e montagens stock](https://github.com/BORELLITO/verbo-no-chao-engine/pull/57)
- [CI recente do HEAD PR #57](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44616216856)
- [Prova física de render real S01 V2](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44615672379)

**Regra de continuidade:** uma nova conversa deve abrir ESTE estado, conferir HEAD/PRs/run IDs no GitHub atual, recuperar o contrato editorial e **só então** editar a próxima cena ou a branch candidata. Nunca converter sucesso técnico em aprovação estética/direitos/publicação.
