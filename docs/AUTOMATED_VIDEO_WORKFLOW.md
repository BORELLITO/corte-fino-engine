# Fluxo automático de produção de vídeo — Verbo no Chão

## Decisão aprovada

O proprietário não deverá conduzir manualmente a produção. Ao solicitar o próximo vídeo, o coordenador operacional executará automaticamente as etapas seguras e autorizadas na infraestrutura cloud e entregará o vídeo renderizado somente após validação interna de todos os pilares, sem exigir revisão de qualidade do proprietário. A publicação continua sujeita a autorização específica.

Este fluxo é independente e clean-room: não utiliza conteúdo, mídia, identidade, prompts, contratos, vozes, assets ou fluxo operacional do Because Of This Stories.

## Fluxo oficial

`PEDIDO → SELEÇÃO INTELIGENTE → REVISÃO SEMÂNTICA IA → PRODUÇÃO CLOUD → QA INTERNO → VÍDEO VALIDADO → AUTORIZAÇÃO DE PUBLICAÇÃO SEPARADA`

### 1. Pedido

O proprietário solicita o próximo vídeo.

### 2. Seleção inteligente

O motor escolhe, com base no briefing e nos gates:

- melhor tema e recorte bíblico;
- roteiro e estrutura de retenção;
- imagens e clipes coerentes;
- voz e configuração de narração;
- trilha e efeitos permitidos;
- composição, legendas e identidade visual;
- título, descrição, capa e metadados preliminares.

### 3. Produção cloud

O motor executa geração, edição, sincronização, montagem e renderização sem exigir PC ou processamento no POCO.

### 4. QA interno

Antes de entregar, o motor verifica:

- fidelidade e contexto bíblico;
- originalidade e coerência narrativa;
- áudio, voz, música e sincronização;
- imagens pertinentes à narração;
- legendas e segurança visual;
- direitos e licenças;
- elegibilidade de monetização;
- especificações de exportação;
- ausência de regressões;
- **não repetição de clipes**.

### 5. Entrega final

A entrega ao proprietário deve conter o vídeo renderizado, o resumo de qualidade, o status de direitos e os metadados recomendados.

### 6. Aprovação

O proprietário **não precisa revisar nem aprovar o roteiro ou o vídeo final**. O motor só pode declarar o vídeo validado após QA real de mídia, som, direitos e contexto. **Publicação é uma ação separada, expressamente autorizada pelo proprietário**, e nunca é inferida do QA interno.

## Invariante editorial — zero repetição de clipes

- O mesmo clipe ou asset de origem só pode aparecer uma vez no mesmo vídeo final.
- Repetir o arquivo com outro crop, zoom, velocidade, espelhamento, reversão, cor, máscara ou enquadramento continua sendo repetição e é proibido.
- Cada plano deve registrar `asset_id`, URL de origem e intervalo temporal utilizado.
- O mesmo intervalo temporal não pode ser reutilizado em outro plano.
- Se duas entradas vierem do mesmo arquivo de origem, o QA deve tratá-las como repetição potencial e bloquear até comprovar que são assets e trechos realmente distintos.
- Qualquer violação bloqueia `READY_FOR_PUBLICATION_AUTHORIZATION`.
- Reutilização em vídeos diferentes não é automaticamente proibida, mas deverá ser evitada quando criar sensação de reciclagem; o motor deve priorizar assets novos e manter histórico de uso.

## Estados obrigatórios

- `PLANNED`: fluxo definido, sem produção iniciada.
- `IN_PROGRESS`: produção cloud em andamento.
- `BLOCKED`: uma dependência real impede uma entrega íntegra; o coordenador registra causa, evidência e única ação indispensável.
- `READY_FOR_PUBLICATION_AUTHORIZATION`: vídeo renderizado e auditado sobre bytes reais, com todos os direitos, som, captions, originalidade, metadados e arte verificados automaticamente.
- `PUBLISHED`: publicação confirmada somente após autorização específica e evidência da plataforma.

Um clipe isolado, uma prévia ou um arquivo transferido entre serviços não pode ser apresentado como vídeo final. Se qualquer gate essencial falhar, o estado permanece `BLOCKED` e a entrega deve declarar explicitamente o que foi comprovado e o que ainda não foi comprovado.

## Regra de autonomia

Não haverá perguntas intermediárias sobre microetapas que já estejam cobertas pelo escopo. O coordenador deve decidir e executar o melhor caminho seguro, registrando bloqueios reais e evitando transferir trabalho operacional desnecessário ao proprietário.

## Limites

Continuam exigindo autorização específica:

- publicação;
- gastos;
- pagamentos;
- exclusões;
- alteração de permissões;
- transmissão de dados sensíveis;
- ações irreversíveis;
- qualquer mudança fora do escopo aprovado.

O estado após a renderização depende dos gates: `BLOCKED` até haver todos os arquivos reais e licenças; após aprovação interna completa, `READY_FOR_PUBLICATION_AUTHORIZATION`, nunca `PUBLISHED` automaticamente. O escopo desta revisão vale apenas para vídeos novos, não para o piloto congelado.


## Integração bloqueante do motor

Este fluxo é executável somente quando o manifesto em contracts/pilot_salmo_13_master.json passa por engine/quality_gates.py. A trilha musical agora é obrigatória: pode ser original procedural sem samples externos ou licenciada com URL de licença. A narração precisa estar persistida, hasheada e em pt-BR/Kokoro-82M. Direitos pendentes permitem apenas PREVIEW_READY; não permitem publicação. A CI verbo-no-chao-gates.yml executa os testes de repetição, cloud-only, música, publicação e uso legado.

## Revisão de autonomia — episódios novos (17/11/2026)

O motor usa os doze pilares documentados em `contracts/autonomous_editorial_policy_v1.json` e `docs/AUTONOMOUS_EDITORIAL_QA_V1.md`. A análise interna de roteiro depende de revisão semântica genuína e fonte/hash; o CI apenas valida o recibo, não é um modelo de linguagem. A aprovação editorial do roteiro E01 é **somente interna**, não aprova o uso comercial da voz ou um arquivo de vídeo inexistente. O piloto Salmo 13 não é promovido automaticamente. O usuário não precisa inspecionar o vídeo acabado, mas deve autorizar a eventual publicação como ação separada.
