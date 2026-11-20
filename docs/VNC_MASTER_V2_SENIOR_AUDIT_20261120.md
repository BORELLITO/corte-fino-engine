# VERBO NO CHÃO — Auditoria MASTER V2 / ciclo de contenção P0–P2
**Data local de corte:** 20/11/2026 (America/Sao_Paulo)  
**Escopo e identidade:** `VERBO_NO_CHAO_EXCLUSIVO` · repositório **público** `BORELLITO/verbo-no-chao-engine` · trabalho somente em branch de auditoria independente.  
**Protocolo de referência:** upload do proprietário `05_PROMPT_MASTER_VERBO_NO_CHAO_V2.txt` (SHA-256 medido `28cba0f640cad30d30e194304bd0963b8761158b4200a7d29efe8cf7e032632e`). Esse SHA é igual ao checkpoint antigo `docs/checkpoints/VNC_E01_CONSOLIDATED_20261119.json`; **não** implica que o conteúdo integral do upload deva ser republicado no GitHub.  
**Fonte atual verificada:** branch padrão `verbo-no-chao/e01-stock-curation-gate-v1`, HEAD `db6e1d4acf23e82793f6230535a1716842ba5cd0`; `main` histórica `b59bbbec9aef843bb7118f1328fab37e01b098b3`. GitHub repo id `1400839762`. A branch operacional é distinta das PRs ainda abertas e **não** contém suas decisões posteriores como código merged.

## Resumo verificável e limites

O E01 **“Quando você pergunta e nada muda”**, sobre **Habacuque 1:2–4**, tem roteiro/paráfrase portuguesa original, locução documentada **70,425s**, **12 cenas** e **28 cues** com ASS físico. O rough cut histórico foi um animatic, não master de filmagens licenciadas. **S01 recebeu aprovação humana apenas da linguagem simbólica de chuva noturna** via prévia Pexels #31069867, SHA `724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961`, registrada na PR #61 DRAFT, não integrada. A **S02** com stock #7034348 e GRADE A, QA real com karaoke de 319 frames e gradiente 55% está em **PR #65 DRAFT, sem aprovação artística**; alternativa #29862379 foi rejeitada em PR #64. Essas evidências físicas **não resolvem** licenças específicas, locução+trilha no master, 10 outras cenas, nem publicação.

**Base textual bíblica consultada:** BibleProject, https://bibleproject.com/guides/book-of-habakkuk/ — o lamento 1:2–4 é sobre **injustiça, violência, Torah negligenciada e líderes corruptos**, não uma promessa individual de resposta rápida. A paráfrase do E01 preserva a dimensão de injustiça coletiva. **Não** é prova de revisão teológica e tradução por profissional independente.

**Fonte primária de licença audiovisual:** https://www.pexels.com/pt-br/licenca/ — uso/edição gratuitos em geral e crédito opcional; vedação a implicar endosso por pessoas/marcas e limites de representação. O uso comercial geral não equivale a certificado de clearance específico de pessoas, propriedade, marca, material musical ou áudio de cada arquivo. A pergunta sobre direitos de terceiro permanece aberta.

## Auditoria das 10 camadas / triagem sênior

| Camada | Verificado neste ciclo | Veredito e ação |
|---|---|---|
| C1 — escopo | Repositório renomeado, default VNC e `main` legado, não são motores intercambiáveis | PASS de identidade; não editamos main/legado, mas a infraestrutura compartilhada exige vigilância |
| C2 — aprovações | PRs #57–65 em DRAFT; S01 aprovada no chat e versionada na #61; S02 não | **BLOCKED** para promover a produção automaticamente; fontes de verdade distintas por camada |
| C3 — inventário | Árvore do HEAD operacional: 301 entradas, 27 workflows VNC, módulos de áudio/FFmpeg/Bíblia, 12 cenas, checkpoints | PASS de inventário parcial. Não houve auditoria byte a byte de todas as 301 entradas |
| C4 — arquitetura | `orchestrator/runflow.py` fail-closed, `agents/team.py` com oito verificadores; branch canônica antiga em `docs/ENGINE_LOCK.md` | **P1 corrigido na branch candidata**: texto de lock + verificador atualizados |
| C5 — estados/replays | Workflow LTX23 e Wan2.2 free possuíam `workflow_dispatch` e rodavam cliente GPU remoto; gerador de run_id contém UUID | **P1 corrigido na branch candidata**: duas rotas substituídas por CI offline; idempotência geral do runflow permanece por revisar |
| C6 — teologia/roteiro/cinema | Contexto Habacuque 1:2–4 compatível com pesquisa de fonte; S01 real aprovada; S02 ainda disputa safe-zone; cenas 3–12 sem prova integral | **BLOCKED** para master, sem fabricar continuidade de atores nem chamar JPG animado de filmagem |
| C7 — segurança/direitos/custos | Actions com `contents: read` observada nos workflows auditados; repo público; Pexels permite uso geral mas não libera terceiros; branch protection não confirmada | **P0 release contido**, não autorizado. Acesso a regras avançadas/branch protection não foi confirmado pelo conector — UNKNOWN |
| C8 — QA | Testes unitários/contratos no GitHub, runs históricos S01/S02, FFmpeg e SHA provados nos ciclos anteriores; QA visual de alguns quadros | PASS apenas nas camadas executadas. Testes e frames amostrados não significam master assistida integralmente |
| C9 — telemetria | GitHub run IDs, commit SHAs, relatórios e SHA; Biblioteca privada com prévias e legendas preservadas | PASS parcial de proveniência, links de artifact do GitHub podem expirar |
| C10 — operação/recuperação | DRAFTs não mescladas, sem automação de postagem; fonte do `docs/SPECIALIST_TEAM.md` tratava `main` como default apesar do atual VNC | **P1 corrigido na branch candidata**; checkpoint deste ciclo versionado em paralelo, sem proclamar merge |

