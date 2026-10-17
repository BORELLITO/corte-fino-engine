# Corte Fino Engine

Motor de produção e preparação de publicações curtas do Corte Fino, separado em duas etapas manuais e auditáveis.

## Fluxo operacional

- **Motor 1 — Creator:** lê uma fonte autorizada, seleciona e renderiza exatamente cinco MP4 verticais e entrega uma pasta de lote no Google Drive.
- **Motor 2 — Publisher:** recebe duas pastas exatas, cada uma com cinco cortes, e prepara dez publicações para o mesmo dia ou para datas/períodos informados.
- Não existe handoff automático entre os motores: o Creator termina depois da entrega e nunca inicia o Publisher.
- A postagem final ocorre exclusivamente no YouTube Studio e no TikTok Studio, por Cloud Web Browser. Não há Metricool, agendador externo ou publicação por API.

## Grade fixa do Publisher

Fuso oficial: `America/Sao_Paulo`.

- **Bloco diurno:** 08h, 10h, 12h, 14h e 16h.
- **Bloco noturno:** 18h, 19h, 20h, 21h e 22h.

Cada pasta recebe um período próprio. Os pares data/horário não podem se sobrepor. O workflow é manual e exige duas pastas, duas datas/períodos, as fontes originais e confirmação explícita dos direitos.

## Contrato de qualidade

Cada lote precisa conter diretamente os arquivos `01.mp4` a `05.mp4`, sem subpastas, extras ou atalhos. O preflight valida o MP4 original em 1080x1920, H.264 High, `yuv420p`, AAC, 48 kHz, 30 fps, bitrate mínimo, decodificação integral e duração superior a 60 segundos.

O Publisher cria copy individual a partir da fala real: título do YouTube em caixa alta e sem pontuação, legenda em parágrafos arejados, dois emojis funcionais, CTA contextual, hashtags temáticas, vinte tags nativas do YouTube e crédito apenas à fonte original. ASR suspeito, título truncado, conflito de horário, checksum duplicado, fonte cruzada ou direitos não confirmados bloqueiam a rodada.

## Pacote browser-only

O manifesto v6 guarda os dez cortes, lote, pasta, checksum, copy e timestamps absolutos. O `browser-package` acrescenta o horário local, o link da pasta, a configuração esperada de audiência e os dados exatos para preencher cada Studio. O estado persistido não inclui transcrições integrais.

Operação manual:

1. Abrir o TikTok Studio, selecionar o MP4 original da pasta indicada e inserir a legenda do pacote.
2. Programar o horário local do lote e revisar a visibilidade antes de confirmar.
3. Repetir no YouTube Studio com título, descrição, tags, audiência e configuração de conteúdo sintético indicadas.
4. Conferir visualmente cada agendamento nas duas plataformas.

## Motor 1

O Creator mantém seus gates próprios: fonte autorizada, transcrição em português, mapa temporal, seleção fechada de cinco unidades de raciocínio, renderização vertical, validação técnica e upload idempotente na pasta do lote. Ele nunca publica automaticamente.

## Uso

1. Execute o workflow manual do Creator e copie o link exato da pasta com os cinco cortes.
2. Execute o workflow manual `Corte Fino Motor 2 — Publicar 10 Cortes` com as duas pastas, datas, períodos, fontes e confirmação de direitos.
3. Rode `dry-run`, `preflight` ou `browser-package` e faça a revisão humana antes de preencher os Studios.

A ferramenta não promete alcance ou viralização. A responsabilidade por autorização, direitos e confirmação final das publicações permanece com o usuário.
