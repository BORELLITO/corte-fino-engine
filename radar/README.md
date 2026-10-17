# Corte Fino — Motor 0: Radar Viral V2

O **Motor 0** é a camada de inteligência editorial anterior ao Creator. Ele descobre, monitora e prioriza fontes; não baixa vídeos, não cria cortes e não publica nada.

## Pipeline

`Discovery → Normalizer → Momentum → Breakout → Content Brain → Comment Brain → Cutability → Rights/Risk → Decision`

### Discovery
- Google Trends Brasil;
- temas editoriais fixos;
- Flow, Inteligência Ltda., RedCast, Podpah e outras fontes reconhecidas;
- buscas extras informadas manualmente.

### Normalizer
- vídeo longo (mínimo operacional de 20 min);
- idioma PT-BR quando a fonte não é reconhecida;
- formato conversacional/entrevista/debate;
- exclusão de conteúdo marcado para crianças;
- deduplicação por videoId;
- identificação por channelId quando disponível.

### Momentum Engine
O Radar mantém snapshots privados entre rodadas. Para cada vídeo calcula:
- views/h no intervalo mais recente;
- comentários/h recentes;
- razão entre velocidade recente e média desde a publicação;
- aceleração entre dois intervalos;
- estado: `NEW`, `ACCELERATING`, `RISING`, `STEADY`, `COOLING` ou `STALE`.

O estado é persistido como `history.json` na pasta privada `RADAR_CORTE_FINO` do Google Drive, sem commit no repositório.

### Breakout Engine
Compara o views/h de um vídeo com a mediana de outros vídeos recentes do mesmo canal disponíveis na rodada. Quando há amostra suficiente, gera:
- baseline do canal;
- breakout ratio;
- breakout score.

Assim, um vídeo pequeno pode superar um vídeo grande quando está muito acima do padrão do próprio canal.

### Content Brain
- carga emocional;
- conflito/polêmica;
- estrutura de podcast/debate;
- parser de capítulos/timecodes da descrição;
- heat score dos capítulos;
- indicação do capítulo mais promissor.

### Comment Brain
Para os pré-candidatos mais fortes, consulta duas amostras:
- comentários por relevância;
- comentários mais recentes.

Mede reação, divergência e respostas. Comentários recentes recebem peso maior para detectar mudança de temperatura.

### Cutability Engine
Estima se o vídeo tem estrutura favorável para gerar cortes:
- fonte reconhecida;
- duração suficiente;
- capítulos;
- capítulos emocionalmente fortes;
- formato entrevista/debate/podcast;
- divergência de comentários.

É um score de triagem, não substitui a análise narrativa do Motor 1.

## Score V2 — conteúdo não político

- 18% momentum;
- 12% velocidade média;
- 12% breakout relativo ao canal;
- 10% engajamento;
- 14% temperatura dos comentários;
- 9% conflito/polêmica;
- 8% emoção;
- 10% cutability;
- 3% Search Gap;
- 2% freshness;
- 2% fonte reconhecida.

O relatório mostra também `confidence_score` separado do score editorial.

### Estados de decisão
- **HOT**: score ≥ 68
- **PROMISING**: score ≥ 57
- **WATCH**: score ≥ 47
- **DROP**: abaixo disso ou sem tensão editorial suficiente

Conteúdo político/eleitoral brasileiro permanece em **watchlist factual**, sem score editorial ou recomendação comparativa.

## Search Gap
Continua como proxy experimental:

`demanda Google Trends × oferta aproximada recente no YouTube`

O número de resultados do YouTube é tratado como aproximação. O peso foi reduzido na V2 para impedir que uma lacuna de busca domine um vídeo fraco editorialmente.

## Segurança e privacidade

- A API key nunca é impressa deliberadamente em logs.
- URLs de erro são sanitizadas antes de serem exibidas.
- O workflow real não roda mais em todo push.
- Push/PR executa apenas testes, sem consumir YouTube API.
- A varredura real roda somente por agenda ou `workflow_dispatch`.
- Como o repositório atualmente é público, o conteúdo integral do Radar **não é publicado em Issue nem no Job Summary**.
- O relatório completo é enviado para a pasta privada `RADAR_CORTE_FINO` no Google Drive. Se existir o secret `RADAR_DRIVE_FOLDER_ID`, ele tem prioridade; caso contrário o motor reutiliza a pasta-base já configurada pelo projeto.
- O histórico de momentum fica em cache do GitHub Actions e é ignorado pelo Git.

## Frequência

- 08:30 BRT
- 20:30 BRT

Padrão atual:
- até 6 tendências;
- até 18 consultas principais por rodada;
- no máximo 3 temas manuais por rodada, sem expulsar as fontes principais;
- os temas editoriais fixos são rotacionados entre as execuções para cobrir o catálogo inteiro;
- até 24 vídeos pré-selecionados recebem análise dupla de comentários;
- entrega visual padrão: Top 5 compacto, até 3 Search Gaps e até 3 itens políticos factuais.

## Arquivos de saída
- `radar/output/radar_latest.md`
- `radar/output/radar_latest.json`
- `radar/output/radar_latest.csv`

Os três arquivos são atualizados de forma idempotente na pasta privada `RADAR_CORTE_FINO` no Google Drive.

## Contrato com os outros motores

`Radar → escolha humana da fonte → Motor 1 → 5 cortes → Motor 2`

O Motor 0 não aciona automaticamente o Creator nem o Publisher.

## Limitações conhecidas

1. Breakout usa a amostra de vídeos disponível na rodada, não um histórico profundo do canal.
2. Cutability V2 usa metadados, capítulos e sinais editoriais; ainda não lê a transcrição integral.
3. Search Gap usa proxy de demanda/oferta e não o Creator Search Insights do TikTok.
4. A primeira aparição de um vídeo não possui delta temporal real; recebe estado `NEW` e confiança menor. A partir da segunda rodada, o relatório também mostra movimento de score.
5. Fonte reconhecida ainda deve passar por revisão de licença/autorização antes de reutilização.
