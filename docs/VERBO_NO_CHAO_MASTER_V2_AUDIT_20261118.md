# VERBO NO CHÃO — Master V2: auditoria executiva e decisão operacional
Data-base: 2026-11-18, America/Sao_Paulo. Status: **CANDIDATO EM BRANCH ISOLADA / NENHUM MERGE / MASTER BLOCKED / PUBLISH BLOCKED**.

## Identidade e precedência
- Project ID: `VERBO_NO_CHAO_EXCLUSIVO`. Projeto original cristão; não Corte Fino, não Because Of This, não CaptaPronto.
- Fonte de instrução do ciclo: anexo local `05_PROMPT_MASTER_VERBO_NO_CHAO_V2.txt` (SHA-256 `28cba0f640cad30d30e194304bd0963b8761158b4200a7d29efe8cf7e032632e`, 22.100 bytes). **O texto integral não foi publicizado no GitHub**; seu SHA identifica precisamente o upload inspecionado no chat.
- Fontes de estado superiores: contratos e decisões aprovadas, GitHub HEAD + logs, arquivos reais e direitos comprovados. Memória/chat/histórico são contexto, não aprovação ou prova de execução.

## Snapshot OBSERVADO
- Repo público `BORELLITO/corte-fino-engine`, `main` `b59bbbec9aef843bb7118f1328fab37e01b098b3`. Ausência de branch protection/rulesets verificada neste ciclo; mudanças em políticas de segurança do repositório compartilhado não foram realizadas.
- PR #41 draft, branch `verbo-no-chao/e01-stock-curation-gate-v1`, HEAD de origem `097baca265b995120c002c6aa9ea102369a53e4e`. Trigger único `contracts/e01_ltx23_s01_one_shot_trigger_20261118.json` já existe. S01 run **44372353305** cancelado (18/11 15h47 BRT), no step `Media dependencies`, depois de instalar gradio_client e antes da etapa que chamaria LTX. Nenhum MP4 ou artifact real. Não fazer rerun.
- PR #42 draft: hardening de fontes/render e áudio, HEAD `c1854bde2d3790320bd16bae1b9d9016378ce9ca`, ainda não integrado à PR #41.
- PR #43 draft: S03 source selection/physical review; uma fonte real foi decodificada mas **rejeitada por incoerência editorial**, HEAD `8067a7ed6ad344567454ce3f14a758b362137588`. Não promover.
- O arquivo de rough cut de ~70,43s e os JPEGs são prévia/storyboard, NÃO master de 12 filmagens. Roteiro E01 e seus hashes não foram modificados neste ciclo.
- CI do HEAD desta branch candidada `6d505853ff4c72c0bf5f27220a9671dd8a23635e`: Engine Gates run `44423769964`, **451 testes contabilizados, 13 ignorados e zero falhas**; 8 jobs e agregador em `44423769839` SUCCESS. Interpretar como verificação de código/contratos, não validação semântica de 12 vídeos.
- Teste físico zero GPU: run `44423770033` SUCCESS. `portable-ffmpeg==0.5.0`; FFmpeg hash `384742b75419584d065bbf372613f9f7e8ccf22525b421c16a2ee679a78ee748`; FFprobe hash `ae9051af68f52e7ad5706b442577689c74c02da618ca1590caf1ac7199f2931c`. Vídeo sintético de 0,833333 s, encode/probe/full decode PASS, sem criar fonte S01. Report SHA `49229744a42a48323759305e522b5dba8558f0ff7aa0afad6206f315d894f43a`.

