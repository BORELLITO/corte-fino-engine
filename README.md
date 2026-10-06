# Corte Fino Engine

Motor de produção para preparar exatamente cinco cortes verticais por rodada aprovada, com transcrição local, seleção editorial, renderização em 9:16 e entrega organizada no Google Drive.

## O que ele faz

- roda diariamente no GitHub Actions;
- aceita um link manual pelo botão Run workflow;
- processa qualquer vídeo colocado na pasta de entrada do Google Drive;
- aceita qualquer link manual pelo Run workflow;
- baixa a fonte indicada;
- transcreve em português com faster-whisper;
- seleciona exatamente cinco trechos independentes, priorizando gancho, tensão, payoff e clareza;
- renderiza MP4 1080x1920 com legendas e marca discreta Corte Fino;
- entrega os arquivos em pastas separadas do Google Drive para YouTube Shorts, TikTok, textos e relatórios;
- mantém a publicação manual, sem publicar automaticamente.

## Importante

O workflow não bloqueia vídeos por status de licença: ele recebe o arquivo, faz a edição e entrega os materiais. A responsabilidade por autorização, licenças e publicação é do usuário. O relatório mantém o status como REVISÃO MANUAL para facilitar a conferência, e a ferramenta nunca publica automaticamente.

A pasta de entrada do Drive funciona como fila de processamento: coloque nela os vídeos que deseja cortar. O arquivo mais recentemente alterado é processado primeiro e depois movido para Processados.

## Como instalar pelo celular

1. Crie um repositório novo no GitHub chamado corte-fino-engine.
2. Deixe o repositório privado para preservar o código e os arquivos de configuração.
3. Envie todos os arquivos desta pasta mantendo a estrutura, especialmente .github/workflows/corte-fino.yml.
4. Abra a aba Actions, escolha Corte Fino Diário e toque em Run workflow.
5. Para usar um link manual, informe source_url. rights_confirmed é opcional e apenas registra a revisão manual; não bloqueia o processamento.
6. Ao terminar, abra a pasta criada no Google Drive e revise os arquivos antes de publicar.

## Execução automática

O workflow está configurado para aproximadamente 19h15 no horário de Brasília, usando 22h15 UTC. O GitHub pode atrasar tarefas agendadas em períodos de alta demanda.

## Estados da rodada

- NO_SOURCE: nenhum vídeo novo na entrada;
- EDITORIAL_EMPTY: nenhum acontecimento suficiente foi encontrado;
- TOP_FIVE_INCOMPLETE: não foi possível aprovar os cinco cortes fechados sem substituição;
- READY_FOR_HUMAN_REVIEW: cortes renderizados, legendas verificadas e QA final aprovado; a postagem continua manual;
- CAPTION_REVIEW_REQUIRED: a fala tem baixa confiança ou risco ortográfico e não foi inventada/corrigida automaticamente;
- REVISÃO MANUAL: direitos e licenças ficam sob responsabilidade do usuário;
- TECHNICAL_FAILURE: falha técnica real.

Uma fonte só é movida para Processados depois de cortes válidos, QA final, upload confirmado e manifesto da rodada. Se o gate falhar, ela permanece disponível para nova tentativa.

## Limitações

- seleção de momentos baseada em transcrição e heurísticas editoriais, não em análise visual avançada;
- processamento mais lento em vídeos longos;
- o GitHub Actions não é armazenamento permanente;
- publicação no YouTube e TikTok ainda é manual;
- a seleção editorial é heurística e não promete viralização;
- a publicação no YouTube e TikTok permanece manual.


## Regras de qualidade incorporadas

- Um único MP4 canônico em 9:16, 1080x1920, atende Shorts e TikTok; o TikTok recebe apenas um atalho no Drive.
- A revisão de legendas combina sincronização, área segura, tokens de risco, confiança por palavra do Whisper e verificação de frequência em português quando disponível.
- O motor não “corrige” uma fala incerta: reprova a rodada do Top 5 e não usa o sexto colocado como substituto.
- Hashtags usam correspondência por palavra, evitando classificar “aviação” como inteligência artificial por conter “ia”.
- O relatório separa QA técnico de prontidão humana e preserva candidatos rejeitados para auditoria.


## Tratamento individual por vídeo

Antes da seleção, cada fonte recebe um perfil editorial próprio a partir do título, canal e transcrição integral. O relatório registra nicho provável, confiança, sinais dominantes, ritmo, densidade de perguntas/conflito e lentes recomendadas. A nota serve para ranquear candidatos; por padrão, não bloqueia o vídeo inteiro. Os bloqueios são objetivos: legenda suspeita, baixa confiança, repetição, falta de continuidade, falha de render ou QA final.


## Regra do Top 5 fechado

Cada rodada tenta entregar exatamente cinco cortes. Depois que os cinco candidatos são escolhidos, nenhum sexto candidato pode substituir um deles. Se um dos cinco falhar no gate de legenda ou no QA do arquivo, a rodada é marcada como `TOP_FIVE_INCOMPLETE`, não é enviada ao Drive e a fonte permanece disponível para nova tentativa.