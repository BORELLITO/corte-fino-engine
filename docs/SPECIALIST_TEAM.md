# VERBO NO CHÃO — Equipe de oito especialistas (v1)

> **Atualização em camada separada (PR dependente):** os agentes 01 (estratégia) e 02 (planejamento 90 dias) passam a executar produtores determinísticos antes das auditorias. Eles geram documentos de revisão reais, mas ainda não são modelos de IA autônomos. Consulte [EDITORIAL_PRODUCERS_V1.md](EDITORIAL_PRODUCERS_V1.md). Os demais agentes permanecem auditores, e a publicação segue bloqueada.

## Fonte canônica e status

A arquitetura aprovada tem oito especialistas. Esta versão executa **oito auditorias independentes, reais e de leitura**, cada uma em um job isolado do GitHub Actions. O coordenador exige os oito relatórios distintos e integra seus bloqueios e provas. Não são oito modelos de linguagem permanentes; criatividade autônoma, prospecção de tendências e geração multimídia ainda dependem de executores e fontes autorizados.

Branch canônica do projeto: `verbo-no-chao/bootstrap`. Branch histórica `main` não é modificada. Não importar mídia, código operacional, vozes, prompts ou identidade do Corte Fino ou do Because Of This.

## Blocos e responsabilidades

| Agente | Trabalho executável nesta versão | Bloqueio declarado quando faltam evidências |
|---|---|---|
| 01 — Estrategista de nicho | Lê política clean-room e engine lock | Falta estratégia de público e diferencial aprovada |
| 02 — Planejador 90 dias | Lê plano de metas/cadência se existir | Falta plano de 90 dias verificável |
| 03 — Pesquisador de ideias | Valida rastreabilidade da decisão de fonte e URLs do piloto | Não conclui liberação de direitos de terceiros |
| 04 — Roteirista de retenção | Executa os validadores editoriais existentes | Não substitui revisão bíblica ou evidência de retenção |
| 05 — Títulos e capas | Valida opções e briefing documentados | Ausência de pacote de títulos e capa |
| 06 — Especialista em Shorts | Executa o gate de manifesto e exige arquivos físicos | Sem MP4 e áudio reais, não libera master |
| 07 — Analista de desempenho | Verifica métricas com origem e data se fornecidas | Sem dados reais, não inventa números |
| 08 — Especialista em monetização | Verifica status de direitos de voz, visuais, trilha e monetização | Direitos pendentes impedem liberação |

## Orquestração

1. Em `push` de uma branch `verbo-no-chao/**` ou PR para `verbo-no-chao/bootstrap`, o workflow `.github/workflows/verbo-no-chao-agents.yml` dispara oito jobs independentes.
2. Cada job lê somente evidências locais e gera `agent-reports/<id>.json`, incluindo hashes SHA-256 das fontes efetivamente consultadas.
3. Os relatórios são preservados como artefatos do GitHub Actions por 14 dias.
4. O coordenador recebe os oito registros, rejeita ausência, duplicação ou tentativa de afirmar publicação e gera `agent-team-report.json`.
5. Gate incompleto retorna `BLOCKED` com motivo; isso **não significa falha técnica da CI**. O CI só fica vermelho diante de falha de execução ou inconsistência na coordenação.

## Controles de segurança

- GitHub Actions: `permissions: contents: read`.
- Sem segredos, API paga, publicações, postagem automática, mudança de contas ou acesso a dados pessoais.
- Oito relatórios não equivalem a oito modelos de IA com sessões persistentes; não declarar geração automática de roteiro/arte/vídeo que não ocorreu.
- Equipe jamais autoriza publicação nem promove Salmo 13 por conta própria.
- `PASS_CHECKED_SCOPE` significa apenas que a verificação limitada daquele especialista passou, **não** uma aprovação completa do vídeo.
- O projeto permanece cloud-only, com POCO como controle apenas.
- `schedule` automático não foi habilitado porque o GitHub executa cron somente a partir da branch padrão, que neste projeto é a `main` histórica/congelada. Habilitar recorrência requer uma decisão de arquitetura separada.

## Documentos de evidência futuros

Criar somente com fatos reais e decisão aprovada:
- `operations/niche_strategy.json`;
- `operations/growth_90d.json`;
- `operations/titles_covers.json`;
- `operations/metrics_snapshot.json`.

## Integração e rollback

Código alterado apenas em branch isolada, sujeito a PR e testes. Nenhum dado histórico do Salmo 13 é editado. Pode ser revertido removendo a integração do PR; nenhuma publicação ou operação externa está ligada ao coordenador.

## Próxima evolução

Conectar executores criativos e fontes de dados de forma econômica, com contratos específicos e provas de licença; então ampliar verificações para produção de conteúdo, sempre sem saltar os gates independentes de QA, direitos, áudio, mídia e aprovação do proprietário.
