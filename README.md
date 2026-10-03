# Corte Fino Engine

Motor de produção para preparar até cinco cortes verticais por rodada, com transcrição local, seleção editorial, renderização em 9:16 e entrega organizada no Google Drive.

## O que ele faz

- roda diariamente no GitHub Actions;
- aceita um link manual pelo botão **Run workflow**;
- processa uma fonte autorizada colocada na pasta de entrada do Google Drive;
- aceita link manual pelo **Run workflow**, desde que a autorização seja confirmada;
- baixa a fonte indicada;
- transcreve em português com `faster-whisper`;
- seleciona até cinco trechos independentes, priorizando gancho, tensão, payoff e clareza;
- renderiza MP4 1080x1920 com legendas e marca discreta Corte Fino;
- entrega os arquivos em pastas separadas do Google Drive para YouTube Shorts, TikTok, textos e relatórios;
- mantém a publicação manual, sem publicar automaticamente.

## Importante

Use somente vídeos próprios, autorizados ou licenciados para cortes. A ferramenta não transforma uma cópia sem autorização em conteúdo permitido, e a atribuição da fonte não substitui permissão.

Use somente vídeos próprios, autorizados ou licenciados. Estar público no YouTube não significa que o material está liberado para cortes.

A pasta de entrada do Drive funciona como fila de fontes autorizadas: coloque nela somente arquivos cuja autorização/licença você confirmou.

## Como instalar pelo celular

1. Crie um repositório novo no GitHub chamado `corte-fino-engine`.
2. Deixe o repositório privado para preservar o código e os arquivos de configuração.
3. Envie todos os arquivos desta pasta mantendo a estrutura, especialmente `.github/workflows/corte-fino.yml`.
4. Abra a aba **Actions**, escolha **Corte Fino Diário** e toque em **Run workflow**.
5. Para usar um link manual, informe `source_url` e confirme `rights_confirmed` somente se a autorização/licença estiver válida.
6. Ao terminar, abra a pasta criada no Google Drive e revise os arquivos antes de publicar.

## Execução automática

O workflow está configurado para aproximadamente 19h15 no horário de Brasília, usando 22h15 UTC. O GitHub pode atrasar tarefas agendadas em períodos de alta demanda.

## Estados da rodada

- `NO_SOURCE`: nenhuma fonte nova na entrada;
- `EDITORIAL_EMPTY`: fonte processada, mas nenhum trecho atingiu a nota mínima;
- `READY_FOR_REVIEW`: cortes renderizados e aprovados na revisão técnica;
- `RIGHTS_PENDING`: direitos não confirmados;
- `TECHNICAL_FAILURE`: falha técnica real.

Uma rodada `EDITORIAL_EMPTY` não move a fonte para `Processados`.

## Limitações

- seleção de momentos baseada em transcrição e heurísticas editoriais, não em análise visual avançada;
- processamento mais lento em vídeos longos;
- o GitHub Actions não é armazenamento permanente;
- publicação no YouTube e TikTok ainda é manual;
- a seleção editorial é heurística e não promete viralização;
- a publicação no YouTube e TikTok permanece manual.
