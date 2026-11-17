# Verbo no Chão — Engine Lock

## Fonte canônica

A branch de operação do canal é verbo-no-chao/bootstrap. Esta documentação, os contratos em contracts/, o validador em engine/ e os testes em tests/ formam a fonte de verdade versionada.

O branch main permanece histórico e congelado. O Because Of This Stories é somente referência externa e não pode ser modificado nem importar conteúdo para este motor.

## Invariantes que bloqueiam a produção

1. O projeto é clean-room: nenhum asset, prompt, voz, contrato, identidade ou fluxo operacional dos projetos antigos pode entrar.
2. A execução é cloud-only. O POCO X8 Pro Max controla a sessão; não hospeda o runtime.
3. Cada vídeo precisa de um manifesto válido antes da renderização final.
4. O mesmo asset de origem nunca pode aparecer duas vezes no mesmo vídeo. Crop, zoom, espelhamento, reversão, velocidade ou cor não criam um asset novo.
5. Cada asset precisa de origem, hash SHA-256, intervalo temporal e estado de direitos.
6. Narração, trilha, legendas, vídeo e saída precisam ter hashes/estado verificável.
7. Trilha ausente, sem origem/licença ou sem ducking da voz bloqueia.
8. Legenda ausente, dessincronizada ou fora da área segura bloqueia.
9. Direitos pendentes permitem somente PREVIEW_READY; nunca permitem publicação.
10. publication_authorized permanece false até aprovação explícita e gates de direitos/monetização liberados.
11. Nenhum arquivo pode ser apresentado como final se for apenas clipe, prévia, transferência ou render não validado.
12. Falha de qualquer gate mantém o estado BLOCKED.

## Estados

- PLANNED: plano criado, produção não iniciada.
- IN_PROGRESS: produção cloud em andamento.
- BLOCKED: dependência ou gate falhou.
- PREVIEW_READY: prévia íntegra para revisão; ainda não publicável.
- READY_FOR_OWNER_APPROVAL: todos os gates internos e direitos passaram; aguarda aprovação explícita.
- PUBLISHED: publicação confirmada com evidência externa após autorização.
- REJECTED: revisão rejeitada; não pode ser promovida automaticamente.

## Fluxo obrigatório

PEDIDO → BRIEFING → ROTEIRO → FONTES → VOZ → TRILHA → TIMELINE → LEGENDAS → QA → MANIFESTO → PREVIEW_READY/READY_FOR_OWNER_APPROVAL → APROVAÇÃO → PUBLICAÇÃO AUTORIZADA

Não existe caminho alternativo que salte a ordem. O coordenador pode executar etapas seguras automaticamente, mas não pode pular gates.

## Travas anti-regressão

- Toda mudança relevante deve ocorrer em branch separada ou commit identificável.
- O validador deve falhar fechado: erro, campo ausente ou estado desconhecido bloqueia.
- Os testes devem cobrir pass, repetição, ausência de música, uso legado e tentativa de publicação.
- Uma decisão nova substitui a anterior somente quando registrada em contrato e changelog.
- Documentação não substitui teste executável.
