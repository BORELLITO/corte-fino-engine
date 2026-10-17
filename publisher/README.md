# Corte Fino Publisher 2.0

O Publisher é o Motor 2 do Corte Fino. Ele recebe **duas pastas exatas do Google Drive**, cada uma com cinco MP4s prontos pelo Creator, e prepara dez publicações por rodada para YouTube Shorts e TikTok.

## Contrato de entrada

Cada rodada exige:

- pasta A: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- pasta B: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- data local e período de cada pasta;
- canal/fonte original de cada pasta;
- confirmação de direitos das duas fontes.

O Publisher nunca procura subpastas, pastas vizinhas, lotes anteriores ou arquivos de outra rodada. Qualquer arquivo extra, subpasta, duplicidade de pasta, duplicidade de checksum ou numeração incorreta bloqueia o preparo.

Períodos fixos em America/Sao_Paulo:

- day: 08h, 10h, 12h, 14h e 16h;
- night: 18h, 19h, 20h, 21h e 22h.

A pasta A e a pasta B podem ter datas diferentes, mas seus pares data/horário não podem se sobrepor. O corte de cada pasta é usado nos dois canais.

## Qualidade e copy

O Publisher baixa o MP4 original do Drive e não reencoda o arquivo. O preflight exige 1080x1920, H.264 High, yuv420p, AAC, 48 kHz, 30 fps, bitrate mínimo, decodificação integral e duração superior a 60 segundos.

Cada corte recebe transcrição local e copy individual:

- título do YouTube em caixa alta, sem pontuação;
- legenda em blocos arejados, com CTA contextual;
- exatamente dois emojis funcionais;
- hashtags derivadas do assunto, sem branding automático do Corte Fino;
- crédito somente ao canal/fonte original;
- tags nativas do YouTube;
- QA bloqueante para ortografia, ASR suspeito, truncamento, espaçamento, hashtags e evidência desconectada do corte.

## Manifesto v6

O manifesto contém dois lotes, dez cortes globais e o índice local de cada corte. Cada item também guarda a pasta, checksum, tamanho, copy, data/hora absoluta de YouTube e TikTok e estado de reconciliação.

Antes da publicação, o Publisher reconfirma no Drive:

- ID e pasta pai;
- nome e tipo MIME;
- tamanho;
- checksum;
- ausência de lixeira;
- marcador anti-duplicidade.

Manifestos v5 ou de cinco cortes são rejeitados. O estado persistido no Git não contém transcrições integrais.

## YouTube

Os dez vídeos são enviados diretamente pela API oficial como private com publishAt, idioma pt-BR, categoria 24, selfDeclaredMadeForKids=false, containsSyntheticMedia=false quando aplicável e notifySubscribers=false.

O Publisher grava uma intenção antes do upload, persiste o ID imediatamente depois do insert, aguarda o processamento e reconcilia estados pendentes antes de permitir qualquer reenvio.

## TikTok

O agendamento externo não participa do fluxo do Corte Fino.

O workflow dedicado roda automaticamente em UTC nas janelas que cobrem 08h–22h de São Paulo. Em cada execução ele:

1. carrega o manifesto v6;
2. valida conta e usuário esperado;
3. seleciona apenas o próximo corte vencido;
4. verifica novamente o arquivo no Drive;
5. publica diretamente pela API oficial;
6. grava publish_id e estado no Drive;
7. reconcilia IDs pendentes antes de iniciar novo upload.

A publicação direta exige PUBLISHER_TIKTOK_DIRECT_ENABLED=1, OAuth válido, escopo video.publish, aprovação/auditoria do app quando exigida e PUBLISHER_TIKTOK_EXPECTED_USERNAME correto.

## Comandos

  python -m publisher.cli prepare \
    --folder-id "LINK_PASTA_A" --folder-2-id "LINK_PASTA_B" \
    --date-1 2026-10-18 --date-2 2026-10-18 \
    --period-1 day --period-2 night \
    --source-name "CANAL A" --source-name-2 "CANAL B" \
    --confirm-rights

  python -m publisher.cli report
  python -m publisher.cli report --remote
  python -m publisher.cli youtube --dry-run
  python -m publisher.cli youtube
  python -m publisher.cli tiktok --dry-run
  python -m publisher.cli tiktok --due-only
  python -m publisher.cli verify-tiktok
  python -m publisher.cli verify-google --folder-id "LINK_A" --folder-2-id "LINK_B"
  python -m publisher.cli preflight --folder-id "LINK_A" --folder-2-id "LINK_B"

## Proteções operacionais

- duas pastas obrigatórias e isoladas;
- dez slots únicos;
- nenhuma publicação adiantada;
- um TikTok vencido por execução automática;
- concorrência serializada entre preparo e publicação;
- direitos, conta, fonte, checksum e manifesto validados;
- falha parcial interrompe a rodada e exige reconciliação;
- o Creator continua separado e não é acionado automaticamente pelo Publisher.

