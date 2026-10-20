# Corte Fino Publisher 2.4 — Control Plane

O Publisher é o Motor 2 do Corte Fino. Ele recebe duas pastas exatas do Google Drive, cada uma com cinco MP4s prontos pelo Creator, e distribui os dez cortes em dois dias: cinco publicações por dia. A versão 2.4 mantém o Distribution Guard, a cadência de cinco por dia e adiciona Account Identity Guard, Publication Receipt e reconciliação.

## Contrato de entrada

Cada rodada exige:

- pasta A: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- pasta B: cinco MP4 diretos, numerados 01, 02, 03, 04 e 05;
- data local de cada pasta;
- canal/fonte original de cada pasta;
- confirmação de direitos das duas fontes.

Grade diária em America/Sao_Paulo:

- perfil experimental atual: 10h, 12h, 14h, 16h e 18h;
- prioridade editorial temporária: 10h, 16h, 18h, 12h e 14h;
- estes horários são hipótese operacional em medição, não regra permanente de aprendizado.

As duas pastas obrigatoriamente usam datas diferentes. A pasta A ocupa um dia e a pasta B o outro, impedindo dez publicações no mesmo dia. A pasta é uma fronteira rígida: subpastas, arquivos extras, lotes vizinhos, duplicidade de checksum ou numeração incorreta bloqueiam o preparo.

## Qualidade e copy

O Publisher baixa e valida o MP4 original. O preflight exige 1080x1920, H.264 High, yuv420p, AAC, 48 kHz, 30 fps, bitrate mínimo, decodificação integral e duração superior a 60 segundos.

Cada corte recebe copy individual:

- título do YouTube em caixa alta, sem pontuação;
- legenda em blocos arejados, com CTA contextual;
- exatamente dois emojis funcionais;
- hashtags derivadas do assunto, sem branding automático do Corte Fino;
- crédito somente ao canal/fonte original;
- tags nativas do YouTube;
- QA bloqueante para ortografia, ASR suspeito, truncamento, espaçamento e evidência desconectada do corte;
- bloqueio de descrições editoriais genéricas como "uma conversa do...", "provoca reflexão", "qual foi a sua leitura" e equivalentes;
- tags de descoberta priorizam assunto, fonte e contexto; o branding Corte Fino não ocupa vagas de descoberta.

## Distribution Guard

Quando houver padrão de 0–5 views, use o modo diagnóstico em vez de aumentar o volume.

O comando `diagnostic-package`:

- escolhe três cortes do mesmo lote/fonte para manter um cluster de audiência;
- prioriza os três maiores `viral_score` daquele lote;
- recomenda 11h30, 16h30 e 20h30 no dia do lote;
- marca a publicação como teste controlado manual;
- exige TikTok público e verificação de elegibilidade no Para Você;
- exige YouTube público, sem restrições e leitura de `Mostrado no feed` / `Visualizaram x deslizaram` após 24h;
- não apaga, não reposta e não altera os sete cortes restantes.

Esse modo existe para separar DISTRIBUIÇÃO de PERFORMANCE. Ele não afirma shadowban e não interpreta retenção quando a amostra é insuficiente.

## Manifesto v8

O manifesto contém dois lotes, dez cortes globais distribuídos em duas datas diferentes, índice local, pasta, checksum, copy, commit do motor, contas-alvo e timestamp absoluto de cada publicação. Cada data contém exatamente cinco slots.

O estado operacional não é commitado no repositório público. O workflow mantém os JSONs somente como artefato temporário de 1 dia. O pacote browser-package contém os dados necessários para preencher os Studios e a conta esperada em cada plataforma.

## Publicação oficial

A publicação é feita exclusivamente por Cloud Web Browser, diretamente nas interfaces oficiais:

1. abrir o TikTok Studio;
2. carregar o MP4 original da pasta correta;
3. inserir a legenda revisada;
4. programar o horário do lote;
5. repetir no YouTube Studio com título, descrição, tags e configuração de audiência;
6. revisar o resultado final em cada plataforma.

O Publisher não publica por API ou qualquer agendador externo. Ele somente prepara e valida o pacote que será confirmado manualmente no Studio.

## Comandos

  python -m publisher.cli prepare \
    --folder-id "LINK_PASTA_A" --folder-2-id "LINK_PASTA_B" \
    --date-1 2026-10-21 --date-2 2026-10-22 \
    --period-1 daily --period-2 daily \
    --source-name "CANAL A" --source-name-2 "CANAL B" \
    --youtube-account "@cortefinoshorts" --tiktok-account "cortefinoshorts" \
    --confirm-rights

  python -m publisher.cli browser-package
  python -m publisher.cli diagnostic-package
  python -m publisher.cli init-ledger --package publisher/state/browser_package.json
  python -m publisher.cli record-receipt --publication-key "RUN:01:youtube" --observed-account "@cortefinoshorts" --receipt-state SCHEDULED --remote-reference "REFERÊNCIA_DO_STUDIO"
  python -m publisher.cli reconcile
  python -m publisher.cli report
  python -m publisher.cli youtube --dry-run
  python -m publisher.cli tiktok --dry-run

## Proteções operacionais

- duas pastas obrigatórias e isoladas;
- cinco slots únicos por data;
- timestamps locais convertidos e revisados antes da postagem;
- Account Identity Guard: cada pacote carrega a conta esperada e o receipt bloqueia identidade divergente;
- revisão visual antes de confirmar cada agendamento;
- manifesto imutável e revisão de cada item no Studio antes da confirmação;
- estado remoto ambíguo exige reconciliação antes de qualquer retry;
- Creator e Publisher continuam separados.

