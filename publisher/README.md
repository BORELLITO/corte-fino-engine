# Corte Fino Publisher 2.6 — Control + Learning + Studio Metrics

O Publisher é o Motor 2 do Corte Fino. Ele recebe duas pastas exatas do Google Drive, cada uma com cinco MP4s prontos pelo Creator, e distribui os dez cortes em dois dias: cinco publicações por dia. A versão 2.5 mantém o Distribution Guard, Account Identity Guard, Publication Receipt e reconciliação, e acrescenta Performance Receipt + feedback conservador para o Creator.

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


## Performance Receipt → Creator

O Publisher pode registrar snapshots de performance em `1h`, `6h`, `24h` e `72h`. Métricas só são aceitas depois que o Publication Receipt confirma o post como `PUBLIC`/`VERIFIED`.

Para aprendizado do Creator:

- snapshots de 1h/6h são observacionais e nunca treinam o ranking;
- 24h/72h podem ser elegíveis;
- YouTube exige sinal de distribuição (`shown_in_feed`) de pelo menos 100;
- restrições, distribuição insuficiente e posts não verificados são excluídos;
- o snapshot maduro mais recente tem autoridade: uma restrição em 72h cancela uma elegibilidade anterior de 24h;
- o histórico é cumulativo entre rodadas e deduplicado por `publication_key`;
- somente após 20 Shorts elegíveis o perfil pode ficar `READY`;
- cada trigger exige pelo menos 5 amostras;
- o ajuste no score do Creator fica limitado a ±2 pontos e atua como desempate, sem substituir os gates editoriais/narrativos.

O Creator grava seu recibo compacto diretamente em `appProperties` do MP4. O Publisher lê esse recibo e consegue relacionar performance com trigger, score, duração, origem e nicho. O histórico e o arquivo `_corte_fino_creator_feedback.json` ficam no diretório raiz privado do Creator no Google Drive, nunca dentro da pasta rígida dos cinco MP4.

A captura de métricas privadas do YouTube/TikTok Studio não é simulada pelo código: Work/operador precisa observar os dados reais e registrá-los no ledger.

Comandos principais:

  python -m publisher.cli init-performance
  python -m publisher.cli record-performance --publication-key "RUN:01:youtube" --horizon 24h --metrics-json '{"shown_in_feed":1200,"views":700,"viewed_rate":64,"avg_percentage_viewed":82}'
  python -m publisher.cli creator-feedback
  python -m publisher.cli publish-feedback

## Studio Metrics Handoff

O estado necessário para medir 24h/72h não depende mais do artefato temporário do GitHub Actions. O Publisher mantém um cofre privado no diretório raiz dos lotes:

`_corte_fino_publisher_state/`

Cada execução persiste um `run-<run_id>.json` sanitizado, sem transcrições, contendo manifesto operacional, Publication Receipt e Performance Ledger.

O workflow `Corte Fino Motor 2 — Performance` possui três modos:

1. `collect-package`: restaura a execução pelo `run_id`, seleciona somente posts realmente PUBLIC/VERIFIED cujo horizonte já venceu e salva o pacote de coleta no Drive;
2. Work/Cloud Browser abre o YouTube Studio/TikTok Studio, confirma a conta visível, lê apenas os valores mostrados e salva um `metrics-result-<run_id>-<horizon>.json` ao lado do pacote;
3. `apply-result`: restaura o pacote original, valida conta, plataforma, chaves e nomes de métricas, grava os snapshots e persiste novamente o estado;
4. em 24h/72h, o workflow atualiza automaticamente o histórico de aprendizado do Creator.

O relógio de 1h/6h/24h/72h parte do primeiro receipt real `PUBLIC/VERIFIED`, não apenas do horário planejado. Campo indisponível no Studio deve ser omitido; nunca preencher com zero por conveniência. Um snapshot já gravado para o mesmo horizonte é imutável e não pode ser sobrescrito.

O YouTube Studio é a fonte para sinais específicos de Shorts como `Mostrado no feed` e `Visualizaram x deslizaram`. A coleta continua dependente de sessão autenticada no Studio; o código não simula essas métricas.

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