## Auditoria C1–C10 — escopo efetivamente examinado
1. **Identidade e missão**: projeto VNC isolado em nomes/branch/contratos. Infra física compartilhada não é licença para copiar assets; **PASS condicional**.
2. **Histórico e aprovações**: pilotos E01 Habacuque e Salmo 13 distintos; direitos/publicação bloqueados; último estado remoto verificado. Não foi possível ler literalmente todos os chats legados, então o histórico integral é **UNKNOWN**, não simular auditoria de conversas inacessíveis.
3. **Inventário**: códigos de S01, assets de E01, contratos, 3 PRs, GH runs e pastas privadas já inventariados no projeto. Declaração sobre 12 master clips ainda **UNKNOWN/NOT AVAILABLE**.
4. **Arquitetura**: GH workflows misturados em repo público; branch exclusiva protege candidate edits, mas main não tem ruleset. PR #42 altera arquivos compartilhados: **revisão de escopo antes de integração**.
5. **Estado/idempotência**: P1 confirmado: instalação apt sem limite operacional útil levou a cancelamento S01. P0 potencial: `workflow_dispatch` na definição do workflow da PR #41; existência de workflow no default branch não constatada, portanto disponibilidade do acionamento manual é **UNKNOWN**. Na branch candidata, despacho manual removido + nonce ADD-only + histórico único exigidos. Geração permanece bloqueada.
6. **Bíblia/roteiro/criatividade**: base Habacuque 1:2–4 preservada; não inventar fala de Deus, milagre ou conteúdo factual. Sem edição de texto/voz neste ciclo. Validação teológica nova e visual subjetiva **NOT_RUN**.
7. **Direitos/custo/privacidade**: Free-tier, voz, música, stock e distribuição comercial sem prova completa `RIGHTS_PASS=UNKNOWN`, logo `PUBLISH_BLOCKED`. Não expor segredos, filmes privados ou arquivos pessoais no GitHub público. PIP de biblioteca versionada, artefato SHA do próprio binário verificado. Gasto externo: **nenhum serviço de geração acionado**.
8. **QA**: unit/contrato (GH green), teste físico synthetic FFmpeg/FFprobe green, zero modelos externos. QA das cenas S01–S12 e master não executado; oito especialistas representam módulos de auditoria determinística, **não oito LLMs independentes**.
9. **Telemetria e backups**: GH run IDs/SHAs, arquivos SHA, artifact JSON, ZIP físico íntegro; backup privado do conteúdo E01 verificado em contexto anterior; destino de novo vídeo **não testado**, pois MP4 S01 inexiste.
10. **Operação/retomada**: não repetir nonce gasto, não invocar workflow antigo, não force-push, sem aprovação comercial; retomar por checkpoint reconciliado com HEAD e novos eventos.

## Issues P0/P1 (evidência → causa-raiz → risco → correção → teste → estado)
- `VNC-P1-001` | Run 44372353305 cancelado durante `Media dependencies` | dependência apt lenta + timeout global de 6 min | sem S01 | `portable-ffmpeg==0.5.0` SHA-verified FFmpeg+FFprobe, sem apt, timeout dedicado | GH 44423770033 | **IMPLEMENTADO/TESTADO CANDIDATE**.
- `VNC-P0-002` | YAML original contém `workflow_dispatch` e não verifica unicidade física do nonce | contrato one-shot sem idempotência suficiente | gasto/duplicação acidental, se manualmente acessível | remover dispatch e validar commit ADD-only/único | unit test em run 44423769964 | **IMPLEMENTADO/TESTADO CANDIDATE; NÃO PROMOVIDO**. Disponibilidade manual real permanece incerta.
- `VNC-P1-003` | S01 sem MP4 >5,74s nem revisão de quadros/actor | geração nunca disparou no último run | impede 8 cenas ROOM_A | preflight e evento novo somente com decisão de custo/idempotência e licença | **BLOCKED**.
- `VNC-P1-004` | direitos de modelo host/voz/música/stock e autorização de publicação não provados | dependências externas não reconciliadas | master/publicação impróprios | manter `RIGHTS_PASS=UNKNOWN` e `PUBLISH_BLOCKED` | sem teste de licença conclusivo | **BLOCKED**.
- `VNC-P1-005` | PR #42/#43 permanecem draft e isolados, material privado fora do runner | integração/handoff de storage não concluídos | replay cloud e anti-regressão ainda não ativos na base | integrar sequencialmente com diff e checks exatos, sem afetar Corte Fino | CI por branch; integração não testada | **BLOCKED PARA PRODUÇÃO**.
- `VNC-P0-006` | repo público e branch main `protected=false`, rulesets=[] | sem barreira institucional detectável | risco de escrita acidental em código compartilhado | revisão de proteção de repositório com escopo sensível e autorização adequada, mais comparação de paths | status consultado, configuração não alterada | **PENDENTE**.

## Decisões e critérios (fail closed)
- Usar CLIP_ACQUISITION: filmagem própria/autorizada, stock verificável, IA só após licença/limite verificados.
- `PROMPT_DEFINED ≠ JOB_STARTED ≠ MP4_VERIFIED ≠ MOVEMENT_QA ≠ RIGHTS ≠ SCENE_APPROVED`.
- Nunca promover imagem estática com zoom/pan como vídeo cinematográfico real.
- Roteiro/áudio/legendas originais E01 continuam protegidos. Salmo 13 separado.
- `MASTER_BLOCKED`, `PUBLISH_BLOCKED`; autonomia para pesquisa, implementação em branch, testes de baixo risco. Não para assinatura/gasto, publicação, alteração de permissão ou exclusão irreversível.
- Releitura obrigatória do checkpoint e HEAD antes de decidir qualquer novo passo.

## Próxima ação única após este ciclo
**Conciliar e aplicar a contenção de nonce/manual dispatch na branch operacional após comparação de diff + testes, sem disparar GPU**. Depois avaliar se uma nova tentativa de aquisição LTX é realmente possível, de custo zero e com licença adequada, ou substituir a fonte/abordagem sem pressionar o usuário.