### Findings — especificação auditável exigida pelo PROMPT MASTER

| ID / gravidade | Evidência | Causa-raiz comprovada (ou hipótese) | Risco | Correção mínima | Regressão | Estado |
|---|---|---|---|---|---|---|
| VNC-P0-01 / P0 | S01 visual sim, S02 não; rights/voice/music e master não liberados | Conteúdo ainda em fase de curadoria, sem provas individuais completas | Publicação indevida ou copyright | Conservar gates `master_allowed=false` e `publication_authorized=false`; nunca merge/publish implícito | Testes existentes de rights/manifest + QA real requeridos antes de release | **BLOQUEADO COM CONTENÇÃO** |
| VNC-P1-02 / P1 | `verbo-no-chao-e01-ltx23-motion.yml` possuía `workflow_dispatch` sem nonce e passo `gradio_client` gerativo | Trabalho histórico de prova gratuita permaneceu reexecutável | Novos gastos indiretos de compute/cota, falhas e idempotência | Substituído por teste estático offline, sem dispatch/predict/install | `tests/test_vnc_provider_replay_containment_v2.py` | **IMPLEMENTADO EM PR; NÃO EM PRODUÇÃO** |
| VNC-P1-03 / P1 | `verbo-no-chao-e01-free-motion-probe.yml` aceitava dispatch e chamava Wan2.2 remoto | Mesma classe de fluxo experimental reexecutável | Replays não autorizados e falsa progressão de clipes | Idem: CI offline e código anterior preservado | Mesmo teste | **IMPLEMENTADO EM PR; NÃO EM PRODUÇÃO** |
| VNC-P1-04 / P1 | `docs/ENGINE_LOCK.md` e `agents/team.py` procuravam `bootstrap` apesar do default VNC atual | Atualização do default não propagada aos verificadores antigos | Auditor de governança verde com fonte canônica obsoleta | Atualizar lock, documentação de especialistas e validação de branch | `tests/test_vnc_operational_branch_governance_v2.py` | **IMPLEMENTADO EM PR; NÃO EM PRODUÇÃO** |
| VNC-P1-05 / P1 | PRs #57–#65 empilhadas sobre branches candidatas; branch operacional em `db6e1d4a` | Aprovações artísticas e pesquisas isoladas sem revisão de integração | Código aprovado/instalado confundido com execução operacional | Checkpoint único distinguindo DRAFT, merge, aprovação; não juntar em massa | Verificação de HEAD/PR e status remotos | **DOCUMENTADO; INTEGRAÇÃO PENDENTE** |
| VNC-P1-06 / P1 | Branch protection endpoint não validado e rulesets listados vazios na API acessível | Indeterminado — conector não permitiu leitura de `.../protection` | Checks podem ser ignorados no merge mesmo estando verdes | Avaliar proteção e checks obrigatórios em operação separada, com autorização específica | Inspeção remota da configuração de proteção | **UNKNOWN / NÃO ALTERADO** |
| VNC-P1-07 / P1 | S02 QA em 720p, 28 cues aplicados sem WAV, relógio com QUARTZ visível e mostra parte sob legendas | Fonte stock central ocupa safe-zone; áudio ausente da prévia | Produto audiovisual ilegível/sincronia não certificada | Manter como prévia; revisar no celular e só então reaquisição nativa para master | QA físico com WAV, ASS e legenda frame a frame | **BLOQUEADO** |
| VNC-P2-08 / P2 | `agents/team.py` possui oito papéis de crescimento/roteiro/monetização | Equipe criada para auditoria determinística, não subagentes IA independentes ou supervisão de fotografia | Pass verde pode ser interpretado incorretamente como liberação bíblica/cinema/direitos | Atualizado documento explicitando o alcance; manter os gates especializados separadamente | Testes da equipe, documentação de limites | **DOCUMENTADO** |
| VNC-P2-09 / P2 | Muitos `checkout@v4`, `setup-python@v5`, bibliotecas `>=` em 27 workflows do baseline | Configuração histórica não totalmente pinada | Mudança upstream e falhas de supply chain | 2 workflows retidos agora usam Actions pinadas; restante depende de auditoria isolada | Scanner de ações e dependências | **PARCIAL** |
| VNC-P2-10 / P2 | `orchestrator/runflow.py` gera UUID por chamada | ID de execução único, mas não chave determinística de idempotência remota | Retentativas de package/render e dispersão do estado se houver provedor materializado | Propor chave por brief+asset SHAs, com ledger reconciliado, antes de qualquer chamada paga | Repetir brief com provider UNKNOWN: zero novas chamadas | **PLANEJADO, NÃO ALTERADO** |
| VNC-P2-11 / P2 | Artefatos ephemeral de Actions e Biblioteca privada; Pexels originais descartados depois da QA; derivado 720p não permite remaster nativo | Política de não persistir originais stock em GitHub e limites de tempo/storage | Reaquisição exigida na master, original externo pode sumir | Continuar SHA/proveniência e preservar cópia privada quando licença e storage permitirem | Teste de reaquisição+rehash | **RISCOS RESIDUAIS DOCUMENTADOS** |

