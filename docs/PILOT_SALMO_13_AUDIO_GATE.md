# Gate de áudio — piloto Salmo 13

Estado: PERSISTED_ASSEMBLED_MIXED_PREVIEW_READY_PENDING_EXACT_VOICE_RIGHTS
Data: 2026-11-17 (America/Sao_Paulo)

## Decisão canônica

A rota oficial de narração do piloto é o **Kokoro-82M no Kokoro Web**, executado em navegador cloud gerenciado:

- página: https://kokoroweb.app/#demoContainer
- idioma: Português (Brazil)
- voz-base: `pm_alex` — exibida na interface como **Alex**
- formato: WAV 24 kHz
- velocidade inicial: 1.0x
- limite observado do site: 2.000 caracteres por entrada
- conta: não necessária
- cobrança por caractere: não aplicada na rota web observada

O POCO X8 Pro Max serve apenas como interface de controle. O processamento ocorre na sessão de navegador cloud, sem instalação, PyTorch, ONNX ou processamento no telefone.

## Correção de conflito

Uma versão anterior deste documento apontou Creative Claw/ElevenLabs como rota principal. Isso foi corrigido porque o branch canônico já contém uma decisão de voz aprovada e um benchmark real do Kokoro Web. Creative Claw não é dependência do piloto e não deve ser usado para substituir silenciosamente a rota Kokoro.

## Execução comprovada nesta etapa

- Idioma selecionado: Português (Brazil).
- Voz selecionada: Alex, correspondente à baseline `pm_alex`.
- Velocidade: 1.0x.
- Formato observado: WAV 24 kHz.
- Segmentos gerados na sessão: **8 de 8**.
- Os oito controles “Download WAV” foram acionados.
- A página exibiu os oito cards de áudio na ordem correta.
- Nenhum crédito ou compra foi utilizado.
- A sessão cloud foi preservada para revisão.

Estado de persistência: **PENDENTE**. O navegador confirmou a geração e disponibilizou os links blob, mas ainda não foi comprovado que os oito arquivos foram recuperados como ativos persistentes da pipeline. Portanto, não há áudio de produção liberado.

## Roteiro e camada de pronúncia

O roteiro editorial aprovado permanece em `tests/fixtures/salmo_13_script.json`. A divisão abaixo altera somente o texto enviado ao TTS; não altera roteiro, legenda ou significado:

1. `Tem dias em que o silêncio parece uma resposta.`
2. `Você ora, espera, olha para o relógio.`
3. `E nada muda.`
4. `Talvez você esteja cansado de parecer forte. Cansado de explicar o que sente. Cansado de esperar uma mudança que não chega.`
5. `O Salmo 13 nasce exatamente nesse lugar: uma oração de lamento, feita por alguém que se sente esquecido, mas ainda decide falar com Deus.`
6. `Davi não transforma a dor em aparência de vitória. Ele pergunta, insiste e apresenta sua angústia. A Bíblia não trata esse lamento como falta de fé. Ela mostra que a dor também pode ser levada à presença de Deus.`
7. `Hoje, talvez a sua oração não precise ser bonita. Pode ser honesta. Diga o que está pesado. Procure apoio. Continue dando o próximo passo possível, sem inventar certezas que você ainda não tem.`
8. `A espera continua sendo difícil, mas o silêncio não precisa ser o fim da esperança. Você pode atravessar este momento um dia de cada vez.`

As pausas narrativas entre os blocos 2 e 3 representam visualmente a reticência do texto editorial original. Nenhuma acentuação deve ser removida.

## Travas

- Não trocar `pm_alex` sem registrar nova decisão e novo benchmark.
- Não usar conteúdo, assets, prompts ou contratos do Because Of This Stories.
- Não declarar o áudio como ativo de produção enquanto o download/persistência e o hash não forem comprovados.
- Cada WAV precisa de segmento, duração, hash e revisão auditiva.
- A montagem só avança depois de confirmar a ordem dos blocos, inteligibilidade, pausas, direitos do modelo/voz e sincronização das legendas.
- Publicação permanece bloqueada.

## Próximo gate

1. Recuperar e confirmar os oito WAVs na superfície cloud.
2. Registrar duração, tamanho e SHA-256 de cada segmento.
3. Montar os segmentos na ordem canônica.
4. Auditar duração total, transições, inteligibilidade e hash.
5. Só então sincronizar imagens, trilha e legendas.


## Evidência do master atual

- Locução contínua: 60,25 s; SHA-256: 946ab6c5ea4acec6b1332161bfae444735e0574e576d260214ded1fdd7cd03e0.
- Trilhas: trilha original procedural sem samples externos; SHA-256: 906b26dc2bad2312e07c8a77c5e9d98ade7fa78d712d767f3106d32178a6eda9.
- Master: salmo13_pilot_master_v1.mp4; 1080x1920; SHA-256: 363283d1872738690abe19d388fdc489c3085bbb5584ce009812822a2170c43c.
- Estado de publicação: BLOCKED.