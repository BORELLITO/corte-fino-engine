# Corte Fino Publisher 1.8

Módulo separado do gerador de cortes. Lê os 5 MP4 prontos no Google Drive, transcreve localmente com `faster-whisper`, cria copy completa para TikTok/YouTube, ranqueia os cortes e agenda os Shorts pela YouTube Data API.

## Entrada

Pasta: o link ou ID exato informado manualmente pelo usuário no campo
`drive_folder` do workflow.

O campo `drive_folder` é obrigatório e aceita diretamente o link compartilhado
da pasta. O Publisher extrai o ID, valida a pasta e só então inicia a preparação.
O link é uma fronteira rígida: somente os arquivos diretamente dentro da pasta
indicada são considerados. O Publisher nunca procura subpastas, lotes anteriores,
pastas vizinhas ou outro conteúdo.

Contrato: exatamente 5 MP4 identificáveis como 01, 02, 03, 04 e 05. O Publisher não cria, recorta, reprocessa nem altera o Motor 1 que gera os cinco cortes.

## Copy completa

- Copy Editorial 2.0: cada corte recebe uma copy individual baseada no próprio transcript, com gancho, evidência textual, CTA contextual e hashtags derivadas do conteúdo.
- Título em CAIXA ALTA e sem pontuação ou travessão, baseado na fala mais forte do trecho, com fallback editorial apenas quando a fala é curta demais.
- Legenda com apelo emocional, contexto humano, CTA específico por tema, crédito natural e hashtags.
- O QA bloqueia títulos com pontuação e impede que o motor invente fonte ou episódio não confirmados.
- Hashtags de distribuição são relacionadas ao assunto; `#CorteFino` e marcadores genéricos de plataforma não são adicionados automaticamente.
- Descrição do YouTube com a mesma linha editorial, CTA e bloco de hashtags.
- Tags do YouTube também são enviadas no campo nativo `snippet.tags[]`, além das hashtags na descrição.
- O texto é normalizado para respeitar 100 caracteres no título, 5.000 bytes UTF-8 na descrição e 500 caracteres nas tags.
- Correções ortográficas seguras são aplicadas antes da copy; tokens de transcrição conhecidos como suspeitos reprovam a rodada. Baixa confiança isolada do ASR vira alerta de revisão, sem bloquear palavras comuns automaticamente.
- O QA bloqueia título truncado, hashtag de plataforma incorreta, espaçamento inválido, frases genéricas antigas e erros ASR não resolvidos antes de qualquer publicação.
- A copy nunca afirma um fato que não esteja sustentado pelo transcript: evidências são trechos literais do corte; perguntas editoriais permanecem perguntas.

## Slots editoriais — America/Sao_Paulo

- YouTube Shorts: 10h, 12h, 15h, 17h e 19h (usados para agendamento pela API).
- TikTok: 10h, 12h, 15h, 17h e 19h (mesma grade editorial do manifesto).

Os cortes mais fortes recebem os slots prioritários de cada rede. O YouTube é agendado
diretamente pela API. O TikTok é publicado pelo workflow automático de hora em hora,
que lê o manifesto persistido e envia somente o corte cujo horário local já venceu.

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
- Os secrets `GOOGLE_*` antigos permanecem exclusivos do Motor 1 e não devem ser alterados.
- Não existe `PUBLISHER_ENABLED`: o Publisher só roda por acionamento manual com link de pasta.
- `PUBLISHER_RIGHTS_AUTHORIZED=1` — opcional; confirmação padrão para lotes sem confirmação específica. Não use como substituto da revisão individual da fonte.
- `PUBLISHER_RIGHTS_STATUS` — descrição da autorização registrada no manifesto.

## TikTok

Fluxo operacional oficial:

1. O vídeo é colocado na pasta de entrada do gerador.
2. O workflow **Corte Fino Motor 1 — Gerar 5 Cortes** seleciona o vídeo, cria exatamente cinco cortes e envia os cinco MP4 para uma única pasta de lote no Drive.
3. O Motor 1 encerra após entregar os cinco MP4; ele não aciona o Publisher.
4. Você copia o link exato da pasta com os cinco MP4.
5. O workflow **Corte Fino Motor 2 — Publicar 5 Cortes** é iniciado manualmente com esse link obrigatório.
6. O Publisher prepara um manifesto v5, cria as copies e executa YouTube/TikTok conforme o modo escolhido, usando os mesmos cinco arquivos e marcadores anti-duplicidade no Drive.

O Publisher gera automaticamente ordem editorial, legenda e hashtags para cinco vídeos. A preparação do lote continua manual e exige o link exato da pasta. Depois que o manifesto é preparado, o modo `youtube` agenda os cinco Shorts pela API e o workflow `Corte Fino Motor 2 — TikTok Agendado` executa `--due-only` de hora em hora. Os campos opcionais `source_name` e `source_episode` alimentam os créditos sem permitir invenções. Cada arquivo é marcado no Drive para impedir duplicidade.

A publicação do TikTok é direta pela API oficial e não depende de Metricool nem do limite mensal de uma ferramenta intermediária. O agendador possui também `workflow_dispatch` para recuperação manual: se o cron atrasar ou um envio ficar pendente, abra **Actions → Corte Fino Motor 2 — TikTok Agendado → Run workflow**. O manifesto persistido continua sendo a única fonte do lote e a marcação no Drive impede duplicações.

Secrets exclusivos do Publisher:

- `PUBLISHER_TIKTOK_CLIENT_KEY` — Client key do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_CLIENT_SECRET` — Client secret do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_REFRESH_TOKEN` — refresh token obtido após autorizar a conta TikTok de publicação.
- `PUBLISHER_TIKTOK_EXPECTED_USERNAME` — opcional; @handle esperado para bloquear publicação na conta errada.
- `PUBLISHER_TIKTOK_PRIVACY_LEVEL` — opcional; padrão `PUBLIC_TO_EVERYONE`, sempre validado contra as opções devolvidas pela conta.

O modo `tiktok --dry-run` não acessa a API e valida as cinco copies. O modo `tiktok --allow-immediate` é usado somente quando o usuário escolhe explicitamente publicar pelo workflow manual. Depois do `init`, o `publish_id` é gravado imediatamente no Drive; novas execuções consultam esse ID antes de criar outro post. Chamadas da API têm retry com backoff para erros transitórios/limites (429 e 5xx), uploads de chunks têm retry e estados ainda processando não são tratados como concluídos. A produção também exige confirmação de direitos no manifesto; o Sandbox privado continua disponível para testes controlados. A publicação real exige `video.publish`, autorização da conta TikTok e aprovação/auditoria do app para sair das limitações de teste da plataforma.
Para o teste real controlado do Sandbox pelo GitHub Actions, use `mode=tiktok-now` e `tiktok_env=sandbox`. Esse modo prepara o lote e envia os cinco vídeos imediatamente apenas para a conta Sandbox configurada; ele é bloqueado quando o ambiente escolhido é Produção. Em Produção, use o modo manual `tiktok` quando quiser enviar os cinco vídeos.



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
python -m publisher.cli tiktok --allow-immediate  # envio imediato explícito
python -m publisher.cli tiktok --due-only         # modo legado, no máximo um vencido
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
- Publisher independente do Motor 1; preparação manual por pasta exata e agendamento TikTok separado, sem descoberta automática de lote;
- manifesto v5 com `run_id`, fonte imutável, direitos confirmados, versão da HUD, créditos editoriais e lote exato do Drive;
- estado persistido no Git sem a transcrição integral dos cortes;
- reconciliação de TikTok pendente mesmo depois da virada do dia;
- pré-flight de todos os horários do YouTube antes do primeiro upload;
- nenhuma subpasta ou arquivo extra é aceito dentro da pasta exata do lote.