## Cobertura real dos papéis

- **BIBLE_RESEARCHER / FACT_CHECK:** contexto histórico-literário consultado via BibleProject; não existe prova de parecer teológico independente final. **UNKNOWN** para liberação final.
- **SCRIPT_EDITOR:** roteiro E01 original, não modificado; consulta de originalidade e não-reciclagem ainda precisa comparar biblioteca/episódios. **PASS de preservação, não de master**.
- **SCENE_BIBLE / CONTINUIDADE:** S01 simbólica documentada, S02 gradiente em QA, 10 cenas restantes e loop S12 não demonstrados com mídia licenciada. **BLOCKED**.
- **CLIP_ACQUISITION / DIREITOS:** Pexels original reconhecido, hashes de stock físicos reportados, clearance individual não concluído. **BLOCKED para release**.
- **VOICE_DIRECTOR / AUDIO_AUDITOR:** WAV e parecer ASR documentados, nenhuma prova nova de mix/trilha true-peak neste ciclo. **UNKNOWN para áudio final**.
- **SUBTITLE_ENGINE:** ASS original 28 cues recuperado/rehash verificado nos ciclos anteriores e aplicado no teste S01/S02, mas vídeo 720p sem voz incorporada. **PASS para artefato QA, BLOCKED para master**.
- **MEDIA / FFmpeg / RELEASE:** rough cut ≠ MP4 final, workflow de publicação não validado no canal real, nenhum master. **BLOCKED**.
- **Oito especialistas GitHub:** determinísticos, workflows de estratégia, planejamento, ideação, retenção, capa, shorts, desempenho e monetização; os relatórios não substituem agentes IA autônomos e não provam mídia. **AUDITADO**.

## Política de isolamento e recuperação

Proibido alterar `main`, branches de Corte Fino, ferramentas CAPTAPRONTO, Because Of This ou Salmo 13 durante este ciclo. Base de trabalho é **EXATAMENTE** HEAD `db6e1d4a`; os arquivos alterados são dois workflows experimentais de vídeo GPU, `agents/team.py`, `docs/ENGINE_LOCK.md`, `docs/SPECIALIST_TEAM.md`, testes novos e documentos de auditoria. Nenhuma filmagem, voz, credencial ou artefato pessoal é copiada para GitHub.

**Rollback:** fechar PR DRAFT, deixar branch operacional inalterada. **Merge não autorizado neste ciclo.** Para ativação do bloqueio dos antigos workflows no default, será necessária integração cuidadosamente revisada (não inferir que DRAFT já está ativa). Os outros workflows de reprodução experimental e `workflow_dispatch` ainda precisam de revisão específica, não alegar blindagem integral.

**Próxima ação única:** após revisão do PR de contenção, integrar especificamente os bloqueios de replay e governança ao ramo operacional somente mediante autorização de merge; então preparar o gate de rights+legibilidade nativa da S02, sem multiplicar buscas/refações vagas.

**Fontes externas:**  
- Bíblia: https://bibleproject.com/guides/book-of-habakkuk/  
- Uso de Pexels: https://www.pexels.com/pt-br/licenca/  
- GitHub branch protection: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule

**Estado final do documento:** diagnóstico baseado nas árvores/arquivos e na API remota consultados, com retificações isoladas; o resultado da CI deve ser preenchido apenas após verificação do HEAD candidato. NÃO é autorização de publicação.
