# Corte Fino Publisher 2.1

O Publisher é o Motor 2 do Corte Fino. Ele recebe duas pastas exatas do Google Drive, cada uma com cinco MP4s prontos pelo Creator, prepara dez publicações e entrega um pacote fechado para postagem no Cloud Web Browser.

## Contrato de entrada

Cada rodada exige:

- pasta A: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- pasta B: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- data local e período de cada pasta;
- canal/fonte original de cada pasta;
- confirmação de direitos das duas fontes.

Períodos em America/Sao_Paulo:

- day: 08h, 10h, 12h, 14h e 16h;
- night: 18h, 19h, 20h, 21h e 22h.

As duas pastas podem ter datas diferentes, mas seus pares data/horário não podem se sobrepor. A pasta é uma fronteira rígida: subpastas, arquivos extras, lotes vizinhos, duplicidade de checksum ou numeração incorreta bloqueiam o preparo.

## Qualidade e copy

O Publisher baixa e valida o MP4 original. O preflight exige 1080x1920, H.264 High, yuv420p, AAC, 48 kHz, 30 fps, bitrate mínimo, decodificação integral e duração superior a 60 segundos.

Cada corte recebe copy individual:

- título do YouTube em caixa alta, sem pontuação;
- legenda em blocos arejados, com CTA contextual;
- exatamente dois emojis funcionais;
- hashtags derivadas do assunto, sem branding automático do Corte Fino;
- crédito somente ao canal/fonte original;
- tags nativas do YouTube;
- QA bloqueante para ortografia, ASR suspeito, truncamento, espaçamento e evidência desconectada do corte.

## Manifesto v6

O manifesto contém dois lotes, dez cortes globais, índice local, pasta, checksum, copy e timestamp absoluto de cada publicação. Manifestos de cinco cortes ou versões anteriores são rejeitados.

O estado persistido no Git não contém transcrições integrais. O pacote browser-package contém somente os dados necessários para preencher os Studios.

## Publicação oficial

A publicação é feita exclusivamente por Cloud Web Browser, diretamente nas interfaces oficiais:

1. abrir o TikTok Studio;
2. carregar o MP4 original da pasta correta;
3. inserir a legenda revisada;
4. programar o horário do lote;
5. repetir no YouTube Studio com título, descrição, tags e configuração de audiência;
6. revisar o resultado final em cada plataforma.

O Publisher não publica por API ou qualquer agendador externo. As funções legadas de publicação permanecem bloqueadas no código para impedir conflito ou duplicidade.

## Comandos

  python -m publisher.cli prepare \
    --folder-id "LINK_PASTA_A" --folder-2-id "LINK_PASTA_B" \
    --date-1 2026-10-18 --date-2 2026-10-18 \
    --period-1 day --period-2 night \
    --source-name "CANAL A" --source-name-2 "CANAL B" \
    --confirm-rights

  python -m publisher.cli browser-package
  python -m publisher.cli report
  python -m publisher.cli youtube --dry-run
  python -m publisher.cli tiktok --dry-run

## Proteções operacionais

- duas pastas obrigatórias e isoladas;
- dez slots únicos;
- timestamps locais convertidos e revisados antes da postagem;
- validação de conta e tela correta no Studio;
- revisão visual antes de confirmar cada agendamento;
- manifesto imutável e revisão de cada item no Studio antes da confirmação;
- falha parcial interrompe a rodada e exige reconciliação;
- Creator e Publisher continuam separados.

