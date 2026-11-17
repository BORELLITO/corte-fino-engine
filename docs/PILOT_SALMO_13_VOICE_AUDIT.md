# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M em execução cloud pelo navegador gerenciado**, português brasileiro.

O POCO X8 Pro Max será usado somente como interface de controle. Não haverá requisito de PC, instalação local, processamento local no telefone ou runtime local para operar o canal.

Candidato-base selecionado para benchmark: **pm_alex**.

## Resultado do benchmark

As três vozes pt-BR passaram no smoke test simplificado:

- pm_alex;
- pm_santa;
- pf_dora.

O trecho canônico completo, com reticências, foi recusado pelo runtime com: “No readable Brazilian Portuguese · Português text was found.”

Isso não autoriza remover acentos nem alterar o roteiro. O texto editorial continua canônico e intacto.

A solução validada foi uma camada de pronúncia separada, com três blocos curtos:

1. “Tem dias em que o silêncio parece uma resposta.”
2. “Você ora, espera, olha para o relógio.”
3. “E nada muda.”

Os três blocos foram gerados em WAV 24 kHz com **pm_alex** na sessão de navegador cloud. O segundo e o terceiro bloco representam a mesma frase editorial original, preservando visualmente a reticência durante a montagem.

## Arquitetura operacional cloud-only

1. O motor mantém o roteiro editorial canônico.
2. O motor deriva uma camada de pronúncia somente para o TTS quando o runtime rejeita pontuação ou reticências.
3. O navegador cloud gerenciado gera cada bloco como WAV.
4. Os blocos são baixados e rastreados por segmento dentro da sessão cloud.
5. A montagem do áudio ocorre na pipeline cloud do projeto.
6. Direitos, inteligibilidade, sincronização e revisão continuam bloqueando publicação até aprovação.

O telefone controla a sessão e a aprovação; não hospeda o motor nem executa PyTorch, ONNX ou outro runtime local.

## Tentativas e limites

A instalação isolada do runtime oficial PyTorch foi tentada fora do repositório. O processo foi encerrado pelo ambiente com status 137 por consumo de memória. Esse registro é histórico e não altera a arquitetura: execução local não é requisito do canal.

## Estado atual

- direção: **APROVADA**;
- candidato-base: **pm_alex**;
- smoke test simplificado: **PASS nas três vozes**;
- texto canônico combinado: **BLOCKED pelo runtime**;
- texto canônico segmentado: **PASS com camada de pronúncia**;
- processamento local no PC/telefone: **NÃO REQUERIDO**;
- voice ID definitivo: **pendente de auditoria de direitos e revisão auditiva**;
- amostras WAV: **geradas para avaliação**;
- áudio de produção: **não autorizado**;
- publicação: **não autorizada**.

## Próximo gate

1. Montar os três WAVs na ordem canônica.
2. Revisar a inteligibilidade, pausas e transição entre blocos.
3. Auditar licença da voz, runtime e dependências para uso comercial.
4. Só então decidir se pm_alex é promovida a voz definitiva.
5. Manter publicação bloqueada.

## Evidências consultadas

- CLI oficial com exemplo pm_alex: https://github.com/hexgrad/kokoro/blob/main/kokoro/__main__.py
- Lista oficial de vozes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
