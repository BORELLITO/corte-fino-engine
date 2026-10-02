# Corte Fino Engine — versão gratuita

Motor experimental para gerar até quatro cortes verticais por dia usando GitHub Actions, `yt-dlp`, Whisper local e FFmpeg.

## O que ele faz

- roda diariamente no GitHub Actions;
- aceita um link manual pelo botão **Run workflow**;
- se nenhum link for informado, tenta descobrir fontes recentes por busca pública;
- baixa a fonte indicada;
- transcreve em português com `faster-whisper`;
- seleciona até quatro janelas com maior potencial editorial;
- renderiza MP4 1080x1920 com legendas e marca discreta Corte Fino;
- entrega os arquivos como artefato baixável do GitHub Actions.

## Importante

Use somente vídeos próprios, autorizados ou licenciados para cortes. A ferramenta não transforma uma cópia sem autorização em conteúdo permitido, e a atribuição da fonte não substitui permissão.

Os arquivos são temporários no GitHub Actions. Baixe o artefato ao terminar a execução; para armazenamento permanente, a próxima evolução será enviar o ZIP para o Google Drive.

## Como instalar pelo celular

1. Crie um repositório novo no GitHub chamado `corte-fino-engine`.
2. Deixe o repositório privado para preservar o código e os arquivos de configuração.
3. Envie todos os arquivos desta pasta mantendo a estrutura, especialmente `.github/workflows/corte-fino.yml`.
4. Abra a aba **Actions**, escolha **Corte Fino Diário** e toque em **Run workflow**.
5. Para um teste controlado, informe no campo `source_url` o link de um vídeo autorizado.
6. Ao terminar, abra a execução e baixe o artefato `corte-fino-resultados`.

## Execução automática

O workflow está configurado para aproximadamente 19h15 no horário de Brasília, usando 22h15 UTC. O GitHub pode atrasar tarefas agendadas em períodos de alta demanda.

## Limitações da versão gratuita

- seleção de momentos baseada em transcrição e heurísticas editoriais, não em análise visual avançada;
- processamento mais lento em vídeos longos;
- o GitHub Actions não é armazenamento permanente;
- publicação no YouTube e TikTok ainda é manual;
- a busca automática pode encontrar fontes sem confirmação de direitos, que devem ser revisadas antes da postagem.
