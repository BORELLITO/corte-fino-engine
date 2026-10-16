# Corte Fino Engine

Motor de produção para preparar exatamente cinco cortes verticais por rodada aprovada, com transcrição local, seleção editorial fechada, renderização em 9:16 e entrega dos vídeos no Google Drive.

## Fluxo operacional em dois motores

- **Motor 1 — Gerar 5 Cortes:** lê o vídeo mais recente da pasta de entrada, gera exatamente cinco MP4 verticais e entrega os arquivos em uma única pasta de lote no Drive.
- **Motor 2 — Publicar 5 Cortes:** é acionado separadamente pelo usuário, recebe obrigatoriamente o link exato da pasta, valida os cinco arquivos, cria as copies, agenda o YouTube e publica o TikTok conforme o modo escolhido.
- Não existe handoff automático entre os motores: o Motor 1 termina depois da entrega e nunca inicia o Publisher.
- O TikTok Sandbox possui um modo de teste real controlado; a Produção permanece bloqueada até a autorização e aprovação necessárias.
- O workflow de troca de token do Sandbox só entrega refresh token em repositório privado; em repositório público, configure o secret manualmente.


## Contrato de entrega

Cada rodada aprovada entrega exatamente cinco arquivos na mesma pasta da rodada:

- `NOME DA FONTE - 01.mp4` até `05.mp4`;

Os vídeos são MP4 H.264/AAC em 1080x1920, com áudio original, fundo desfocado, cores originais, HUD `CORTE / FINO` no canto superior direito e legendas sincronizadas na área segura.

A duração é um gate obrigatório: cada corte precisa ter estritamente mais de 60 segundos. O alvo editorial é 68 segundos e o limite máximo configurado é 90 segundos. Candidatos e arquivos finais com 60 segundos ou menos são reprovados automaticamente.

A seleção narrativa também é obrigatória: o motor primeiro cria um mapa temporal da fonte, depois procura unidades de raciocínio com começo autônomo, contexto suficiente, desenvolvimento e conclusão real. O corte precisa ter pelo menos 45 palavras, não pode depender de uma fala anterior e não pode considerar silêncio ou fim da transcrição como prova de encerramento. A seleção rejeita trechos que começam no meio do raciocínio, atravessam uma mudança brusca de assunto sem transição ou terminam em palavras dependentes, como “de”, “que”, “para” ou “e”.

Não são criados subdiretórios de plataforma, atalhos, ZIPs, relatórios, textos ou arquivos de QA dentro da pasta final. Relatórios e QA permanecem apenas como artefatos internos da execução. A publicação é feita pelo Publisher separado, usando exclusivamente o link exato do lote.

## O que ele faz

- processa o vídeo mais recentemente alterado na pasta de entrada do Google Drive;
- aceita uma fonte manual pelo botão Run workflow;
- transcreve em português com faster-whisper e timestamps por palavra;
- analisa cada fonte individualmente para adaptar a leitura editorial;
- pré-audita duração, legendas e seleciona exatamente cinco candidatos publicáveis, sem substituir um candidato reprovado depois do fechamento por um sexto;
- bloqueia legenda suspeita, repetição, falta de continuidade, falha de render ou vídeo inválido;
- renderiza os cinco vídeos;
- faz upload idempotente e verificável na mesma pasta, podendo retomar uma rodada parcial;
- move a fonte para `Processados` somente depois de confirmar os cinco arquivos;
- nunca publica automaticamente.

## Estados da rodada

- `NO_SOURCE`: nenhum vídeo novo na entrada;
- `EDITORIAL_EMPTY`: nenhum acontecimento suficiente foi encontrado;
- `TOP_FIVE_INCOMPLETE`: não foi possível aprovar os cinco candidatos fechados;
- `READY_FOR_HUMAN_REVIEW`: cinco vídeos passaram pelos gates;
- `CAPTION_REVIEW_REQUIRED`: risco de transcrição/ortografia exige revisão;
- `TECHNICAL_FAILURE`: falha técnica real.

O alvo confortável de leitura é 18 caracteres por segundo; até 24 caracteres por segundo é o limite duro para fala acelerada e fica marcado para revisão humana. Se qualquer item do Top 5 fechado falhar depois da seleção, a rodada não é enviada ao Drive e a fonte permanece disponível para nova tentativa. Não há substituição silenciosa depois do fechamento.

## Como usar

1. Configure os secrets do Google Drive usados pelo workflow.
2. Coloque um vídeo autorizado na pasta de entrada ou informe `source_url` no Run workflow.
3. Execute o workflow `Corte Fino Motor 1 — Gerar 5 Cortes`.
4. Copie o link exato da pasta que contém os cinco cortes.
5. Execute manualmente o workflow `Corte Fino Motor 2 — Publicar 5 Cortes` e cole o link no campo `drive_folder`.
6. Faça o dry-run/preflight e só depois escolha a publicação.

Em uma execução local, coloque o MP4 em `work/source/`; o motor usa automaticamente o arquivo mais recentemente alterado, sem apagar a entrada antes do processamento.

A responsabilidade por autorização, licenças e publicação permanece com o usuário. A seleção editorial usa heurísticas e não promete viralização.
