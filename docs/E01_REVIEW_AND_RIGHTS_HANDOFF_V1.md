# VERBO NO CHÃO — E01 | Handoff de revisão bíblica e licenciamento v1

**Status do dossiê de direitos:** `REVIEW_PACKET_READY_NOT_APPROVED` (registro histórico complementar) • **Roteiro E01:** `AUTO_APPROVED_FOR_INTERNAL_PRODUCTION` via política de IA posterior • **Áudio E01:** `BLOCKED` • **Publicação:** autorização específica ainda necessária.

## O que foi implementado e medido

O motor possui uma única narração canônica revisada para **Habacuque 1:2–4** (E01, *Quando você pergunta e nada muda*), em seis blocos e com SHA-256 do texto preservado no contrato `contracts/e01_editorial_crosscheck_v1.json`.

Foi produzido um **dossiê de evidências** `contracts/e01_rights_review_dossier_v1.json` com seis linhas de proveniência: modelo, distribuição ONNX, voz observada no cache, termos comerciais do serviço, informações sobre o runtime do site e direitos de uso das referências bíblicas. Não é parecer jurídico nem parecer teológico externo.

A integração `agents/e01_rights_handoff.py` assegura que:

- O texto não mude sem alterar os hashes;
- A permissão comercial **condicional** do serviço não se torne aprovação geral das licenças;
- A identidade SHA-256 observada no cache não se torne prova de qual objeto o motor efetivamente consumiu;
- Revisão teológica humana, aprovação do titular do canal, licenças completas e publicação nunca sejam promovidas automaticamente;
- URLs falsas, fonte substituída e direitos inventados façam a checagem **falhar**, não passar.

`agents/audio_preflight.py` produz, em cada execução, os seguintes arquivos adicionais no artefato `vnc-audio-preflight`:

- `audio-preflight/e01_human_review_packet.md` — **roteiro integral exato** com seis blocos, referências, checklist para parecer humano e situação de direitos;
- `audio-preflight/rights_review_handoff.json` — resultado técnico de validação, ainda **não aprovado**.

O coordenador exige que esse pacote de revisão exista e esteja explicitamente `REVIEW_PACKET_READY_NOT_APPROVED`; não inventa nem substitui assinatura de um revisor humano.

## Fontes públicas revisadas em 17/11/2026

1. Modelo original: https://huggingface.co/hexgrad/Kokoro-82M — declara **Apache-2.0**, menciona uso comercial da tecnologia e descreve os dados de treinamento (incluindo exemplos CC BY).
2. Conversão ONNX: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX — declara **Apache-2.0**, independentemente do site hospedado.
3. Arquivo de voz ONNX: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/blob/main/voices/pm_alex.bin — SHA-256 conhecido. A evidência do navegador ficou registrada em `contracts/kokoro_controlled_smoke_evidence_v1.json`.
4. Serviço comercial: https://kokoroweb.app/terms — revisão de **30/10/2026**; permite WAV para projetos comerciais **quando o usuário tiver os direitos necessários**. O site também alerta sobre texto, músicas e componentes de terceiros.
5. Política do serviço: https://kokoroweb.app/privacy — síntese no navegador; não comprova correspondência entre frontend hospedado e qualquer repositório público.
6. Pesquisa de contexto: https://bibleproject.com/guides/book-of-habakkuk/ e https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4 — bibliografia para análise, **não licença para copiar uma tradução moderna**.

### Ajustes importantes de interpretação jurídica

O uso de áudio gerado por um serviço cujo site permite projetos comerciais **não exige automaticamente licença para redistribuir o código do site**, desde que o projeto use o serviço e não copie seu software. Por outro lado, a permissão contratual do site **não garante** os direitos de todas as vozes e materiais de terceiros, qualidade ou exclusividade da saída. Distinguir essas hipóteses evita tanto bloqueios jurídicos exagerados quanto autorização sem provas.

O uso dos dados de treinamento de terceiros citados pela upstream exige cuidado; não presumir que a licença de um áudio CC BY usado no treinamento cria automaticamente uma obrigação de atribuição em cada saída sintetizada, nem o contrário. A situação da obra final dependerá de direitos e condições aplicáveis.

## Parecer humano opcional; revisão editorial por IA obrigatória

O parecer semântico por IA deve examinar o **roteiro exato** vinculado ao hash, especialmente o gênero de lamento de Habacuque, violência social, lei ineficaz, justiça distorcida, continuidade do diálogo e ausência de promessas temporais sobrenaturais. A versão E01 foi avaliada pelo ChatGPT e vinculada em `contracts/e01_ai_editorial_review_v1.json`. Isto **não é um parecer teológico humano independente**; se houver dúvida crítica, a IA deve corrigir/bloquear, não fingir assinatura externa.

O proprietário não precisa aprovar versões textuais, ajustes de arte, trilha ou montagem. O motor deve validar as evidências reais e aplicar QA interno completo. A **publicação** depende de uma autorização separada. Ninguém deve fingir que a conclusão de um checklist aprova uma licença ou arquivo de vídeo inexistente.

## Evidência, custo e rollback

A solução roda no GitHub Actions usando dados versionados e ferramentas já presentes no motor; não instala modelos novos, não executa TTS de novo, não cria custos diretos adicionais de API, mas consome minutos da cota de CI. O novo trabalho está numa branch isolada empilhada na PR #33, sem merge na branch `bootstrap` ou `main`. PR #25 continua independente.

**Próximo gate real:** a revisão semântica do roteiro E01 já foi versionada e verificada; faltam direitos e avisos de runtime, áudio de produção e a validação física dos demais pilares. O pacote com nome histórico `e01_human_review_packet.md` é somente opcional, não representa tarefa atribuída ao usuário.


## Precedência

Este documento nasceu na PR #34. Para episódios novos, a política posterior `contracts/autonomous_editorial_policy_v1.json` e o gate `agents/autonomous_editorial_gate.py` substituem **somente** a exigência de parecer humano e assinatura do usuário em roteiro/vídeo. Seus controles de direitos e impossibilidade de publicação automática continuam obrigatórios. O piloto Salmo 13 conserva suas próprias travas.
