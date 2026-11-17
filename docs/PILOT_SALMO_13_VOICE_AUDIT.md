# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M em execução cloud pelo navegador gerenciado**, português brasileiro.

O POCO X8 Pro Max será usado somente como interface de controle. Não haverá requisito de PC, instalação local, processamento local no telefone ou runtime local para operar o canal.

Candidato-base selecionado: **pm_alex**, exibido no Kokoro Web como **Alex**.

## Resultado do benchmark

As três vozes pt-BR passaram no smoke test simplificado:

- pm_alex;
- pm_santa;
- pf_dora.

O trecho canônico completo, com reticências, foi recusado pelo runtime com: “No readable Brazilian Portuguese · Português text was found.”

Isso não autoriza remover acentos nem alterar o roteiro. O texto editorial continua canônico e intacto.

A solução validada é uma camada de pronúncia separada. Para o roteiro completo, o texto foi dividido em oito segmentos, preservando a reticência editorial entre os segmentos 2 e 3:

1. “Tem dias em que o silêncio parece uma resposta.”
2. “Você ora, espera, olha para o relógio.”
3. “E nada muda.”
4. “Talvez você esteja cansado de parecer forte. Cansado de explicar o que sente. Cansado de esperar uma mudança que não chega.”
5. “O Salmo 13 nasce exatamente nesse lugar: uma oração de lamento, feita por alguém que se sente esquecido, mas ainda decide falar com Deus.”
6. “Davi não transforma a dor em aparência de vitória. Ele pergunta, insiste e apresenta sua angústia. A Bíblia não trata esse lamento como falta de fé. Ela mostra que a dor também pode ser levada à presença de Deus.”
7. “Hoje, talvez a sua oração não precise ser bonita. Pode ser honesta. Diga o que está pesado. Procure apoio. Continue dando o próximo passo possível, sem inventar certezas que você ainda não tem.”
8. “A espera continua sendo difícil, mas o silêncio não precisa ser o fim da esperança. Você pode atravessar este momento um dia de cada vez.”

Os oito segmentos foram gerados na sessão cloud com **pm_alex/Alex**, em WAV 24 kHz, velocidade 1.0x. Os oito controles de download foram acionados. Os cards de áudio ficaram visíveis na ordem 1–8.

A persistência dos arquivos fora da sessão ainda não foi comprovada; por isso, eles não são considerados ativos de produção.

## Arquitetura operacional cloud-only

1. O motor mantém o roteiro editorial canônico.
2. O motor deriva uma camada de pronúncia somente para o TTS quando o runtime rejeita pontuação ou reticências.
3. O navegador cloud gerenciado gera cada bloco como WAV.
4. Cada bloco é revisado e rastreado por segmento.
5. A persistência/montagem do áudio ocorre na pipeline cloud do projeto somente após confirmação dos arquivos.
6. Direitos, inteligibilidade, sincronização e revisão continuam bloqueando publicação até aprovação.

O telefone controla a sessão e a aprovação; não hospeda o motor nem executa PyTorch, ONNX ou outro runtime local.

## Tentativas e limites

A instalação isolada do runtime oficial PyTorch foi tentada fora do repositório. O processo foi encerrado pelo ambiente com status 137 por consumo de memória. Esse registro é histórico e não altera a arquitetura: execução local não é requisito do canal.

## Estado atual

- direção: **APROVADA**;
- candidato-base: **pm_alex / Alex**;
- smoke test simplificado: **PASS nas três vozes**;
- texto canônico combinado: **BLOCKED pelo runtime**;
- texto canônico segmentado: **PASS**;
- roteiro completo segmentado: **8/8 GERADOS**;
- formato: **WAV 24 kHz**;
- processamento local no PC/telefone: **NÃO REQUERIDO**;
- persistência dos arquivos: **não comprovada**;
- duração/tamanho/hash dos WAVs: **pendentes**;
- áudio de produção: **não autorizado**;
- publicação: **não autorizada**.

## Próximo gate

1. Confirmar a presença dos oito WAVs na superfície cloud.
2. Registrar duração, tamanho e SHA-256 por segmento.
3. Montar os oito WAVs na ordem canônica.
4. Revisar a inteligibilidade, pausas e transições.
5. Auditar licença do modelo, voz e runtime para uso comercial.
6. Só então promover pm_alex a voz definitiva de produção.
7. Manter publicação bloqueada.

## Evidências consultadas

- CLI oficial com exemplo pm_alex: https://github.com/hexgrad/kokoro/blob/main/kokoro/__main__.py
- Lista oficial de vozes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE
- Sessão de execução: https://kokoroweb.app/#demoContainer

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
