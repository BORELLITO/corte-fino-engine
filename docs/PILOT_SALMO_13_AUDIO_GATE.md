# Gate de áudio — piloto Salmo 13

Estado: KOKORO_TTS_CLOUD_ROUTE_ACTIVE_PENDING_AUDIO_PERSISTENCE
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

## Evidência já existente

- As vozes `pm_alex`, `pm_santa` e `pf_dora` passaram no smoke test pt-BR.
- `pm_alex` foi selecionada como baseline provisória.
- O texto completo com reticência foi recusado pelo runtime.
- A camada de pronúncia segmentada passou mantendo o texto editorial canônico intacto.
- Três blocos curtos foram anteriormente gerados em WAV 24 kHz; a persistência desses downloads ainda não havia sido comprovada.
- Nesta execução, a primeira amostra foi regenerada com Alex e está visível na sessão cloud; a persistência do arquivo ainda aguarda confirmação.

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

1. Gerar os oito segmentos na sessão Kokoro Web com `pm_alex`.
2. Confirmar que cada WAV pode ser baixado e recuperado na superfície cloud.
3. Montar os segmentos na ordem canônica.
4. Auditar duração, transição, inteligibilidade e hash.
5. Só então sincronizar imagens, trilha e legendas.
