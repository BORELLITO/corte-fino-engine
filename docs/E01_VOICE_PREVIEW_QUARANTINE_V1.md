# VERBO NO CHÃO — Candidato de voz E01 com prova física (quarentena)

**Nova etapa técnica:** tentar sintetizar o texto **exato** do episódio `VNC-W01-E1`, cujo SHA-256 de narração é `67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990`. Isso é diferente do teste anterior de uma frase técnica: agora o roteiro completo é a entrada controlada.

## Governança e direitos

- Fonte da narração: `agents/first_batch_seed.json`, aprovado *somente para produção editorial interna* pelo registro `contracts/e01_ai_editorial_review_v1.json`; cada edição invalida a prova anterior.
- Voz: Kokoro `pm_alex` / português do Brasil. Usar o serviço público sem autenticação, uma única geração em Chrome isolado no GitHub Actions, respeitando os termos da página https://kokoroweb.app/terms .
- O serviço permite WAV comercial **condicionalmente aos direitos relevantes**, não certifica licenças de todos os componentes nem a inteligibilidade.
- A origem do modelo `hexgrad/Kokoro-82M` declara Apache-2.0 em https://huggingface.co/hexgrad/Kokoro-82M .
- O candidato **não** é áudio master nem peça publicável. Direito completo e notices do runtime real, revisão por escuta/comparação com script e aprovação do vídeo final continuam pendentes. A política do usuário dispensa sua revisão manual intermediária; QA não pode ser fingido.

## Componente implementado

- `agents/e01_voice_preview.py` valida a origem, roteiro, SHA-256 e a separação de direitos; sintetiza **uma vez** por execução e verifica o arquivo ONNX `pm_alex.bin` no cache do **mesmo navegador** (`522240` bytes, SHA-256 `0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a`).
- O áudio é lido a partir do objeto `blob:` local no navegador. A validação física exige RIFF/WAVE, PCM16 decodificável, taxa suportada, 25–150 segundos, PCM não silencioso, bytes sem truncamento e SHA-256.
- A prova gera `voice-preview-e01/e01-preview-only.wav` e `voice-preview-e01/report.json` **somente quando as verificações passam**. Caso qualquer verificação falhe, o programa apaga o WAV candidato e registra um código de erro em `report.json`. Não altera `audio-preflight/preflight.json`, manifesto de vídeo, gates de direitos ou autorização de publicação.
- `.github/workflows/verbo-no-chao-e01-voice-preview.yml`: workflow **one-shot** ligado a alterações em seu próprio arquivo ou acionamento explícito. O runner usa Chrome isolado e Playwright versionado. Não instala APIs pagas, não publica externamente, não grava binários do modelo, não registra credenciais, não tenta download em massa.
- Artefatos temporários do GitHub Actions são privados ao contexto do repositório e têm retenção de 7 dias; não devem ser vinculados a publicações.

## Gates que ainda precisam ser cumpridos

1. Conferir o resultado da execução do navegador, incluindo a decodificação física e hash do WAV. **Um CI verde não basta por si só: é preciso ler o relatório e confirmar os bytes.**
2. QA de inteligibilidade e pronúncia **sobre o áudio real**; verificar silêncio, cortes, palavras omitidas e fidelidade ao roteiro. A mera leitura dos cabeçalhos WAV **não** é escuta.
3. Resolver direitos de uso efetivos da voz e dos recursos, sem transformar permissão condicional em autorização definitiva.
4. Obter/criar mídia visual original coerente, trilha com licença, legendas sincronizadas e master real; validar cada componente e antirrepetição.
5. Somente após QA audiovisual completo: disponibilizar vídeo final. Publicação exige autorização específica do proprietário, separada.

## Preservação e rollback

Branch nova sobre PR #35, sem merge em `main` nem `verbo-no-chao/bootstrap`. Piloto Salmo 13 protegido. Se o teste falhar, manter relatórios com causa comprovada e descartar só a branch isolada; nenhuma produção já aprovada é sobrescrita.


## Resultado real da execução — 17/11/2026

**Run comprovado:** https://github.com/BORELLITO/corte-fino-engine/actions/runs/44192226678

O job executou **13 testes do componente** e a geração do texto integral. O navegador retornou WAV IEEE_FLOAT32, que passou na normalização segura do motor para WAV PCM16. O arquivo resultante foi baixado do artefato e conferido novamente, fora do GitHub, por um decodificador de áudio:

| Medida | Resultado |
|---|---|
| Roteiro | `VNC-W01-E1` (SHA-256 `67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990`) |
| Voz | `pm_alex` no português brasileiro |
| Cache de voz na mesma sessão | SHA-256 ONNX upstream correspondente; 522.240 bytes |
| Fonte recebida | IEEE float32 WAV, 6.727.244 bytes |
| Hash SHA-256 fonte | `ece58c8f94914f08295b900be992288eb8f6df30f4fefbcc844ca34d651ca14b` |
| WAV normalizado | PCM16, mono, 24.000 Hz |
| Duração | **70,075 s** |
| Frames | 1.681.800 |
| Tamanho normalizado | **3.363.644 bytes** |
| SHA-256 normalizado | **`f7c18eac3b8ebc59069665d5e633d8ace1c342efd34546e0591cb7dd713a05d4`** |
| RMS e pico PCM | 2.258,19 / 26.887 |
| Pico estimado | −1,72 dBFS |
| RMS estimado | −23,23 dBFS |
| Amostras com amplitude acima de 99% do máximo | 0 |
| Escuta, correspondência de transcrição e pronúncia | **NÃO AVALIADAS** |
| Licenças finais e publicação | **NÃO LIBERADAS** |

O relatório original `report.json` tem **2.262 bytes** e SHA-256 `a11f144722de64a1cd096deb460a21522104ba09cd4572bf13cc61a64c570686`. O artefato `vnc-e01-quarantined-voice-preview` (ID `14378530045`) expira após sete dias.

O contrato `contracts/e01_real_voice_preview_evidence_v1.json` preserva esses metadados sem versionar nem distribuir os pesos do modelo ou áudio de produção. **Não se deve tratar essa evidência como autorização comercial, conclusão de QA subjetivo ou master publicável.**

### Bloqueios remanescentes

1. Verificação automatizada da fidelidade do áudio à transcrição original e inteligibilidade/pausas, sem exigir que o proprietário ouça.
2. Avaliação real dos direitos da voz/serviço e dos componentes da versão usada.
3. Criação de imagens/clipes originais e trilha com licença comprovada, montagem, legendas sincronizadas e exportação de master física.
4. QA final de todos os pilares e, apenas para publicação, autorização explícita do proprietário.
