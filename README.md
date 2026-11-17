# Verbo no Chão

Motor audiovisual cristão original.

Estado: CLEAN_BOOTSTRAP

Esta branch é uma base limpa e independente. Nenhum conteúdo operacional de projetos anteriores é utilizado.

## Engine lock

A operação atual usa exclusivamente o motor Verbo no Chão. As regras bloqueantes estão em docs/ENGINE_LOCK.md, os contratos em contracts/, o validador em engine/quality_gates.py e os testes em tests/test_verbo_no_chao_gates.py. A CI verbo-no-chao-gates.yml deve passar antes de qualquer promoção de estado.