# Corte Fino Publisher 1.0

Módulo separado do gerador de cortes. Lê os 5 MP4 prontos no Google Drive, transcreve localmente com `faster-whisper`, cria copy de TikTok/YouTube, ranqueia os cortes e agenda os Shorts diretamente pela YouTube Data API.

## Entrada

Pasta: `15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da`

Contrato: exatamente 5 MP4 identificáveis como 01, 02, 03, 04 e 05.

## Horários base — America/Sao_Paulo

- YouTube Shorts: 10h, 12h, 14h, 16h e 18h.
- TikTok: 10h, 12h, 16h, 18h e 20h.

Os cortes mais fortes recebem os slots prioritários de cada rede.

## YouTube

Os cinco vídeos são enviados como `private` com `status.publishAt`, o mecanismo oficial de agendamento. O Drive recebe `appProperties` com o ID publicado para evitar duplicidade.

Secrets:
- `GOOGLE_CLIENT_ID` — já existente.
- `GOOGLE_CLIENT_SECRET` — já existente.
- `GOOGLE_REFRESH_TOKEN` — já existente para Drive.
- `YOUTUBE_REFRESH_TOKEN` — OAuth do canal Corte Fino com escopo `https://www.googleapis.com/auth/youtube.upload`.
- `PUBLISHER_ENABLED=1` — só depois dos testes, para ligar a execução diária.

## TikTok

O Publisher gera automaticamente ordem, horário e legenda, mas não faz Direct Post nesta versão. As diretrizes oficiais do Content Posting API não aceitam um cliente criado somente como utilitário interno para publicar nas contas administradas pelo próprio usuário/equipe, e clientes não auditados têm restrições de visibilidade. Não incluímos automação que contorne essas regras.

O pacote fica pronto para TikTok Studio ou para futura integração oficial aprovada.

## Comandos

```bash
python -m publisher.cli prepare
python -m publisher.cli report
python -m publisher.cli youtube --dry-run
python -m publisher.cli youtube
```

## Guards

- exatamente 5 vídeos e sequência 01..05;
- transcrição local, sem serviço pago;
- sem Metricool;
- título do YouTube limitado;
- anti-duplicidade via Drive;
- publicação automática desativada até `PUBLISHER_ENABLED=1`.
