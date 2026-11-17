# VERBO NO CHÃO — Pré-voo de áudio E01 (evidência revisada em 17/11/2026)

**Estado: `BLOCKED`. A etapa executável produz documentos, NÃO áudios.**  
Branch experimental empilhada sobre PR #33, sem alterar o piloto Salmo 13 nem liberar publicação.

## 1. Revisão bíblica do primeiro roteiro

Referência E01: **Habacuque 1:2–4**, "Quando você pergunta e nada muda".

Fontes de contexto consultadas:

- Texto e notas da NET Bible: https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4
- Estrutura do livro no BibleProject: https://bibleproject.com/guides/book-of-habakkuk/
- Análise literária da Bible.org: https://new.bible.org/seriespage/2-habakkuk

O texto de 1:2–4 é um **lamento profético por violência, injustiça e perda da eficácia da lei**. A resposta divina aparece mais adiante no livro, seguida de novas perguntas. O roteiro E01 foi corrigido para incluir o aspecto da justiça distorcida e para não sugerir que o silêncio dure por todo o livro.

`contracts/e01_editorial_crosscheck_v1.json` registra três afirmações de contexto, três fontes e SHA-256 de cada um dos seis blocos do texto revisado. `agents/e01_context_review.py` confere referências, vínculos, integridade e estados sem copiar textos das fontes. **Isto é cruzamento editorial interno, não revisão teológica independente por uma pessoa e não prova de originalidade absoluta.**

## 2. Pesquisa atual da voz pm_alex

- **Modelo Kokoro-82M:** licença Apache-2.0 declarada pela upstream. https://huggingface.co/hexgrad/Kokoro-82M
- **Voz `pm_alex`:** presente na lista oficial de pt-BR, hash abreviado `cf0ba8c5`. https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- **Arquivo upstream:** a própria página do arquivo publica o SHA-256 integral `cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526`. https://huggingface.co/hexgrad/Kokoro-82M/blob/main/voices/pm_alex.pt
- **Termos Kokoro Web:** atualizados em **30/10/2026**, permitem baixar WAV e usar narração em projetos pessoais ou comerciais **desde que todos os direitos e licenças necessários sejam respeitados**. https://kokoroweb.app/terms
- **Execução:** o serviço informa que faz a síntese **dentro do navegador** usando recursos do dispositivo que está executando a página; não é uma API de sintetização no servidor. Em navegador cloud, a síntese de uma **frase técnica original** já foi comprovada em 17/11/2026; essa sessão não gerou o roteiro E01. https://kokoroweb.app/privacy

A upstream do modelo e o site de TTS **são entidades independentes**. O hash publicado no Hugging Face é **metadado do arquivo upstream**, não a medição dos bytes realmente baixados ou usados pelo site. Não baixamos nem carregamos o `.pt`; formatos PyTorch com pickle não devem ser desserializados a partir de conteúdo não verificado.

### Direitos ainda não comprovados

1. Uso efetivo do objeto de voz pelo mecanismo de inferência: o cache real da sessão apresentou `pm_alex.bin` com SHA-256 oficial, mas isso não prova de forma independente o consumo desse objeto pelo runtime.
2. Avisos e licenças das dependências realmente usadas, incluindo eventuais direitos de terceiros sobre o pack.
3. Revisão teológica/editorial independente e aprovação explícita do roteiro pelo proprietário.
4. Integridade, inteligibilidade, sincronização e duração do WAV que somente será produzido depois dos gates.

O fato de os termos do site permitirem **uso comercial condicional** elimina a antiga pendência "termos do serviço não encontrados", mas **não** libera automaticamente um áudio ou publicação.

## 2.1. Novo gate: bytes reais do arquivo ONNX (PR dependente)

Uma investigação mais profunda identificou **dois arquivos diferentes** para a voz **pm_alex**:

- Modelo original (PyTorch): `hexgrad/Kokoro-82M/voices/pm_alex.pt`, SHA-256 **`cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526`**.
- Distribuição ONNX para navegadores: `onnx-community/Kokoro-82M-v1.0-ONNX/voices/pm_alex.bin`, SHA-256 **`0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a`**.
- Fontes oficiais: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/voices/pm_alex.pt e https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/blob/main/voices/pm_alex.bin.

**Hashes diferentes não provam fraude; os arquivos pertencem a distribuições e formatos diferentes.** Também não é possível inferir apenas pelo nome qual deles o Kokoro Web carrega.

