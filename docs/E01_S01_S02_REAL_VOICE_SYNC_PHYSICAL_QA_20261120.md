# E01 · S01 + S02 — prova física de voz real + karaoke de origem (20/11/2026)

**PROJETO EXCLUSIVO:** `VERBO_NO_CHAO_EXCLUSIVO`  
**Conteúdo:** “Quando você pergunta e nada muda” · Habacuque 1:2–4 · E01 v2  
**Escopo:** somente os primeiros **319 quadros / 10,633333 s**. **Prévia 720×1280, não master.**  
**Aprovações:** S01 chuva noturna aprovada visualmente. S02 relógio com gradiente 55% **não aprovada artisticamente**. Rights, música, master e publicação **bloqueados**.

## Por que executar isso agora?

A PR #65 já demonstrou que o ASS original de 28 cues acompanha uma transição S01 + S02 feita com **filmagens em movimento** (chuva em janela e relógio). Entretanto, suas prévias anteriores estavam **sem WAV**. Validar a sincronização com a **narração original real** reduz o risco de aceitar uma imagem aparentemente boa que não acompanha a voz.

Foi recuperado o artefato ainda ativo no [GitHub Actions run 44204100486](https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/44204100486), artifact `14383520578`, sem executar navegador TTS novamente. ZIP íntegro; o WAV `e01-v2-preview-only.wav` foi conferido fisicamente:

| Prova de origem | Fato observado |
|---|---|
| WAV original | **3.380.444 bytes** |
| SHA-256 | `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e` |
| Código/forma | PCM16 mono, 24.000 Hz |
| Duração | **70,425 s** |
| Relatório de origem | SHA `a904ac1d1b10190e1e3cbbd5ba4c9fd8aa9a2a837b9db02dcbf97b64db479a03` |

A entrada de imagem/ASS foi a prévia física anterior, **S01 aprovada visualmente + S02 candidata**, áudio ausente:
- MP4 `S01_S02_GRADE_A_GRADIENT_55_REAL_KARAOKE_QA.mp4`, SHA `f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c`, 720×1280 H264, 319 frames a 30fps, 10,633333s, sem áudio.
- ASS original do E01 v2, 28 diálogos, SHA `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`. Nenhuma palavra, tempo de fala ou estilo foi alterado.

## Resultado renderizado e verificado

**Arquivo real:** `S01_S02_REAL_KARAOKE_AND_ORIGINAL_VOICE_10S_QA_NOT_MASTER.mp4`

- **SHA-256:** `979fcb7d630177efc99e76baa98adc0d34cf0d3a89beaf06484060c7bdd6e5f6`.
- **Bytes:** 2.264.744.
- **Vídeo:** H.264 **cópia do bitstream** do MP4 prévio, sem reencode de vídeo. 720×1280, 319 quadros, 30fps.
- **Voz:** original PCM16 convertido para AAC mono 160k, 48 kHz para container MP4, **sem nova síntese, sem mudança de velocidade, sem música, sem ganho/normalização**.
- **Tempos:** formato total 10,633333s, vídeo 10,633333s, áudio 10,633000s. A partir de zero, sem offset intencional.
- **Decodificação completa:** FFmpeg `-xerror` de vídeo + áudio **PASS**.
- **Alinhamento técnico com a origem:** correlação cruzada do trecho de voz decodificado vs. original de referência (ressampleados a 24 kHz) **≈1,0000**, melhor lag **0 ms**, medidos na janela 0,8–5,8s. Esse ensaio não substitui escuta humana de cada palavra nem prova ausência de atraso subjetivo de legenda.
- **Narração no recorte de 10,63s:** medição `ebur128` do WAV original: **−22,5 LUFS** integrado, LRA 2,1 LU, true peak **−2,3 dBTP**; `volumedetect` média **−22,8 dBFS** e pico amostrado −2,5 dBFS. Nesses limites não foi detectado clipping. O volume ainda não é um mix final calibrado para plataformas.

**Privado e preservado:**  
`/VERBO_NO_CHAO/E01_AUDIO_CANONICAL_V2/e01-v2-preview-only-SHA_VERIFIED.wav`  
`/VERBO_NO_CHAO/E01_S01_S02_QA_REAL_VOICE_20261120/` (MP4, relatório JSON, ZIP de revisão)

O arquivo QA foi renderizado, inspecionado com `ffprobe`, `sha256sum`, decodificado com FFmpeg, e testado em amostras de áudio fisicamente no contêiner. O GitHub **não** precisa baixar WAV nem usar credenciais para rodar os testes offline.

## Integração GitHub e anti-regressão

A PR #65 já é DRAFT, empilhada sobre #63, ainda sem merge. Adicionados nesta PR:
- `contracts/e01_s01_s02_real_voice_sync_qa_20261120_v1.json`, fontes SHA, 319 frames e release flags negativos;
- `agents/e01_s01_s02_real_voice_sync_qa_v1.py`, CLI offline de reprodução **somente com fonte física já presente**, valida SHA/contagem/formatos, mux com copy de vídeo + áudio AAC, full decode, saída com hard-link exclusivo para evitar sobrescrever artefatos;
- `tests/test_e01_s01_s02_real_voice_sync_qa_v1.py`, casos forjados de direitos, duração, 28 cues, 720p, áudio e ausência de mídia;
- este relatório.

Não chamar uma execução CI verde de nova renderização física: os MP4/WAV originais estão em armazenamento privado.

**Limites de contrato:** uma versão compilada com FFmpeg diferente pode ter SHA de saída AAC diferente; o SHA acima é o fato observado nesta execução, não um requisito de byte-identidade universal do encoder.

## Gates não liberados

- **S01:** aprovada somente na direção visual específica (chuva); a fonte aprovada está preservada.
- **S02:** título, mostrador, texto `QUARTZ`, composição e redução localizada de contraste **ainda exigem decisão estética**; não foi automaticamente aceita por ter áudio.
- **Narração:** ASR de dois modelos tinha divergência pontual de segmentação da expressão `esperar machuca`; não regravar sem evidência e não declarar audição humana integral do episódio.
- **Licenças:** permissão geral de stock Pexels e licença geral do modelo Kokoro não substituem liberação específica de direitos de imagem/voz/marcas.
- **Música / mix:** nenhuma trilha adicionada e nenhum sidechain final; não afirmar `AUDIO_QA_PASS` para master.
- **E01 final:** S03–S12 ainda dependem de mídia real coerente; não foi criada master 1080×1920.
- **Publicação:** nenhuma autorização nem canal verificado para postagem; nenhum efeito externo de publicação.

**Próxima ação única:** ouvir/ver a prévia S01+S02 com voz real em tela móvel e tomar decisão artística específica sobre S02 antes de fechar a cena, preservar `PR #65 DRAFT` e não promover para master.
