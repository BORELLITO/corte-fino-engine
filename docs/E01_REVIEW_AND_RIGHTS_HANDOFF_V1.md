# VERBO NO CHÃO — E01 | Handoff de revisão bíblica e licenciamento v1

**Status:** `REVIEW_PACKET_READY_NOT_APPROVED` • **Áudio E01:** `BLOCKED` • **Publicação:** proibida até autorização independente.

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

## Parecer humano ainda indispensável

O revisor deve examinar o **roteiro exato** vinculado ao hash, especialmente o gênero de lamento de Habacuque, violência social, lei ineficaz, justiça distorcida, continuidade do diálogo e ausência de promessas temporais sobrenaturais. Não é suficiente um teste de estrutura ou uma revisão de IA a partir de comentários; o parecer humano deve ser identificável e **não pode ser criado por uma ferramenta fingindo ser outra pessoa**.

O proprietário deve aprovar posteriormente a versão textual exata, separadamente da voz, arte, trilha, montagem e publicação. **Nenhuma dessas decisões foi simulada.**

## Evidência, custo e rollback

A solução roda no GitHub Actions usando dados versionados e ferramentas já presentes no motor; não instala modelos novos, não executa TTS de novo, não cria custos diretos adicionais de API, mas consome minutos da cota de CI. O novo trabalho está numa branch isolada empilhada na PR #33, sem merge na branch `bootstrap` ou `main`. PR #25 continua independente.

**Próximo gate real:** obter um parecer bíblico humano independente sobre `e01_human_review_packet.md` e a aprovação do titular vinculada ao hash. A validação de licenças e avisos da versão do serviço usada para o WAV de produção ainda demanda revisão específica antes da entrega comercial.