O contrato `contracts/onnx_voice_asset_v1.json` fixa formato, revisão de origem `4685882`, URL HTTPS, SHA-256 esperado e limite de tamanho. O executor `agents/onnx_byte_audit.py` efetua download **somente para leitura e hash em memória**, sem desserialização, sem TTS, sem salvar nem redistribuir o arquivo, usando limite de 1 MB.

O GitHub Actions gera `vnc-onnx-voice-asset-audit`, que registra `VERIFIED_UPSTREAM_ONNX_BYTES_HOSTED_UNPROVEN` apenas após leitura e hash de bytes reais. Se houver falha de rede/hash/tamanho, registra `BLOCKED_UPSTREAM_BYTES_NOT_VERIFIED` e o pré-voo mantém a trava. O executor do pré-voo lê esse relatório e inclui hash de sua proveniência. O arquivo de voz binário **não** entra nos artefatos.

**Evidência atualizada:** o ONNX upstream foi verificado por SHA e, durante uma síntese controlada de 5,875 s no Kokoro Web, um arquivo `pm_alex.bin` no cache do navegador correspondeu ao SHA oficial e tinha 522.240 bytes. Isso comprova a integridade do item em cache naquela sessão, **não o uso efetivo desse objeto pela inferência**, nem os avisos de todos os componentes e a liberação comercial final. Ver `docs/KOKORO_CONTROLLED_SMOKE_V1.md`.

## 3. O motor executa e verifica

Fluxo: `editorial_production` → `script_production`; em paralelo, `onnx_voice_asset_check` → `audio_preflight` (espera ambos) → 8 auditores + coordenador.

Artefatos de GitHub Actions: `vnc-onnx-voice-asset-audit` (somente JSON da checagem binária) e `vnc-audio-preflight`.

- `audio-preflight/preflight.json`: E01, hashes de entrada, seis segmentos, voz candidata, revisão interna, bloqueios e estados.
- `audio-preflight/context_crosscheck.json`: resultado do cruzamento editorial interno com o mesmo fingerprint do roteiro.
- `audio-preflight/preflight.md`: texto em seis segmentos, limitações e direitos pendentes.
- `audio-preflight/historical_smoke.json`: prova do teste técnico anterior, sem liberação de direitos.
- `audio-preflight/rights_review_handoff.json`: dossiê de seis fontes, licenças e bloqueios.
- `audio-preflight/e01_human_review_packet.md`: roteiro integral e checklist para um revisor bíblico humano independente.
- `audio-preflight/report.json`: estado `BLOCKED`, arquivos e hashes para o coordenador.

O coordenador impede qualquer falsa conclusão de que `internal_context_crosscheck_completed` seja uma revisão humana ou autorização de áudio. A CI pode passar tecnicamente enquanto a **produção de áudio permanece bloqueada com motivos reais**.

## 4. Escopo e rollback

Sem contratação paga, publicação, WAV do E01, upload de mídia de produção, mudanças no piloto Salmo 13, alteração de `main` ou merge automático. O workflow utiliza minutos da cota GitHub Actions. A voz `pm_alex` é **baseline**, não voz definitivamente liberada. Os demais roteiros E02 e E03 não foram revisados nesta etapa.

Próximo gate: revisão bíblica humana independente do roteiro exato, aprovação do proprietário e revisão de direitos/avisos aplicáveis à voz usada para produzir o WAV final. Uma aprovação de roteiro não significa aprovação de áudio, vídeo ou publicação.


## Política posterior: QA autônomo de roteiro (17/11/2026)

Para novos episódios, `contracts/autonomous_editorial_policy_v1.json` substitui a exigência de leitura humana/assinatura do roteiro pelo proprietário. A evidência real de análise contextual do ChatGPT para o E01 está no recibo `contracts/e01_ai_editorial_review_v1.json`, com SHA-256 e oito pilares. O novo arquivo `audio-preflight/ai_editorial_approval.json` registra aprovação **somente do roteiro**; `audio-preflight/video_pillar_readiness.json` apresenta os doze pilares: oito avaliados no texto e quatro bloqueados até haver provas físicas, direitos e QA real. Nenhum modelo adicional de IA é executado dentro do GitHub Actions.

O `e01_human_review_packet.md` conserva apenas valor de auditoria **opcional**. Não deve mais ser solicitado ao proprietário, e a ausência de parecer humano não é bloqueio automático de texto. O áudio do E01 permanece bloqueado por questões reais de direitos do runtime e de produção ausente. O vídeo final não exige revisão de qualidade do usuário, mas publicação segue dependente de autorização explícita.
