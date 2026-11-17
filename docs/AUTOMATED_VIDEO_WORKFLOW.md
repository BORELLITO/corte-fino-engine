# Fluxo automático de produção de vídeo — Verbo no Chão

## Decisão aprovada

O proprietário não deverá conduzir manualmente a produção. Ao solicitar o próximo vídeo, o coordenador operacional executará automaticamente as etapas seguras e autorizadas na infraestrutura cloud e entregará o vídeo renderizado para aprovação final.

Este fluxo é independente e clean-room: não utiliza conteúdo, mídia, identidade, prompts, contratos, vozes, assets ou fluxo operacional do Because Of This Stories.

## Fluxo oficial

`PEDIDO → SELEÇÃO INTELIGENTE → PRODUÇÃO CLOUD → QA INTERNO → VÍDEO PRONTO → APROVAÇÃO DO PROPRIETÁRIO`

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

O proprietário aprova ou rejeita o resultado final. A aprovação do vídeo não equivale automaticamente à autorização de publicação.

## Invariante editorial — zero repetição de clipes

- O mesmo clipe ou asset de origem só pode aparecer uma vez no mesmo vídeo final.
- Repetir o arquivo com outro crop, zoom, velocidade, espelhamento, reversão, cor, máscara ou enquadramento continua sendo repetição e é proibido.
- Cada plano deve registrar `asset_id`, URL de origem e intervalo temporal utilizado.
- O mesmo intervalo temporal não pode ser reutilizado em outro plano.
- Se duas entradas vierem do mesmo arquivo de origem, o QA deve tratá-las como repetição potencial e bloquear até comprovar que são assets e trechos realmente distintos.
- Qualquer violação bloqueia `READY_FOR_OWNER_APPROVAL`.
- Reutilização em vídeos diferentes não é automaticamente proibida, mas deverá ser evitada quando criar sensação de reciclagem; o motor deve priorizar assets novos e manter histórico de uso.

## Estados obrigatórios

- `PLANNED`: fluxo definido, sem produção iniciada.
- `IN_PROGRESS`: produção cloud em andamento.
- `BLOCKED`: uma dependência real impede uma entrega íntegra; o coordenador registra causa, evidência e única ação indispensável.
- `READY_FOR_OWNER_APPROVAL`: vídeo renderizado, QA interno concluído e direitos com status compatível.
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

O estado padrão após a renderização é `READY_FOR_OWNER_APPROVAL`, nunca `PUBLISHED`.
