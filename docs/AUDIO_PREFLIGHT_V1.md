# VERBO NO CHÃO — Pré-voo de áudio E01 (evidência revisada em 17/11/2026)

**Estado: `BLOCKED`. A etapa executável produz documentos, NÃO áudios.**  
Branch experimental empilhada sobre PR #29, sem alterar o piloto Salmo 13 nem liberar publicação.

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
- **Execução:** o serviço informa que faz a síntese **dentro do navegador** usando recursos do dispositivo que está executando a página; não é uma API de sintetização no servidor. Em um navegador cloud, a computação pode ocorrer na sessão cloud, mas isso não foi testado nesta camada. https://kokoroweb.app/privacy

A upstream do modelo e o site de TTS **são entidades independentes**. O hash publicado no Hugging Face é **metadado do arquivo upstream**, não a medição dos bytes realmente baixados ou usados pelo site. Não baixamos nem carregamos o `.pt`; formatos PyTorch com pickle não devem ser desserializados a partir de conteúdo não verificado.

### Direitos ainda não comprovados

1. Identidade do arquivo de voz realmente carregado pelo site hospedado e sua correspondência com a upstream.
2. Avisos e licenças das dependências realmente usadas, incluindo eventuais direitos de terceiros sobre o pack.
3. Revisão teológica/editorial independente e aprovação explícita do roteiro pelo proprietário.
4. Integridade, inteligibilidade, sincronização e duração do WAV que somente será produzido depois dos gates.

O fato de os termos do site permitirem **uso comercial condicional** elimina a antiga pendência "termos do serviço não encontrados", mas **não** libera automaticamente um áudio ou publicação.

## 3. O motor executa e verifica

Fluxo: `editorial_production` → `script_production` → `audio_preflight` → 8 auditores → coordenador.

Artefato de GitHub Actions: `vnc-audio-preflight`.

- `audio-preflight/preflight.json`: E01, hashes de entrada, seis segmentos, voz candidata, revisão interna, bloqueios e estados.
- `audio-preflight/context_crosscheck.json`: resultado do cruzamento editorial interno com o mesmo fingerprint do roteiro.
- `audio-preflight/preflight.md`: texto em seis segmentos, limitações e direitos pendentes.
- `audio-preflight/report.json`: estado `BLOCKED`, arquivos e hashes para o coordenador.

O coordenador impede qualquer falsa conclusão de que `internal_context_crosscheck_completed` seja uma revisão humana ou autorização de áudio. A CI pode passar tecnicamente enquanto a **produção de áudio permanece bloqueada com motivos reais**.

## 4. Escopo e rollback

Sem gastos, publicação, WAV, upload, mudanças no piloto Salmo 13, alteração de `main` ou merge automático. A voz `pm_alex` é **baseline**, não voz definitivamente liberada. Os demais roteiros E02 e E03 não foram revisados nesta etapa.

Próximo gate: aprovação editorial explícita do roteiro após revisão independente e validação de identidade/direitos do pack realmente utilizado. Uma aprovação de roteiro não significa aprovação de áudio, vídeo ou publicação.
