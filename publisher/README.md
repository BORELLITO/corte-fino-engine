# Corte Fino Publisher 1.1

Módulo separado do gerador de cortes. Lê os 5 MP4 prontos no Google Drive, transcreve localmente com `faster-whisper`, cria copy completa para TikTok/YouTube, ranqueia os cortes e agenda os Shorts pela YouTube Data API.

## Entrada

Pasta: `15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da`

Contrato: exatamente 5 MP4 identificáveis como 01, 02, 03, 04 e 05. O Publisher não cria, recorta, reprocessa nem altera o motor que gera os cinco cortes diários.

## Copy completa

- Título em CAIXA ALTA, baseado na fala mais forte do trecho.
- Legenda com apelo emocional, contexto humano, pergunta de conversa e hashtags.
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

- `` — credencial OAuth do Google.
- `PUBLISHER_GOOGLE_CLIENT_ID` — credencial OAuth do Google.
- `PUBLISHER_GOOGLE_CLIENT_SECRET` — refresh token do Drive.
- `PUBLISHER_GOOGLE_REFRESH_TOKEN` — refresh token do canal Corte Fino com escopo `https://www.googleapis.com/auth/youtube.upload`.
- `PUBLISHER_ENABLED=1` — só depois dos testes, para ligar a execução diária.

## TikTok

O Publisher gera automaticamente ordem, horário e legenda, mas não faz Direct Post nesta versão. O pacote fica pronto para TikTok Studio ou para futura integração oficial aprovada.

## Comandos

```
python -m publisher.cli prepare
python -m publisher.cli report
python -m publisher.cli youtube --dry-run
python -m publisher.cli youtube
```

## Guards

- exatamente 5 vídeos e sequência 01..05;
- transcrição local;
- sem Metricool;
- copy completa com limites de caracteres/bytes;
- anti-duplicidade via Drive;
- publicação automática desativada até `PUBLISHER_ENABLED=1`.
