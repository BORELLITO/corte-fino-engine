# Corte Fino Publisher 1.2

Módulo separado do gerador de cortes. Lê os 5 MP4 prontos no Google Drive, transcreve localmente com `faster-whisper`, cria copy completa para TikTok/YouTube, ranqueia os cortes e agenda os Shorts pela YouTube Data API.

## Entrada

Pasta: `15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da`

Contrato: exatamente 5 MP4 identificáveis como 01, 02, 03, 04 e 05. O Publisher não cria, recorta, reprocessa nem altera o motor que gera os cinco cortes diários.

## Copy completa

- Título em CAIXA ALTA, baseado na fala mais forte do trecho, com fallback editorial apenas quando a fala é curta demais.
- Legenda com apelo emocional, contexto humano, pergunta de conversa e hashtags.
- Hashtags próprias por plataforma: TikTok não recebe `#Shorts` e YouTube não recebe `#TikTok`.
- Descrição do YouTube com a mesma linha editorial, CTA e bloco de hashtags.
- Tags do YouTube também são enviadas no campo nativo `snippet.tags[]`, além das hashtags na descrição.
- O texto é normalizado para respeitar 100 caracteres no título, 5.000 bytes UTF-8 na descrição e 500 caracteres nas tags.

## Horários base — America/Sao_Paulo

- YouTube Shorts: 10h, 12h, 14h, 16h e 18h.
- TikTok: 10h, 12h, 16h, 18h e 20h.

Os cortes mais fortes recebem os slots prioritários de cada rede.

## YouTube

Os cinco vídeos são enviados como `private` com `status.publishAt`, para publicação programada. Também são enviados idioma padrão `pt-BR`, categoria `24`, `selfDeclaredMadeForKids=false` e `notifySubscribers=false`. O Drive recebe `appProperties` com o ID publicado para evitar duplicidade.

O campo `containsSyntheticMedia` fica em `false` para os cortes editoriais originais do Corte Fino, sem cenas realistas geradas ou alteradas por IA. Se um vídeo futuro tiver alteração sintética realista, essa declaração deve ser revisada antes do upload.

Secrets:

- `PUBLISHER_GOOGLE_CLIENT_ID` — credencial OAuth exclusiva do Publisher.
- `PUBLISHER_GOOGLE_CLIENT_SECRET` — segredo OAuth exclusivo do Publisher.
- `PUBLISHER_GOOGLE_REFRESH_TOKEN` — refresh token do Drive usado pelo Publisher.
- `PUBLISHER_YOUTUBE_REFRESH_TOKEN` — refresh token da conta `extremeheroesshorts@gmail.com`, com escopo `https://www.googleapis.com/auth/youtube.upload`.
- O token do YouTube é obrigatório e não cai silenciosamente no token do Drive.
- Os secrets `GOOGLE_*` antigos permanecem exclusivos do motor diário e não devem ser alterados.
- `PUBLISHER_ENABLED=1` — só depois dos testes, para ligar a execução diária.

## TikTok

O Publisher gera automaticamente ordem, horário, legenda e hashtags para cinco vídeos. Como o Direct Post do TikTok envia o vídeo imediatamente, o workflow roda nas cinco janelas locais (10h, 12h, 16h, 18h e 20h) e publica no máximo um corte por janela. Cada arquivo é marcado no Drive para impedir duplicidade.

Secrets exclusivos do Publisher:

- `PUBLISHER_TIKTOK_CLIENT_KEY` — Client key do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_CLIENT_SECRET` — Client secret do app Corte Fino Publisher.
- `PUBLISHER_TIKTOK_REFRESH_TOKEN` — refresh token obtido após autorizar a conta TikTok de publicação.
- `PUBLISHER_TIKTOK_EXPECTED_USERNAME` — opcional; @handle esperado para bloquear publicação na conta errada.
- `PUBLISHER_TIKTOK_PRIVACY_LEVEL` — opcional; padrão `PUBLIC_TO_EVERYONE`, sempre validado contra as opções devolvidas pela conta.

O modo `tiktok --dry-run` não acessa a API e valida os cinco horários e captions. `tiktok --due-only` publica somente o próximo corte vencido, evitando enviar os cinco de uma vez. Depois do `init`, o `publish_id` é gravado imediatamente no Drive; novas execuções consultam esse ID antes de criar outro post. Uploads de chunks têm retry e estados ainda processando não são tratados como concluídos. A publicação real exige `video.publish`, autorização da conta TikTok e aprovação/auditoria do app para sair das limitações de teste da plataforma.

Antes de ativar a publicação, rode `python -m publisher.cli verify-tiktok`. Esse comando renova o OAuth, consulta o perfil autorizado e não publica nem envia vídeo. Se `PUBLISHER_TIKTOK_EXPECTED_USERNAME` estiver configurado, a execução falha quando o token pertence a outro perfil.

## Comandos

```
python -m publisher.cli prepare
python -m publisher.cli report
python -m publisher.cli youtube --dry-run
python -m publisher.cli youtube
python -m publisher.cli tiktok --dry-run
python -m publisher.cli tiktok --due-only
python -m publisher.cli tiktok
python -m publisher.cli verify-tiktok
python -m publisher.cli verify-google
python -m publisher.cli prepare --target-date 2026-10-07
```

## Guards

- exatamente 5 vídeos e sequência 01..05;
- MP4 validado com `ffprobe`: 1080x1920, H.264, AAC e duração positiva;
- transcrição local;
- sem Metricool;
- copy completa com limites de caracteres/bytes;
- anti-duplicidade via Drive;
- estados TikTok pendente, processando, concluído e falho persistidos no Drive;
- preflight read-only separado para Google e TikTok;
- publicação automática desativada até `PUBLISHER_ENABLED=1`.
