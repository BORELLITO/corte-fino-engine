# Corte Fino Engine

Motor de produção para preparar exatamente cinco cortes verticais por rodada aprovada, com transcrição local, seleção editorial fechada, renderização em 9:16 e entrega dos vídeos no Google Drive.

## Contrato de entrega

Cada rodada aprovada entrega exatamente cinco arquivos na mesma pasta da rodada:

- `NOME DA FONTE - 01.mp4` até `05.mp4`;

Os vídeos são MP4 H.264/AAC em 1080x1920, com áudio original, fundo desfocado, cores originais, HUD `CORTE / FINO` no canto superior direito e legendas sincronizadas na área segura.

Não são criados subdiretórios de plataforma, atalhos, ZIPs, relatórios, textos ou arquivos de QA dentro da pasta final. Relatórios e QA permanecem apenas como artefatos internos da execução. A publicação é feita pelo Publisher separado, usando exclusivamente o link exato do lote.

## O que ele faz

- processa o vídeo mais recentemente alterado na pasta de entrada do Google Drive;
- aceita uma fonte manual pelo botão Run workflow;
- transcreve em português com faster-whisper e timestamps por palavra;
- analisa cada fonte individualmente para adaptar a leitura editorial;
- pré-audita legendas e seleciona exatamente cinco candidatos publicáveis, sem substituir um candidato reprovado depois do fechamento por um sexto;
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
3. Execute o workflow `Corte Fino Diário`.
4. Revise a pasta da rodada e confirme autorização/licença antes de publicar.

A responsabilidade por autorização, licenças e publicação permanece com o usuário. A seleção editorial usa heurísticas e não promete viralização.

