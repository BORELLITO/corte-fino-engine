# VERBO NO CHÃO — Prova controlada de síntese Kokoro Web (17/11/2026)

**Status técnico: TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED**  
**Status operacional do episódio E01: BLOCKED**. Não publicar, não gerar master, não promover direitos.

## Objetivo e resultado

Foi realizada **uma síntese real curta**, isolada dos scripts cristãos, no Chrome headless do GitHub Actions, no site público `https://kokoroweb.app/`.

O texto utilizado foi uma frase técnica original de 74 caracteres, com fingerprint `080334bb6a03686b996284829618413ab113624ce07b1c5640974b55a9bc2c7c`. Não foi usado o roteiro Habacuque, o piloto Salmo 13, dados privados ou mídias do canal.

**Prova real obtida:**

| Medição | Valor observado |
|---|---|
| Site aberto | Sim |
| Idioma | Português (Brasil) selecionado |
| Voz | Alex (pm_alex) selecionada |
| Botão Generate | Acionado uma única vez |
| Áudio técnico | Elemento de áudio carregado no navegador |
| Duração pelo metadata HTML do áudio | **5,875 s** |
| Voice cache | `pm_alex.bin`, **522.240 bytes** |
| SHA-256 do arquivo lido do cache | **`0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a`** |
| Comparação com ONNX upstream | **MATCH** |
| Respostas de rede diretamente hasheadas | 0 |
| Recursos relacionados à engine/modelos observados | 12 |
| Avisos de inspeção | `voice_response_not_hashable` |
| WAV salvo/exportado | **Não** |
| Áudio aprovado para o canal | **Não** |
| Publicação | **Não autorizada** |

A tentativa de hashear diretamente uma resposta de rede não gerou prova; contudo, o **cache da mesma sessão que sintetizou o teste** continha `pm_alex.bin` com SHA-256 correspondente aos bytes da distribuição `onnx-community/Kokoro-82M-v1.0-ONNX`, validados anteriormente pela PR #31.

**Interpretação correta:** a síntese curta funcionou, e um arquivo de voz com identidade criptográfica oficial esteve presente no cache daquele navegador. Isso **não demonstra de maneira independente** qual objeto o mecanismo de inferência efetivamente consumiu, nem comprova identidade de todas as dependências, licenciamento integral, qualidade de pronúncia ou que uma próxima sessão será igual.

A duração foi obtida pelo metadata do player, **não por escuta humana nem por um WAV persistido**.

## Evidência rastreável

- Workflow com execução real: https://github.com/BORELLITO/corte-fino-engine/actions/runs/44179520750
- Commit executado: `781817eee77369739174fe24751a3111eb0af682`
- Artefato GitHub Actions: `vnc-kokoro-controlled-smoke-evidence` (ID `14371033576`, retenção de 14 dias)
- Arquivo `report.json` dentro do artefato: **1.723 bytes**; SHA-256 **`1b83c7dcdcf11c18241d20c572b72db286b3c4a1a38cdae45dc8ffa5acf9af37`**
- Contrato versionado de preservação: `contracts/kokoro_controlled_smoke_evidence_v1.json`
- Verificador: `agents/controlled_smoke_evidence.py`
- Execução em navegador: `agents/kokoro_controlled_smoke.py`
- Workflow one-shot: `.github/workflows/verbo-no-chao-controlled-tts-smoke.yml`

A evidência histórica fica versionada no código, pois o artefato expira, **sem redistribuir o binário de voz ou o áudio**. O contrato guarda explicitamente `historical_observation_only = true`.

## Integração com o motor

O pré-voo `agents/audio_preflight.py` agora valida esse contrato e registra:

- `historical_short_technical_smoke` com fonte, data, 5,875 s e SHA do cache;
- `historical_browser_cache_pm_alex_bin_sha256_matched = true`;
- `effective_inference_voice_asset_consumption_proven = false`;
- `audio_generated = false` — **para o episódio**, não para o teste;
- `publication_authorized = false`.

O coordenador `agents/team.py` exige o hash da prova histórica para aceitar relatórios desta camada, mas mantém o estado de operação em `BLOCKED` até os demais gates.

**Nenhum gate editorial ou jurídico é afrouxado por esta nova evidência.**

## Custos, riscos e repetição

O site informa que a primeira síntese pode transferir cerca de **92–326 MB** de pesos do modelo. Por isso a prova foi criada como **workflow separado**, executado uma vez na implementação, com limite de 8 minutos por job e 175 segundos de espera pela síntese; é possível relançá-lo explicitamente no GitHub Actions. Não há loop recorrente nem monitoramento diário.

O motor tem CI gratuito dentro das cotas do GitHub Actions, mas não presume minutos ilimitados nem ausência de cobrança fora de franquias. O site declara não cobrar por caractere ou exigir conta no fluxo público (https://kokoroweb.app/).

A sessão foi executada sem contas conectadas, e o relatório não armazena cookies, texto sensível, URLs com tokens, voz binária, vídeo ou WAV. **Não reproduzir ou publicar o áudio temporário sem revisão.**

## Pendências corretas após o avanço

1. Revisão teológica independente do roteiro E01 e aprovação de seu texto exato pelo proprietário.
2. Revisão de licenças/avisos do conjunto concreto de modelo, voz e dependências, sem presumir que termos comerciais condicionais do site liberam todos os componentes.
3. Primeiro áudio do roteiro E01 **somente após** os gates anteriores; nesse momento medir WAV real, qualidade, pausas, legibilidade e sincronia.
4. Montagem de vídeo e aprovação audiovisual independentes; publicação sempre exige autorização separada.
5. Integração das PRs empilhadas #26–#33 só depois de revisão e sem sobrescrever `bootstrap`; a PR #25 de provas físicas permanece independente.

Nenhuma das cinco pendências é automaticamente resolvida por um teste técnico de cinco segundos.
