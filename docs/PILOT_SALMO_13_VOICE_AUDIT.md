# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M em execução cloud pelo navegador gerenciado**, português brasileiro.

O POCO X8 Pro Max será usado somente como interface de controle. Não haverá requisito de PC, instalação local, processamento local no telefone ou runtime local para operar o canal.

Candidato-base selecionado para benchmark: **pm_alex**.

## Resultado do benchmark

As três vozes pt-BR foram geradas com sucesso no smoke test usando o mesmo trecho simplificado:

- pm_alex;
- pm_santa;
- pf_dora.

O navegador rejeitou o trecho canônico com acentos e pontuação, exibindo: “No readable Brazilian Portuguese · Português text was found.”

Isso é um bloqueio do fluxo de entrada desse runtime de navegador, não uma autorização para remover acentos do roteiro. O texto bíblico e a narração canônica devem preservar ortografia, contexto e naturalidade.

## Arquitetura operacional cloud-only

1. O motor prepara e segmenta o roteiro canônico em blocos curtos, sem alterar o texto editorial.
2. O navegador cloud gerenciado abre o gerador de voz.
3. Cada bloco é enviado e gerado como WAV em sessão controlada.
4. Os blocos são revisados e rastreados por segmento.
5. A montagem do áudio ocorre na pipeline cloud do projeto.
6. Somente depois dos gates de direitos, precisão e qualidade o material poderá seguir para vídeo e publicação.

O telefone controla a sessão e a aprovação; não hospeda o motor nem precisa executar PyTorch, ONNX ou outro runtime local.

## Tentativas e limites

A instalação isolada do runtime oficial PyTorch foi tentada fora do repositório. O processo foi encerrado pelo ambiente com status 137 por consumo de memória. Esse resultado não altera a arquitetura: execução local não é requisito do canal e a tentativa histórica permanece apenas como evidência de que não devemos depender dela neste ambiente.

## Próxima correção necessária

1. Segmentar o texto canônico em blocos naturais curtos no navegador cloud.
2. Gerar cada bloco preservando acentos, pontuação e texto exibido.
3. Se um bloco continuar sendo recusado, registrar o erro e criar uma camada de pronúncia separada, sem substituir o roteiro visual/editorial.
4. Comparar novamente as três vozes no mesmo conjunto de blocos.
5. Confirmar a licença da voz, do runtime e das dependências antes de qualquer áudio de produção.
6. Manter publicação bloqueada.

## Estado atual

- direção: **APROVADA**;
- candidato-base: **pm_alex**;
- smoke test simplificado: **PASS nas três vozes**;
- texto canônico no runtime de navegador: **BLOCKED**;
- processamento local no PC/telefone: **NÃO REQUERIDO**;
- voice ID definitivo: **pendente**;
- áudio de produção: **não gerado**;
- publicação: **não autorizada**.

## Evidências consultadas

- CLI oficial com exemplo pm_alex: https://github.com/hexgrad/kokoro/blob/main/kokoro/__main__.py
- Lista oficial de vozes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
