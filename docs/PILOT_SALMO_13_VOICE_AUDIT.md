# Auditoria de voz — piloto Salmo 13

## Decisão

Direção aprovada: **Kokoro-82M local, português brasileiro**.

A aprovação é da direção técnica, não de um voice ID específico. O voice ID permanece pendente até a verificação do pacote exato.

## Por que esta direção venceu

- custo recorrente potencialmente zero em execução local;
- modelo aberto com licença Apache 2.0 declarada pelo projeto;
- suporte a português brasileiro;
- possibilidade de controle local do áudio, sem depender de uma API paga para cada roteiro.

## Travas antes da geração

1. Selecionar um voice ID pt-BR específico.
2. Confirmar a licença do pacote/voz exato.
3. Auditar as dependências de inferência e seus avisos de licença.
4. Fazer benchmark no ambiente disponível antes de incorporar o runtime.
5. Gerar uma amostra curta e revisar pronúncia, naturalidade, ritmo e emoção.
6. Manter publicação bloqueada até o gate de direitos e QA audiovisual.

## Estado atual

- direção: **APROVADA**;
- voice ID: **não selecionado**;
- áudio: **não gerado**;
- publicação: **não autorizada**.

## Evidências consultadas

- Repositório oficial: https://github.com/hexgrad/kokoro
- Licença oficial: https://github.com/hexgrad/kokoro/blob/main/LICENSE
- Modelo oficial: https://huggingface.co/hexgrad/Kokoro-82M

A licença Apache do modelo não elimina a necessidade de auditar a voz específica, o runtime e as dependências antes do uso comercial.
