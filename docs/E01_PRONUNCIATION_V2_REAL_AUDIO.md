# VERBO NO CHÃO — E01 v2 | Correção de pronúncia e nova narração real

**Estado editorial:** `AUTO_APPROVED_FOR_INTERNAL_PRODUCTION` (somente texto).  
**Estado da voz:** `QUARANTINED_E01_V2_WAV_PHYSICALLY_VERIFIED`.  
**Estado da publicação:** `BLOCKED`.

## Diagnóstico e escolha

A versão v1 de Habacuque 1:2–4 foi gerada com `pm_alex`, 70,075 s e SHA-256 `f7c18eac3b8ebc59069665d5e633d8ace1c342efd34546e0591cb7dd713a05d4`. O Whisper-small (WER 2,747%) e Whisper-base (WER 2,747%) reconheceram uma ocorrência inicial de “dói” como “dou/do”. Isso é **alerta corroborado por dois ASRs da mesma família**, não prova definitiva de pronúncia errada.

Estratégia aprovada internamente: **corrigir somente a primeira frase do bloco de conexão**:

| V1 (preservada) | V2 (candidata) |
|---|---|
| Às vezes, dói esperar. | Às vezes, esperar machuca. |

Todos os outros blocos, contexto bíblico, links, parâmetros, título e restrições da v1 permanecem idênticos. O texto preserva lamento sincero e justiça social, sem prometer soluções milagrosas. Fontes de contexto: https://bible.usccb.org/bible/habakkuk/1 ; https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4 ; https://www.workingpreacher.org/commentaries/revised-common-lectionary/ordinary-27-3/commentary-on-habakkuk-11-4-21-4-11 .

## Estado dos hashes e da aprovação

- SHA-256 **v1** imutável: `67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990`.
- SHA-256 **v2** novo: `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6`.
- `contracts/e01_script_v2_candidate.json`: cópia com único trecho alterado, lineage para v1 e publicação false.
- `contracts/e01_ai_editorial_review_v2.json`: **nova análise semântica de oito pilares**, produzida pelo ChatGPT com fontes e âncoras do texto exato. Não é teólogo humano ou revisor independente adicional.
- `agents/e01_v2_candidate.py`: exige que **todas** as demais propriedades do roteiro v2 sejam exatamente iguais à v1, valida o pai, o hash v2 e o novo recibo, e impede atribuir direitos/publicação inexistentes.
- `agents/autonomous_editorial_gate.py`: suporte estritamente versionado para E01 v2, sem afrouxar checagem v1.

## Prova de WAV real — Chrome e Kokoro Web

- [Workflow real](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44204100486), execução `44204100486` no SHA `bcddb4e71bec66133c7628b3f431640da63ed8b5`.
- Modelo selecionado: `pm_alex`, idioma pt-BR. O cache da mesma sessão continha `pm_alex.bin`, SHA ONNX `0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a`. O hash em cache não prova consumo efetivo na inferência.
- WAV original do navegador: IEEE_FLOAT32, **6.760.844 bytes** e SHA-256 `31360887e49f0957d7829c75d1dfbc94ca95abe943d79e4755b28e520e2d9afe`.
- WAV de prévia normalizado: PCM16, mono, 24 kHz, **70,425 s**, **1.690.200 frames**, **3.380.444 bytes**, SHA-256 **`4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`**.
- Pico PCM 26.887, RMS 2.259,42; cabeçalho, duração e hash conferidos novamente após baixar o artefato.
- Relatório `report.json`: 2.394 bytes, SHA-256 `a904ac1d1b10190e1e3cbbd5ba4c9fd8aa9a2a837b9db02dcbf97b64db479a03`.
- Artefato `vnc-e01-v2-pronunciation-safe-preview` ID `14383520578`, retenção 7 dias. Evidência versionada em `contracts/e01_v2_voice_preview_evidence_v1.json`, **sem armazenar áudio nos commits**.
- Nenhuma geração nova afetou a WAV anterior. A v2 continua em quarentena e não pode ser publicada.

## Próxima validação operacional — ASR duplo sobre WAV v2

`agents/e01_v2_dual_asr.py` e `.github/workflows/verbo-no-chao-e01-v2-dual-asr.yml` conferem os **bytes físicos** do novo WAV e do relatório, usam a nova aprovação do roteiro e transcrevem a mesma gravação por dois modelos multilíngues:

- `Systran/faster-whisper-small` e `Systran/faster-whisper-base`, sem usar o roteiro como `initial_prompt`;
- WER, CER, timestamps, omissões e divergência de palavras críticas;
- exigência adicional de reconhecimento da expressão **“esperar machuca”** pelos dois modelos;
- não validar output se ambos repetirem omissão crítica ou se faltar evidência física/temporal;
- preservar status `production_audio_master_approved=false`, `voice_rights_cleared=false`, `publication_authorized=false`.

Passar no ASR significa **triagem textual preliminar**, não audição subjetiva ou licenciamento. Corrigir novamente se um novo erro real aparecer; não solicitar microaprovação do usuário. Em seguida, resolver direitos, mídias visuais com proveniência, música, legendas e master decodificável. Publicação requer autorização específica.

## Segurança

PR empilhada sobre a #37. **Sem merge**, sem mudar `main`, `verbo-no-chao/bootstrap`, roteiro v1 ou piloto Salmo 13, sem criar canal/conta paga, sem publicar. Rollback: manter v1 e descartar branch v2.
