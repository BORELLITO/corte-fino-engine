# VERBO NO CHÃO — E01 v2: legendas sincronizadas por ASR e 12 cenas de produção

**Data da validação:** 17/11/2026 (Brasil) / 18/11/2026 (GitHub UTC).  
**Estado:** `TIMED_CAPTIONS_PROVISIONAL_NOT_MASTER`. **NÃO PUBLICÁVEL**.

## Resultado físico real

O motor leu o **mesmo WAV** da nova versão E01, 70,425 segundos, SHA-256 `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`, e não gerou uma terceira voz.

O ASR real de dois modelos estava preservado no run https://github.com/BORELLITO/corte-fino-engine/actions/runs/44204868327, SHA-256 JSON `377063ff846ddef641b9288656ea867ede965a73991abe6b4c203dec3a919a8b`.

O roteiro canônico E01 v2, **SHA-256** `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6`, foi usado como texto da legenda. Assim se evita publicar transcrições incorretas de ASR como se fossem palavras aprovadas.

- **182/182 palavras** canônicas preservadas em **28 legendas**.
- **179** tempos vieram de palavras reconhecidas literalmente pelo Whisper-small; **1** palavra foi recuperada pelo Whisper-base; **2** utilizaram equivalências fonéticas/numéricas documentadas (não prova de pronúncia perfeita). **Nenhum** tempo foi interpolado.
- Formatos realmente gerados: `.srt`, `.vtt`, `.ass` com karaokê por palavra e `e01-v2-caption-timeline.json` rastreável por token.
- Máximo **2 linhas**, **28 caracteres por linha**, sem sobreposição relevante entre blocos; primeira legenda em 0,000 s e última termina aos 70,140 s.
- **Workflow real verificado:** https://github.com/BORELLITO/corte-fino-engine/actions/runs/44208934506 (**SUCCESS**, suíte de caption e render). Usou FFmpeg portátil versionado `imageio-ffmpeg==0.6.0` para não depender de ffmpeg/apt presentes no runner.
- Um arquivo de diagnóstico real de **540×960**, H.264 + AAC, ~70,43 s foi gerado, **um quadro foi fisicamente decodificado no GitHub** e também inspecionado na conversa. O cabeçalho legível diz **“PRÉVIA TÉCNICA - NÃO PUBLICAR”**. O fundo é neutro: **não é uma master final do canal**.

**Proveniência byte a byte:** `contracts/e01_v2_caption_qa_real_evidence_v1.json`, artefato GitHub ID `14385236602`, run `44208934506`. SHA-256 do MP4 `e6770f417aa335dc80277ed45bab50b97980ad035b5bf52cfccd862e6da10bc1`. Cada um dos sete arquivos gerados tem seu hash fixado no contrato.

## Posição editorial, percepção e limitações

A versão da legenda reproduz o roteiro aprovado, não o texto reconhecido literalmente pelo ASR. A expressão “esperar machuca” foi reconhecida pelo Whisper-small, enquanto o Whisper-base segmentou como “esperar uma chuca”; esse alerta de pronúncia **continua registrado**, sem provocar uma reescrita excessiva.

O efeito karaoke foi renderizado com alinhamento por timestamps estimados, mas **QA de sincronização frame a frame não foi aprovado**. O formato final será **1080×1920** a 30 ou 60 fps, com conteúdo visual verdadeiro, safe zones das plataformas e validação efetiva.

**Não afirmar:** liberação de direitos comerciais do runtime da voz, licença de música, imagens originais geradas/checadas, áudio master final, sincronismo perfeito ou publicação autorizada. Todos permanecem bloqueados.

## Continuidade visual: doze cenas com identidade e função

O `contracts/e01_v2_12_scene_visual_plan_v1.json` cria 12 direções audiovisuais **cronometradas pelo áudio real**, do segundo 0,000 ao 70,425. Todas as 28 legendas foram associadas a um desses blocos. A proposta usa realismo cinematográfico discreto, ambiente contemporâneo coerente, um personagem anônimo consistente e uma breve metáfora visual para o contexto profético de Habacuque. Nenhum texto bíblico moderno é reproduzido como “arte” e não há encenação apresentada como fato histórico.

**É um plano de filmagens e prompts, não ativos físicos gerados.** Todos os campos `generated=false`, `rights=PENDING`, `asset_sha256=null` e `publication_authorized=false` permanecem bloqueados. Sem fotografias reais, licenças e hashes, o motor não pode promover o storyboard para vídeo final.

## Próximo gate operacional

Criar/licenciar cenas reais de acordo com os 12 segmentos; preservar os hashes e direitos de cada ativo, validar continuidade visual e relação bíblica; montar em 1080×1920 usando áudio e legendas aprovados, música com direitos e QA de mídia física. Deixar o vídeo em `BLOCKED` caso a licença do runtime ou qualquer recurso não possa ser comprovada. Não pedir microaprovação do usuário para roteiro e QA; somente para a futura publicação.

A PR desta etapa é empilhada sobre a **#38**. `main`, `verbo-no-chao/bootstrap`, piloto Salmo 13, script e WAV v1/v2 permanecem imutáveis. Não houve merge, postagem, exclusão ou contratação de serviço.
