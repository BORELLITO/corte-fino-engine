# VERBO NO CHÃO — QA independente da narração E01 por reconhecimento de fala (v1)

**Escopo:** episódio `VNC-W01-E1` (Habacuque 1:2–4), 70,075 s, WAV de prévia em quarentena. **O roteiro não exige revisão do usuário.** O objetivo é automatizar a conferência de fidelidade e cronologia do áudio, não promover um vídeo inexistente.

## Entrada real e imutável

O workflow `.github/workflows/verbo-no-chao-e01-asr-audit.yml` baixa o artefato privado `vnc-e01-quarantined-voice-preview` do run GitHub Actions [44192226678](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44192226678) por meio da própria integração GitHub, sem gerar o áudio novamente.

Antes de baixar o modelo de reconhecimento, verifica:

- `e01-preview-only.wav`: 3.363.644 bytes, SHA-256 `f7c18eac3b8ebc59069665d5e633d8ace1c342efd34546e0591cb7dd713a05d4`;
- `report.json` do produtor: 2.262 bytes, SHA-256 `a11f144722de64a1cd096deb460a21522104ba09cd4572bf13cc61a64c570686`;
- revisão semântica do roteiro: SHA-256 `67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990`;
- WAV RIFF/PCM16 mono 24 kHz, com exatamente 70,075 segundos.

Qualquer diferença bloqueia o processo. O modelo baixado não fica versionado no repositório nem nos artefatos. O pacote de vídeo, o piloto Salmo 13, e os manifests de publicação não são modificados.

## Método de ASR e comparação

- **Modelo:** `Systran/faster-whisper-small` (multilíngue, não `small.en`) — <https://huggingface.co/Systran/faster-whisper-small>, licença MIT declarada.
- **Biblioteca:** `faster-whisper==1.2.1` — <https://github.com/SYSTRAN/faster-whisper>, licença MIT; CTranslate2 CPU `int8` com 4 threads.
- **Reprodutibilidade:** consulta o commit SHA-1 do modelo no Hugging Face; baixa somente arquivos JSON/binários desse commit exato; computa SHA-256 dos pesos `model.bin` no runner. O relatório informa ambas as identidades.
- **Transcrição:** pt-BR, `task=transcribe`, `beam_size=5`, sem `initial_prompt` com o roteiro (evita contaminação de resultado), timestamps por palavra, `vad_filter=False`, sem carregar dados pessoais.
- **Correção:** normaliza maiúsculas, acentos, espaços e pontuação. Calcula distância verdadeira de Levenshtein por palavras (WER) e caracteres (CER) e enumera blocos de possíveis omissões/substituições, vinculados ao texto original.
- **Portões provisórios:** WER ≤13%, CER ≤8%, sem possível omissão consecutiva superior a seis palavras, timestamps válidos dentro dos 70,075s e mínimo de 15 palavras com tempos. São parâmetros internos de triagem, não métricas de qualidade de áudio universalmente validadas.

Uma **transcrição por ASR não é o áudio real nem uma audição humana**. Mesmo WER e CER baixos não provam automaticamente prosódia, qualidade da pronúncia de nomes bíblicos, entonação, direitos, precisão perfeita das legendas, música ou ausência de erros não reconhecidos pelo próprio modelo. Diferenças altas requerem reavaliação automatizada, ajuste de voz/segmentação, nova síntese com novo SHA e segunda comparação, sem solicitar revisão intermediária ao usuário.

A execução conserva somente `asr-report/report.json` no artefato `vnc-e01-independent-asr-report`: métricas, texto reconhecido, timestamps, possíveis divergências, commit/hash do modelo e os bloqueios de direitos/mídia. **Nunca** envia o WAV ou os pesos do modelo para artefatos externos adicionais, nem publica no YouTube ou TikTok.

## Estágios e integridade

`ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED` significa que o áudio e o roteiro parecem corresponder ao modelo independente sob os limites definidos. **Não significa** que o áudio seja uma master aprovada ou esteja licenciado.

`BLOCKED_ASR_DISCREPANCIES` significa que a transcrição encontrada excedeu um limite; o relatório fornece trechos a investigar.

`BLOCKED_ASR_AUDIT_NOT_COMPLETED` significa falha de dependência, modelo, fonte ou execução, mesmo que outras pipelines estejam verdes.

Os três estados mantêm `voice_rights_cleared=false`, `production_audio_master_approved=false`, `publication_authorized=false`.

## Limites operacionais e continuidade

A primeira execução do modelo `small` pode transferir centenas de MB e consumir minutos de CPU. O workflow é **isolado e one-shot**, com disparo manual disponível posteriormente e sem cron; novos commits editoriais não provocam novas transcrições. Pode haver cotas de minutos do GitHub Actions, mesmo sem API paga. A prévia de voz é retida pelo GitHub por 7 dias; se o artefato expirar, **não** baixar um áudio parecido ou regravar sem tratar como outra revisão com novas provas.

O pacote `agents/e01_asr_qa.py` e `tests/test_e01_asr_qa.py` pode ser testado com Python puro; a inferência só é importada no job de áudio real. Falhas do fornecedor são registradas pelo estágio (modelo, download, inferência), sem vazar tokens ou URLs privadas.

**Próximo gate após esse QA:** entender e corrigir discrepâncias reais de pronúncia/texto; em seguida seguir para a trilha e clipes originais com direitos, temporização das legendas baseada em mídia real, composição e QA do vídeo decodificado. A publicação permanece uma autorização específica e separada do usuário; não existem microaprovações de roteiro ou qualidade a solicitar.
