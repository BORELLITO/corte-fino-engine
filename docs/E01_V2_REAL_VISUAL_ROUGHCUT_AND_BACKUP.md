# VERBO NO CHÃO — E01 v2: primeiro corte visual REAL, com mídia em quarentena

**Etapa:** `REAL_12_SCENE_VISUAL_ROUGHCUT_QA_NOT_MASTER`  
**Escopo:** produção técnica original do E01 `VNC-W01-E1`, versão 2, **sem publicação**.

## O que realmente foi produzido

- 12 fotogramas originais produzidos pela geração de imagens do ChatGPT nesta conversa, com continuidade visual de protagonista/objetos/ambiente, inspirados no storyboard da PR #39.
- 1 fotografia vertical original em resolução próxima à saída; 11 enquadramentos extraídos de uma prancheta cinematográfica original de 3×4 quadros. **Os 11 são material de baixa resolução reampliado.**
- Conversão para 12 arquivos JPEG `720×1280` com hashes SHA-256 distintos e sequências reais contínuas de 0,000s a 70,425s.
- Movimento de câmera **simulado com FFmpeg (zoom/pan)**. Não chamar as 12 imagens de clipes de vídeo gerados por IA.
- 1 rough cut audiovisual real **`720×1280 / 30fps / 2.113 frames / aproximadamente 70,433s / H.264 + AAC`**, usando exatamente o WAV E01 v2 de SHA `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e` e legenda ASS `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`.
- Watermark visível de QA: **PRÉVIA TÉCNICA — NÃO PUBLICAR**. Sem música não licenciada.
- SHA-256 do MP4: **`a080e7d572a28befb8657157bfe3fedbb3b0d1b30d1276beee3a2173f45c2cfa`** (4.866.921 bytes).
- O pacote com os 12 JPG, imagens geradoras originais, legendas e relatórios tem SHA `151f488d6f73416d5a937e726a7a99dc9cb86d922f54a951746ec116228d0b75` e 5.475.964 bytes.

## Evidências da execução

**Contêiner local desta conversa (não GitHub Actions):**
- Hash do vídeo conferido.
- **13 frames** de posições diferentes decodificados e inspecionados; houve variação real de imagens, sem segmentos inteiramente pretos.
- Segunda verificação decodificou **a sequência completa de vídeo e áudio com FFmpeg 7.0.2**, código de retorno 0, sem erro de decodificação: `ffmpeg -v error -i <arquivo_físico> -f null -`.
- `contracts/e01_v2_visual_full_decode_evidence_v1.json` registra a origem local e os limites dessa prova; **não afirma que GitHub Actions viu ou codificou o MP4**.
- `contracts/e01_v2_12_real_visual_roughcut_evidence_v1.json`: manifesto com 12 arquivos, cada tamanho, hash SHA, timeline, versão original/derivada e estado de direitos.
- `agents/e01_visual_roughcut_gate.py`: verifica os bytes físicos do ZIP/JPEG, assinatura dos pais originais e SHA exato do MP4, negando evidências apenas textuais.
- `agents/e01_visual_roughcut_render.py`: reconstrução local a partir do pacote comprovado + WAV e ASS originais; FFmpeg portátil (imagem via `imageio-ffmpeg`), safe file paths e decodificação integral. Pode ser executado em Work/desktop ou CI **quando** os bytes reais estiverem disponíveis.
- Testes adversariais protegendo cronologia, falsificação de imagem, status de direitos, tentativa de trocar modelo de áudio e falsa aprovação de publicação.

## Backup privado com fontes completas

Foi criado um **backup na Biblioteca pessoal do ChatGPT** em:

`/VERBO_NO_CHAO/E01_V2_ROUGHCUT/`

Contém o MP4 de rough cut, 12 imagens originais com hashes e imagens geradoras, folha de contato, pacote do WAV v2, pacote original de legendas ASS/SRT e o script de reprodução. Os registros foram criados sem sobrescrever arquivos antigos. **Isso NÃO é o mesmo que Google Drive ou um artefato acessível aos runners do GitHub Actions.**

**Implicação técnica:** o GitHub contém código, testes e metadados, mas **não** os JPGs, o WAV e o MP4 em suas branches/artifacts. A CI valida contratos/testes, porém o replay físico no Actions está `BLOCKED_ASSETS_NOT_AVAILABLE` até uma transferência segura e verificável do ZIP e fontes. Não criar endpoint público para ativos privados sem autorização.

## Bloqueios reais que proíbem lançamento

1. **Qualidade:** 11 cenas foram ampliadas a partir de tiles; isso não é master 1080×1920. Devem ser refeitas como imagens individuais em resolução real ou clipes autorizados, mantendo a direção visual.
2. **Direitos:** mesmo sendo imagens originais geradas pelo ChatGPT, a autorização comercial efetiva de todos os componentes, voicepack/runtime e eventuais recursos externos **não** foi definitivamente comprovada.
3. **Áudio:** alerta residual do ASR v2 `esperar uma chuca` ainda não é um defeito acústico confirmado nem aprovação de pronúncia final; persiste o gate.
4. **Música:** nenhuma trilha foi inserida sem comprovação de licença. Selecionar/compor e documentar a fonte antes da master.
5. **Validação:** a composição de HQ 1080×1920, safe zone de todas as plataformas, legibilidade e QA visual integral, loop contínuo e sincronismo final ainda não foram concluídos.
6. **Publicação:** a ação de enviar o vídeo a YouTube/TikTok permanece explicitamente não autorizada; o proprietário dispensou microaprovações de qualidade, **não** autorização separada para publicar.

## Segurança e rollback

Branch isolada e PR DRAFT sobre a #39, sem modificar `main`, `verbo-no-chao/bootstrap`, piloto Salmo 13 ou roteiros/WAV v1/v2. Não houve merge, postagem, compra, geração paga, remoção ou alteração de permissões.

## Próximo passo

Gerar/refinar os 11 ativos visuais com resolução realmente adequada (não upscale artificial), sincronizar sua transferência segura com a nuvem ou o GitHub Actions, verificar hashes/direitos, montar nova versão 1080×1920 com trilha licenciada, fazer QA físico final e manter publicação bloqueada até autorização específica.
