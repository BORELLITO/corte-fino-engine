# VERBO NO CHÃO — Pré-voo de áudio E01 (v1)

**Estado operacional: BLOCKED** • **Build automatizado do pré-voo: IMPLEMENTADO**  
Data da verificação pública: 17/11/2026.

## Decisão

Não gerar narração definitiva nem publicar até existir revisão bíblica/autorais do roteiro e prova verificável da cadeia de uso comercial da voz **no runtime que será realmente usado**. Para reduzir custo e riscos, preparar o pacote de TTS em JSON/Markdown antes de iniciar serviços externos.

O primeiro candidato é `VNC-W01-E1` (Habacuque 1:2–4), roteiro ainda `DRAFT_REVIEW_REQUIRED`. Os episódios E2 e E3 permanecem intactos.

## Pesquisas oficiais verificadas

1. O proprietário upstream `hexgrad/Kokoro-82M` declara **Apache-2.0** no cartão do modelo e disponibiliza a voz brasileira `pm_alex`.
   - https://huggingface.co/hexgrad/Kokoro-82M
2. O catálogo `VOICES.md` da upstream identifica `pm_alex` como pt-BR masculino e indica o **prefixo de hash** `cf0ba8c5`. Um prefixo não substitui o SHA-256 integral dos bytes recebidos.
   - https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
3. A página dos arquivos do modelo lista `voices/pm_alex.pt`. **Não foi baixado, hasheado nem validado um pack físico neste fluxo**, e não se presume que um serviço hospedado use exatamente esse pack.
   - https://huggingface.co/hexgrad/Kokoro-82M/tree/main/voices
4. O repositório oficial do runtime Kokoro publica texto de licença Apache, mas isso **não comprova os termos de serviço, dependências e os limites comerciais de um site hospedado por terceiros**.
   - https://github.com/hexgrad/kokoro/blob/main/LICENSE
5. A decisão anterior do piloto em `contracts/pilot_voice_decision.json` mantém `pm_alex` como **baseline de prévia**, com licenciamento exato do pack e runtime pendentes.

O registro auditável está em `contracts/kokoro_voice_research_v1.json`. Ele **separa evidência upstream verificada de pontos legais e técnicos não demonstrados**, sem marcar comercialização como liberada. Licença Apache do modelo não garante, por si só, direitos sobre todos os elementos e serviços externos.

## Pipeline real

`editorial_production` → `script_production` → `audio_preflight` → 8 auditorias → `coordinator`.

O preflight produz o artefato de GitHub Actions `vnc-audio-preflight` com:

- `audio-preflight/preflight.json`: identidade do roteiro, hash da narração e de cada um dos seis blocos, voz candidata, fontes e bloqueios.
- `audio-preflight/preflight.md`: roteiro E01 dividido em seis partes e a revisão necessária, sem reescrever nenhum texto.
- `audio-preflight/report.json`: estado `BLOCKED`, lista de blockers e hashes dos dois arquivos produzidos.

O coordenador **não se limita a exibir oito jobs verdes**: incorpora a situação do áudio. Reportar licença liberada, áudio gerado ou autorização de publicação sem prova invalida o relatório.

Os arquivos ficam retidos por 14 dias em GitHub Actions. Os rascunhos já são públicos por estarem no repositório público; nunca inserir tokens, IDs privados ou dados sensíveis em relatórios públicos.

## Critérios de aceitação desta camada

- `Engine Gates` verde no SHA final; regressões editoriais e do piloto continuam cobertas.
- `Eight Specialist Audits` verde operacionalmente, com relatórios do preflight e do coordenador.
- Áudio permanece `BLOCKED` com motivos explícitos, e **nenhum WAV é gerado**.
- Rejeição automática de hash adulterado do roteiro, flag de aprovação ou publicação, falso direito comercial do pack, serviço não verificado e entradas incompletas.
- Sem gastos, cadastro de serviço, download de modelos não auditados, publicação ou alteração de estado do Salmo 13.

## Gates futuros necessários

- Revisão teológica e narrativa por leitura independente do texto bíblico e dos trechos autorais (a verificação automática atual não conclui exegese).
- Aprovação explícita do roteiro do primeiro episódio pelo proprietário antes de geração definitiva.
- SHA-256 integral do pack de voz realmente utilizado e documentação/licença aplicável ao seu uso comercial.
- Termos do serviço de execução escolhido (não confundir licença do Kokoro open-source com contrato de serviço de terceiros).
- Medição real de áudio WAV, pronúncia, pausas, sincronização, loudness e ducking; depois QA do master e direitos de cada asset.
- Aprovação de vídeo e autorização de publicação permanecem decisões separadas.

## Controle de dependências e rollback

Branch isolada deste PR sobre `verbo-no-chao/first-three-scripts-v1` (PR #28), que depende de #27 e #26. A PR #25 da integridade física é independente. **Nenhum PR foi mesclado na branch operacional** `verbo-no-chao/bootstrap` ou na `main` histórica. Reverter esta nova PR não afeta o piloto, plano editorial ou scripts anteriores.
