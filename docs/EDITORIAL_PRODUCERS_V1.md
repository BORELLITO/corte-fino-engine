# VERBO NO CHÃO — Camada editorial de produção v1

Estado: `IMPLEMENTED_IN_FEATURE_BRANCH / REQUIRES_OWNER_REVIEW`

## O que executa de verdade

1. `agents/editorial_seed.json` versiona as decisões aprovadas (identidade, público, promessa e voz teológica) e distingue claramente o que é PROPOSTO.
2. `agents/content_production.py` lê as políticas canônicas, valida o catálogo de 39 pautas e produz artefatos reais, reproduzíveis, legíveis e verificáveis sem APIs externas.
3. `.github/workflows/verbo-no-chao-agents.yml` roda a produção em `editorial_production`, armazena os artefatos no GitHub Actions e entrega `operations/*.json` a cada um dos oito auditores.
4. `agents/team.py` verifica se estratégia e plano mantêm as decisões aprovadas, fonte com hash, aprovação pendente, 39 ideias únicas e publicação bloqueada.
5. O coordenador reúne os oito relatórios; aprovação automática de publicação é impossível. A planilha futura de métricas ainda não existe e o agente de desempenho permanece bloqueado por ausência de dados reais.

## Entregas produzidas

| Arquivo do artefato `vnc-editorial-deliverables` | Conteúdo |
|---|---|
| `editorial-deliveries/editorial_strategy.md` | Estratégia humana: público, promessa, diferenciação, cinco pilares propostos, guardrails |
| `editorial-deliveries/90_day_plan.md` | 13 semanas, 39 ideias com referência, título, gancho, aplicação e trava teológica |
| `operations/niche_strategy.json` | Estratégia em dados estruturados para o agente 01 e outros módulos |
| `operations/growth_90d.json` | 39 slots relativos em janela de 90 dias, três marcos de revisão, sem datas reais |
| `editorial-deliveries/production_report.json` | Lista de artefatos produzidos e SHA-256 do conteúdo e fontes |

Arquivos de execução são gerados no runner, excluídos do Git, e retidos 14 dias no GitHub Actions, para não tratar propostas como decisões canônicas e evitar poluir o repositório.

## Decisões preservadas

- Nome: **VERBO NO CHÃO**.
- Promessa: **Dar sentido bíblico às dores, dúvidas e recomeços da vida real — com contexto, profundidade e esperança honesta.**
- Público central: pessoas enfrentando dificuldades; público secundário: cristãos em busca de aprofundamento.
- Voz teológica: cristã ampla, bíblica, cristocêntrica, não sectária.
- Não inventar revelações, prometer resultados, explorar medo/culpa, substituir ajuda profissional ou usar texto literal de tradução sem direitos comprovados.
- Salmo 13 é o piloto já existente: não muda de estado nem entra na fila nova.
- Clean-room: proibido importar material, voz, código operacional, identidade ou fluxos de outros canais.
- Publicação permanece desautorizada por padrão; qualquer autorização futura é separada da aprovação de roteiro ou vídeo.

## Pontos ainda em revisão

- **Assinatura** “Bíblia para a vida real” é uma proposta, não aprovação final.
- **Cinco pilares** e **39 pautas** são propostas editoriais, não roteiros validados ou decisões finais.
- **Cadência** de três Shorts semanais e **alvo** de 75 s são hipóteses reversíveis; não alteram o piloto nem criam agenda.
- Dias 1/4/6 são relativos a um início ainda NÃO DEFINIDO. Não há data real nem upload agendado.
- Referências são âncoras para estudo, não exegese automática: cada pauta precisa de pesquisa bíblica e revisão editorial antes do roteiro.
- Não há navegação web, LLM criativo, pesquisa atual, acesso a YouTube Analytics ou publicação automática nesta camada. O produtor é **determinístico, baseado em fonte versionada**, não um agente de IA autônomo.

## Testes e critérios de aceitação

- Testar geração determinística, 39 ideias distintas, 13 semanas, último slot no Dia 90 e exclusão de Salmo 13.
- Testar status de revisão, bloqueio de publicação, ausência de datas, direitos não aprovados, hashes e arquivo de resultado.
- Testar bloqueio de duplicidade de referência, gancho, falsas promessas, alteração da promessa e falsificação de aprovação.
- GitHub Actions do commit final: suíte `Engine Gates` verde e workflow de produção + 8 auditores + coordenador verde.
- `PASS_CHECKED_SCOPE` dos agentes 01 e 02 significa validade do artefato **como proposta**, nunca liberação de canal/publicação.
- O master audiovisual, direitos de voz e visuais e métricas continuam sujeitos a gates independentes.

## Rollback e dependências

Camada criada sobre a branch isolada `verbo-no-chao/specialist-team-v1`, que é a PR #26 ainda não integrada à `verbo-no-chao/bootstrap`. Merge deve respeitar a dependência: PR #26 antes desta camada. Não mesclar na `main` histórica. Não foram alterados os contratos, arquivos e decisões do piloto.
