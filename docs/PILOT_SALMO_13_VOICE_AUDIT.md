# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M local, português brasileiro**.

Candidato-base selecionado para benchmark: **pm_alex**.

## Resultado do benchmark

As três vozes pt-BR foram geradas com sucesso no smoke test usando o mesmo trecho simplificado:

- pm_alex;
- pm_santa;
- pf_dora.

O navegador rejeitou o trecho canônico com acentos e pontuação, exibindo: “No readable Brazilian Portuguese · Português text was found.”

Isso é um bloqueio do runtime de navegador para produção, não uma autorização para remover acentos do roteiro. O texto bíblico e a narração canônica devem preservar ortografia, contexto e naturalidade.

## Próxima correção necessária

1. Testar o runtime oficial local com o texto canônico.
2. Se necessário, criar uma camada de pronúncia separada do texto exibido, preservando o roteiro original.
3. Comparar novamente as três vozes com o mesmo trecho canônico.
4. Escolher o voice ID definitivo somente após ouvir a pronúncia real.
5. Confirmar a licença do pacote/voz e das dependências.
6. Manter publicação bloqueada.

## Estado atual

- direção: **APROVADA**;
- candidato-base: **pm_alex**;
- smoke test simplificado: **PASS nas três vozes**;
- texto canônico no runtime de navegador: **BLOCKED**;
- voice ID definitivo: **pendente**;
- áudio de produção: **não gerado**;
- publicação: **não autorizada**.

## Evidências consultadas

- CLI oficial com exemplo pm_alex: https://github.com/hexgrad/kokoro/blob/main/kokoro/__main__.py
- Lista oficial de vozes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
