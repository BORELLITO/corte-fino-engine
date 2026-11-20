# Pipeline Driver v1

`contracts/e01_pipeline_v1.json` declara a ordem canônica das etapas do episódio e, para cada uma, o contrato de evidência e as condições de DONE. `python -m orchestrator.pipeline` lê as evidências (somente leitura, fail-closed) e informa o estado de cada etapa (`DONE`, `READY`, `WAITING`, `HUMAN_ACTION`), a próxima etapa e o workflow a disparar.

Garantias: evidência ausente, corrompida, fora da raiz ou com tipo diferente (ex.: `1` no lugar de `true`) nunca conta como DONE; `publication` é sempre `human_only` e o driver nunca declara `PUBLISHED`.

Próximos passos da automação total: (1) dispatcher que dispare o workflow da etapa READY com token; (2) fazer cada workflow gravar o contrato de evidência por commit, sem edição manual; (3) provedor que materialize o pacote do `runflow`.
