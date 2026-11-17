# Auditoria de fonte — Salmo 13

## Veredito

Para o piloto, a rota segura é:

- citar a referência Salmo 13;
- usar paráfrase original;
- não reproduzir versos literalmente;
- manter a tradução sem seleção até a licença da edição ser confirmada.

## Motivo

A edição NAA exibida pela SBB possui aviso de copyright. A SBB também informa que a edição de 2010 da Tradução Brasileira recebeu alterações em relação à edição de 1917. Embora um registro da Digital Bible Library classifique a edição de 1917 como domínio público, outras páginas identificam a versão TB 1917/2010 com direitos reservados.

Essa divergência é suficiente para bloquear o uso literal da edição de 2010 em conteúdo monetizado.

## Decisão operacional

O motor deve tratar a fonte como:

- source_mode: reference_and_paraphrase;
- verbatim_quote_status: BLOCKED_PENDING_LICENSE;
- selected_translation: null.

A citação literal só poderá ser liberada depois de uma fonte de direitos inequívoca e compatível com uso comercial.

Esta decisão não impede a produção de um roteiro original fundamentado no Salmo 13. Ela apenas impede que uma tradução específica seja reproduzida sem autorização comprovada.
