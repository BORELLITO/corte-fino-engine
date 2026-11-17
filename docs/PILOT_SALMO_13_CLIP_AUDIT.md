# Auditoria do primeiro clipe cloud — Salmo 13

Estado: `BLOCKED_PENDING_DURABLE_ASSET_AND_MULTI_SHOT_ACCESS`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Origem e escopo

- Projeto: Verbo no Chão — piloto Salmo 13.
- Regra clean-room: nenhum conteúdo, mídia, identidade, prompt ou fluxo operacional do Because Of This Stories foi utilizado.
- Superfície principal: LoreMotion, execução cloud via navegador gerenciado.
- Modelo: LTX 2.5, gratuito e ad-supported.
- Formato observado: vertical 9:16, 720p, 5 segundos.
- Prompt: paisagem contemplativa ao amanhecer, caminho junto a oliveiras, névoa, movimento lento de câmera, sem pessoas, texto, logotipos ou fala.
- Status observado: render concluído.

## Evidência observada

- URL direta do MP4 observada após a geração:
  https://videos.loremotion.com/videos/d005a3cb-6a93-461b-8c76-ed60b6d15a78.mp4
- O MP4 foi baixado pelo navegador gerenciado e transferido automaticamente para o editor cloud Free.ai.
- O editor confirmou o recebimento mostrando duração de 5,0 s, dimensões 704×1280 e tamanho 9,5 MB, identificador de arquivo `a66c7185-952f-4427-ad31-940b41e47129`.
- Essa transferência comprova o transporte cloud entre serviços, mas não equivale a armazenamento durável sob controle do projeto nem a um vídeo final exportado.
- O arquivo baixado continua tratado como entrega temporária até existir armazenamento cloud durável validado.

## Limite encontrado

- O segundo clipe foi preparado automaticamente com o mesmo padrão visual, mas o LoreMotion bloqueou novas gerações anônimas após o primeiro vídeo e exibiu a exigência de conta gratuita.
- Não foi criada conta nem utilizado login, pois isso exigiria uma identidade/credencial do proprietário que não está disponível nem autorizada para ser inferida.
- O Clipaist foi testado como alternativa sem cadastro; três tentativas foram recusadas pela fila congestionada e nenhum segundo MP4 foi entregue.
- O editor Free.ai confirmou que é um assistente de edição de clipe único, sem montagem multi-clipe completa; portanto não fecha o piloto sozinho.
- Creative Claw foi auditado como alternativa, mas o saldo disponível é 0 créditos; geração e montagem pagas não foram acionadas.
- Não houve tentativa de contornar limites, criar contas, inserir credenciais ou pagar serviços.

## Direitos e monetização

- Os Termos de Serviço públicos do LoreMotion foram consultados em 2026-11-17 e declaram propriedade do conteúdo gerado, uso comercial, edição e redistribuição sem royalties/atribuição, sujeitos aos termos do modelo utilizado: https://loremotion.com/terms/
- Gate atual: `MODEL_PROVIDER_TERMS_PENDING`.
- A alegação de uso comercial do serviço foi registrada, mas a cadeia completa de licença do modelo e a retenção durável do arquivo ainda não foram comprovadas.
- O clipe não está autorizado para publicação.
- Não houve gasto, pagamento ou publicação.

## Próximo gate automático

1. obter acesso multi-shot em uma rota gratuita sustentável ou mediante conta/autorização do proprietário;
2. preservar os clipes em armazenamento cloud durável;
3. fechar a verificação de licença do modelo e retenção;
4. combinar narração, trilha, legendas e montagem;
5. executar QA audiovisual;
6. entregar somente após o estado `READY_FOR_OWNER_APPROVAL`.
