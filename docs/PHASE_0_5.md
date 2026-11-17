# Fase 0.5 — Fixture oficial do piloto

Resultado: INTERNAL_VALIDATED

Foi criado um fixture estrutural do piloto do Salmo 13 para testar o fluxo completo sem produzir mídia.

O fixture:

- passa pelo orquestrador em modo fixture_mode;
- usa ativos sintéticos marcados como FIXTURE_ONLY;
- não afirma licença comercial real;
- não valida uma tradução bíblica definitiva;
- bloqueia quando o modo fixture é removido;
- não permite publicação.

Validação:

- gate Clean-Room: PASS;
- testes unitários: 22 aprovados, 0 falhas;
- fixture JSON: válido;
- runtime sem dependências externas.

Ainda não autorizado:

- geração de voz;
- seleção de imagens reais;
- trilha final;
- renderização;
- publicação.
