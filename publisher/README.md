# Corte Fino Publisher 1.5

Módulo separado do gerador de cortes. Lê os 5 MP4 prontos no Google Drive, transcreve localmente com `faster-whisper`, cria copy completa para TikTok/YouTube, ranqueia os cortes e agenda os Shorts pela YouTube Data API.

## Entrada

Pasta: o lote exato informado pelo usuário ou registrado pelo gerador em
`publisher/state/latest_batch.json`.

Na ativação manual, o campo `drive_folder` aceita diretamente o link compartilhado
da pasta. O Publisher extrai o ID, valida a pasta e só então inicia a preparação.
O link é uma fronteira rígida: somente os arquivos diretamente dentro da pasta
indicada são considerados. O Publisher nunca procura subpastas, lotes anteriores,
pastas vizinhas ou outro conteúdo. Quando a execução é agendada, o Publisher usa
somente o último lote exato registrado pelo gerador; nunca redescobre uma pasta
por data, nome ou proximidade.

Contrato: exatamente 5 MP4 identificáveis como 01, 02, 03, 04 e 05. O Publisher não cria, recorta, reprocessa nem altera o motor que gera os cinco cortes diários.

## Copy completa

- Copy Editorial 2.0: cada corte recebe uma copy individual baseada no próprio transcript, com gancho, evidência textual, CTA contextual e hashtags derivadas do conteúdo.
- Título em CAIXA ALTA, baseado na fala mais forte do trecho, com fallback editorial apenas quando a fala é curta demais.
- Legenda com apelo emocional, contexto humano, pergunta de conversa e hashtags.
- Hashtags próprias por plataforma: TikTok não recebe `#Shorts` e YouTube não recebe `#TikTok`.
- Descrição do YouTube com a mesma linha editorial, CTA e bloco de hashtags.
- Tags do YouTube também são enviadas no campo nativo `snippet.tags[]`, além das hashtags na descrição.
- O texto é normalizado para respeitar 100 caracteres no título, 5.000 bytes UTF-8 na descrição e 500 caracteres nas tags.
- Correções ortográficas seguras são aplicadas antes da copy; tokens de transcrição conhecidos como suspeitos e baixa confiança do ASR reprovam a rodada em vez de serem inventados.
- O QA bloqueia título truncado, hashtag de plataforma incorreta, espaçamento inválido, frases genéricas antigas e erros ASR não resolvidos antes de qualquer publicação.
- A copy nunca afirma um fato que não esteja sustentado pelo transcript: evidências são trechos literais do corte; perguntas editoriais permanecem perguntas.

## Horários base — America/Sao_Paulo

- YouTube Shorts: 10h, 12h, 14h, 16h e 18h.
- TikTok: 10h, 12h, 16h, 18h e 20h.

Os cortes mais fortes recebem os slots prioritários de cada rede.

## YouTube

Os cinco vídeos são enviados como `private` com `status.publishAt`, para publicação programada. Também são enviados idioma padrão `pt-BR`, categoria `24`, `selfDeclaredMadeForKids=false` e `notifySubscribers=false`. O Drive recebe `appProperties` com o ID publicado para evitar duplicidade.

O campo `containsSyntheticMedia` fica em `false` para os cortes editoriais originais do Corte Fino, sem cenas realistas geradas ou alteradas por IA. Se um vídeo futuro tiver alteração sintética realista, essa declaração deve ser revisada antes do upload.

Depois do `videos.insert`, o Publisher consulta o processamento do vídeo. Só grava `SCHEDULED` quando o YouTube confirma `succeeded`; estados ainda processando permanecem reconciliáveis e não geram um segundo upload.

Secrets:

- `PUBLISHER_GOOGLE_CLIENT_ID` — credencial OAuth exclusiva do Publisher.
- `PUBLISHER_GOOGLE_CLIENT_SECRET` — segredo OAuth exclusivo do Publisher.
- `PUBLISHER_GOOGLE_REFRESH_TOKEN` — refresh token do Drive usado pelo Publisher.
- `PUBLISHER_YOUTUBE_REFRESH_TOKEN` — refresh token da conta `extremeheroesshorts@gmail.com`, com escopo `https://www.googleapis.com/auth/youtube.upload`.
- O token do YouTube é obrigatório e não cai silenciosamente no token do Drive.
- Os secrets `GOOGLE_*` antigos permanecem exclusivos do motor diário e não devem ser alterados.
- `PUBLISHER_ENABLED=1` — só depois dos testes, para ligar a execução diária.

## TikTok

Fluxo operacional oficial:

1. O vídeo é colocado na pasta de entrada do gerador.
2. O workflow **Corte Fino Diário** seleciona o vídeo, cria exatamente cinco cortes e envia os cinco MP4 para uma única pasta de lote no Drive.
3. O gerador registra automaticamente o link e o ID dessa pasta em `publisher/state/latest_batch.json`.
4. O workflow **Corte Fino Publisher** usa esse lote registrado automaticamente. O campo `drive_folder` só é necessário quando você quiser substituir manualmente o lote.
5. O Publisher prepara um manifesto v3, cria as copies e publica YouTube/TikTok de forma independente, usando os mesmos cinco arquivos e marcadores anti-duplicidade no Drive.

O Publisher gera automaticamente ordem, horário, legenda e hashtags para cinco vídeos. Como o Direct Post do TikTok envia o vídeo imediatamente, o workflow roda nas cinco janelas locais (10h, 12h, 16h, 18h e 20h) e publica no máximo um corte por janela. Cada arquivo é marcado no Drive para impedir duplicidade.

Secrets exclusivos do Publisher:

- `PUBLISHER_TIKTOK_CLIENT_KEY` — Client key do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_CLIENT_SECRET` — Client secret do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_REFRESH_TOKEN` — refresh token obtido após autorizar a conta TikTok de publicação.
- `PUBLISHER_TIKTOK_EXPECTED_USERNAME` — opcional; @handle esperado para bloquear publicação na conta errada.
- `PUBLISHER_TIKTOK_PRIVACY_LEVEL` — opcional; padrão `PUBLIC_TO_EVERYONE`, sempre validado contra as opções devolvidas pela conta.

O modo `tiktok --dry-run` não acessa a API e valida os cinco horários e captions. `tiktok --due-only` publica somente o próximo corte vencido, evitando enviar os cinco de uma vez. A publicação imediata de todos os cortes fica bloqueada por padrão e exige confirmação explícita. Depois do `init`, o `publish_id` é gravado imediatamente no Drive; novas execuções consultam esse ID antes de criar outro post. Uploads de chunks têm retry e estados ainda processando não são tratados como concluídos. A publicação real exige `video.publish`, autorização da conta TikTok e aprovação/auditoria do app para sair das limitações de teste da plataforma.
Para o teste real controlado do Sandbox pelo GitHub Actions, use `mode=tiktok-now` e `tiktok_env=sandbox`. Esse modo prepara o lote e envia os cinco vídeos imediatamente apenas para a conta Sandbox configurada; ele é bloqueado quando o ambiente escolhido é Produção. Em Produção, o modo normal continua usando `--due-only`, um vídeo por janela programada.



Antes de ativar a publicação, rode `python -m publisher.cli verify-tiktok`. Esse comando renova o OAuth, consulta o perfil autorizado e não publica nem envia vídeo. Se `PUBLISHER_TIKTOK_EXPECTED_USERNAME` estiver configurado, a execução falha quando o token pertence a outro perfil.

## Reconciliação e preflight

Antes do upload para o YouTube, o Publisher grava uma intenção pendente no Drive. Se o processo cair depois do upload e antes do marcador final, a próxima execução procura o vídeo recém-criado por título e janela de horário. Quando não consegue confirmar com segurança, bloqueia o reenvio para evitar duplicidade.

O comando `preflight` valida, sem publicar, os cinco arquivos do Drive, as credenciais Google e a conta TikTok autorizada:

```
python -m publisher.cli preflight
python -m publisher.cli preflight --folder-id "https://drive.google.com/drive/folders/ID_DA_PASTA"
```

Para consultar estados persistidos no Drive:

```
python -m publisher.cli report --remote
```

## Comandos

```
python -m publisher.cli prepare
python -m publisher.cli report
python -m publisher.cli youtube --dry-run
python -m publisher.cli youtube
python -m publisher.cli tiktok --dry-run
python -m publisher.cli tiktok --due-only
python -m publisher.cli tiktok
python -m publisher.cli tiktok --allow-immediate  # somente se o envio imediato for intencional
python -m publisher.cli verify-tiktok
python -m publisher.cli verify-google
python -m publisher.cli preflight
python -m publisher.cli report --remote
python -m publisher.cli prepare --target-date 2026-10-07
```

## Guards

- exatamente 5 vídeos MP4 diretos e sequência 01..05;
- checksum, tamanho, nome e pasta dos cinco arquivos revalidados antes de cada publicação;
- MP4 validado com `ffprobe`/`ffmpeg`: 1080x1920, H.264, AAC, 30 fps, yuv420p, áudio 48 kHz, decodificação integral e duração entre 45 e 90 segundos;
- transcrição local;
- sem Metricool;
- copy completa com limites de caracteres/bytes;
- QA editorial bloqueante para ortografia, truncamento e tokens ASR suspeitos;
- anti-duplicidade via Drive;
- intenção pendente e reconciliação do upload do YouTube;
- estados TikTok pendente, processando, concluído e falho persistidos no Drive;
- preflight read-only separado para Google e TikTok;
- publicação automática desativada até `PUBLISHER_ENABLED=1`;
- manifesto v3 com `run_id`, fonte imutável e lote exato do Drive.
