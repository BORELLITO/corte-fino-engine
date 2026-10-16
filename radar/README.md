# Corte Fino — Motor 0: Radar Viral

O **Motor 0** pesquisa oportunidades antes da edição. Ele é propositalmente isolado do Motor 1 (Creator) e do Motor 2 (Publisher): não baixa vídeos, não cria cortes e não publica nada.

## Objetivo

Detectar vídeos longos recentes no YouTube que tenham sinais combinados de:

- velocidade de visualizações;
- densidade de comentários e likes;
- comentários com reação e divergência;
- carga emocional;
- conflito/polêmica;
- baixa saturação relativa para um tema com demanda;
- preferência editorial por fontes como Flow, Inteligência Ltda. e canais semelhantes.

O resultado é um relatório com links de origem. A decisão de usar um vídeo continua humana.

## Arquitetura

1. **Google Trends Brasil** fornece temas que estão ganhando atenção.
2. **Temas editoriais fixos** cobrem bets, relacionamento, religião, crime, dinheiro, IA, saúde mental, família, carros, celebridades e ciência.
3. **Consultas de fonte** mantêm Flow, Inteligência Ltda., Cortes do Flow, Cortes do Inteligência, RedCast e Podpah no radar.
4. **YouTube Data API v3** procura vídeos longos publicados na janela definida.
5. O método videos.list coleta duração, views, likes, comentários e o status de licença informado pelo YouTube.
6. Para os pré-candidatos mais fortes, commentThreads.list amostra comentários relevantes e mede reação/divergência.
7. O motor calcula um radar_score de 0–100 apenas para conteúdo não político.
8. Conteúdo político/eleitoral é separado em uma watchlist factual, sem score editorial nem recomendação comparativa.
9. O workflow publica o relatório no Summary da Action, salva JSON/CSV/Markdown como artifact e mantém uma issue fixa atualizada.

## Score não político

Pesos da versão 1:

- 24% velocidade de views;
- 18% calor/divergência dos comentários;
- 13% engajamento;
- 13% Search Gap;
- 12% conflito/polêmica;
- 10% emoção;
- 5% atualidade;
- 5% preferência de fonte.

Vídeos encontrados por mais de uma rota de busca recebem uma pequena confirmação adicional.

## Search Gap

O TikTok Creator Search Insights não é consumido diretamente pelo motor. A versão 1 usa um proxy automatizável:

**demanda do Google Trends Brasil × oferta recente do YouTube**

A oferta vem de pageInfo.totalResults da busca do YouTube e deve ser tratada como aproximada. A ideia não é afirmar volume absoluto, mas priorizar temas com atenção crescente e menos saturação relativa.

## Direitos e integridade

- Estar em Flow, Inteligência ou qualquer outro canal **não é interpretado como autorização automática**.
- O motor registra o campo status.license retornado pelo YouTube.
- creativeCommon é registrado, mas ainda exige cumprimento dos termos e atribuição aplicáveis.
- Todo o resto fica como manual_review.
- Alegações graves, morte/autolesão e conteúdo envolvendo menores recebem flags.
- O Radar nunca altera o título original para transformar alegação em fato.

## Política/eleições

Para conteúdo político/eleitoral brasileiro, o Motor 0 não gera nota editorial nem escolhe “melhor candidato”. Ele mostra apenas uma watchlist cronológica com métricas públicas brutas do vídeo.

## Frequência

O workflow roda três vezes ao dia:

- 08:30 BRT;
- 14:30 BRT;
- 20:30 BRT.

Também pode ser acionado manualmente.

A configuração usa no máximo 24 consultas por rodada para manter o consumo previsível.

## Configuração única

Crie um secret no repositório:

YOUTUBE_API_KEY

A chave precisa ter **YouTube Data API v3** habilitada. Restrinja a chave à API do YouTube no Google Cloud.

Depois, execute:

**Actions → Corte Fino Motor 0 — Radar Viral → Run workflow**

## Saídas

- radar/output/radar_latest.md — leitura humana;
- radar/output/radar_latest.json — integração futura;
- radar/output/radar_latest.csv — auditoria/análise;
- issue fixa “🎯 Corte Fino — Radar Viral (automático)”;
- artifact da execução por 14 dias.

## Contrato com os outros motores

O Motor 0 termina no relatório.

Ele **não** dispara o Motor 1 automaticamente e **não** interfere no Publisher. Isso preserva o contrato já existente:

Radar → escolha humana da fonte → Motor 1 → link da pasta com 5 cortes → Motor 2

Uma integração automática entre Radar e Creator só deve ser criada como etapa separada e explicitamente aprovada.
