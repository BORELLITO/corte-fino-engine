# Auditoria do primeiro clipe cloud — Salmo 13

Estado: `PARTIAL_DURABLE_ACCESS_BLOCKED_PENDING_MULTI_SHOT_AND_RIGHTS_LEDGER`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Origem e escopo

- Projeto: Verbo no Chão — piloto Salmo 13.
- Regra clean-room: nenhum conteúdo, mídia, identidade, prompt ou fluxo operacional do Because Of This Stories foi utilizado.
- A auditoria registra duas rotas independentes: geração simbólica LoreMotion e aquisição de stock licenciado Pexels.
- Nenhuma rota foi tratada como autorização automática de publicação.

## Rota LoreMotion observada anteriormente

- Superfície: LoreMotion, execução cloud via navegador gerenciado.
- Modelo: LTX 2.5, gratuito e ad-supported.
- Formato observado: vertical 9:16, 720p, 5 segundos.
- Prompt: paisagem contemplativa ao amanhecer, caminho junto a oliveiras, névoa, movimento lento de câmera, sem pessoas, texto, logotipos ou fala.
- URL direta do MP4 observada após a geração:
  https://videos.loremotion.com/videos/d005a3cb-6a93-461b-8c76-ed60b6d15a78.mp4
- O MP4 foi baixado pelo navegador gerenciado e transferido automaticamente para o editor cloud Free.ai.
- O editor confirmou duração de 5,0 s, dimensões 704×1280 e tamanho 9,5 MB, identificador de arquivo `a66c7185-952f-4427-ad31-940b41e47129`.
- Essa transferência comprovou transporte cloud entre serviços, mas não armazenamento durável sob controle do projeto nem vídeo final exportado.
- O arquivo LoreMotion permanece temporário e não está liberado para publicação.

## Rota Pexels persistida — S13-V01

- Página oficial: https://www.pexels.com/video/a-sunrise-over-a-city-with-fog-and-trees-18310302/
- A página foi validada como Free, 1080×1920, proporção 9:16 e duração exibida de aproximadamente 16 segundos.
- O download direto pelo navegador cloud expirou em duas tentativas, com timeouts de 30 e 120 segundos.
- Foi utilizada uma rota cloud alternativa de importação direta do arquivo oficial.
- A importação foi concluída com sucesso na biblioteca audiovisual.
- ID durável: `e4f8059a-5773-487d-8fb5-a769bf1dbf22`.
- URL persistente: https://cdn.creativeclaw.co/u/cfe41e70/videos/bda458db-8fe2-4f6f-bdeb-956db4dc48c9.mp4
- Inspeção técnica confirmada: MIME `video/mp4`, 1080×1920, duração exata de 17,045 segundos.
- O Pexels S13-V01 está apto para o lote de montagem, mas ainda depende do ledger final de direitos e da obtenção de múltiplos planos.
- Hash criptográfico não foi calculado nesta etapa.

## Limites encontrados

- O segundo clipe LoreMotion foi bloqueado após a primeira geração, com exigência de conta gratuita.
- Não foi criada conta nem utilizado login, pois isso exigiria identidade/credencial do proprietário.
- O Clipaist foi testado como alternativa sem cadastro; três tentativas foram recusadas pela fila congestionada e nenhum segundo MP4 foi entregue.
- O editor Free.ai confirmou ser um assistente de edição de clipe único, sem montagem multi-clipe completa.
- A geração/montagem paga do Creative Claw não foi acionada; a rota utilizada foi somente importação de arquivo público já existente.
- Não houve tentativa de contornar limites, criar contas, inserir credenciais ou pagar serviços.

## Direitos e monetização

- Pexels: licença pública gratuita para uso comercial sem atribuição obrigatória, sujeita às restrições de terceiros e da própria licença.
- LoreMotion: os Termos públicos consultados em 2026-11-17 declaram propriedade do conteúdo gerado, uso comercial, edição e redistribuição sem royalties/atribuição, sujeitos aos termos do modelo utilizado: https://loremotion.com/terms/
- Gate de direitos LoreMotion: `MODEL_PROVIDER_TERMS_PENDING`.
- Gate de direitos Pexels: página e licença de origem verificadas; registro específico do asset e hash ainda pendentes.
- Nenhum clipe está autorizado para publicação isoladamente.
- Não houve gasto, pagamento ou publicação.

## Próximo gate automático

1. importar pelo menos mais três candidatos compatíveis pela rota cloud persistente;
2. inspecionar proporção, duração, composição e área segura de legenda;
3. registrar fonte, autor, licença, identificador durável e hash quando disponível;
4. fechar o lote multi-shot;
5. combinar narração, trilha, legendas e montagem;
6. executar QA audiovisual;
7. entregar somente após o estado `READY_FOR_OWNER_APPROVAL`.
