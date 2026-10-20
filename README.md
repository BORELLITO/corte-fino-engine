# Corte Fino Engine

Motor de produção e preparação de publicações curtas do Corte Fino, separado em duas etapas manuais e auditáveis.

## Fluxo operacional

- **Motor 1 — Creator:** lê uma fonte autorizada, seleciona e renderiza exatamente cinco MP4 verticais e entrega uma pasta de lote no Google Drive.
- **Motor 2 — Publisher:** recebe duas pastas exatas, cada uma com cinco cortes, e prepara cinco publicações por dia em duas datas diferentes.
- Não existe handoff automático entre os motores: o Creator termina depois da entrega e nunca inicia o Publisher.
- A postagem final ocorre exclusivamente no YouTube Studio e no TikTok Studio, por Cloud Web Browser. Não há serviço externo de agendamento nem API de publicação.

## Grade fixa do Publisher

Fuso oficial: `America/Sao_Paulo`.

- **Grade diária oficial:** 10h, 12h, 14h, 16h e 18h.
- O corte mais forte recebe prioridade de 10h; depois 16h, 18h, 12h e 14h.

Cada pasta representa um dia de publicação. As duas pastas precisam usar datas diferentes; o padrão operacional é lote A em um dia e lote B no dia seguinte. O workflow é manual e exige duas pastas, duas datas, as fontes originais e confirmação explícita dos direitos.

## Contrato de qualidade

Cada lote precisa conter diretamente os arquivos `01.mp4` a `05.mp4`, sem subpastas, extras ou atalhos. O preflight valida o MP4 original em 1080x1920, H.264 High, `yuv420p`, AAC, 48 kHz, 30 fps, bitrate mínimo, decodificação integral e duração superior a 60 segundos.

O Publisher cria copy individual a partir da fala real: título do YouTube em caixa alta e sem pontuação, legenda em parágrafos arejados, dois emojis funcionais, CTA contextual, hashtags temáticas, vinte tags nativas do YouTube e crédito apenas à fonte original. ASR suspeito, título truncado, conflito de horário, checksum duplicado, fonte cruzada ou direitos não confirmados bloqueiam a rodada.

## Pacote browser-only

O manifesto v7 guarda os dez cortes distribuídos em cinco por dia, lote, pasta, checksum, copy e timestamps absolutos. O `browser-package` acrescenta o horário local, o link da pasta, a configuração esperada de audiência e os dados exatos para preencher cada Studio. A audiência do TikTok é hard-locked em `PUBLIC_TO_EVERYONE`; o preflight falha se o pacote não contiver a confirmação `Todos (público)` e a verificação pós-publicação. O estado persistido não inclui transcrições integrais.

Operação manual:

1. Abrir o TikTok Studio, selecionar o MP4 original da pasta indicada e inserir a legenda do pacote.
2. Antes de programar, abrir a privacidade de cada TikTok e confirmar **Todos (público)**. Se aparecer qualquer outra opção, interromper a rodada.
3. Programar o horário local do lote e revisar novamente a visibilidade antes de confirmar.
4. Após o horário, conferir se o relógio desapareceu e se o vídeo recebeu URL/visualizações; o agendamento sozinho não é considerado publicação pública.
5. Repetir no YouTube Studio com título, descrição, tags, audiência e configuração de conteúdo sintético indicadas.
6. Conferir visualmente cada agendamento nas duas plataformas.

## Motor 1

O Creator mantém seus gates próprios: fonte autorizada, transcrição em português, mapa temporal, análise do arco entre abertura/desenvolvimento/fechamento, seleção fechada de cinco unidades de raciocínio com diversidade temporal, renderização vertical, validação técnica e upload idempotente na pasta do lote. A camada de legendas usa revisão contextual conservadora: corrige ruído ortográfico do ASR com vocabulário português, palavras vizinhas e metadados da fonte, preserva nomes/gírias/siglas, normaliza capitalização e pontuação com base em pausas reais e mantém cada bloco preso aos timestamps das palavras. Ele nunca publica automaticamente.

O destino de saída do Creator é configurado exclusivamente pelo secret `DRIVE_FOLDER_ID`; ele não reutiliza o destino do Publisher nem um ID de fallback. O motor registra a execução e a qualidade do lote, mas ainda não ajusta automaticamente a seleção com métricas posteriores de retenção ou alcance.

## Uso

1. Execute o workflow manual do Creator e copie o link exato da pasta com os cinco cortes.
2. Execute o workflow manual `Corte Fino Motor 2 — Publicar 5 por Dia` com as duas pastas, duas datas diferentes, fontes e confirmação de direitos.
3. Rode `dry-run`, `preflight` ou `browser-package` e faça a revisão humana antes de preencher os Studios.

A ferramenta não promete alcance ou viralização. A responsabilidade por autorização, direitos e confirmação final das publicações permanece com o usuário.
