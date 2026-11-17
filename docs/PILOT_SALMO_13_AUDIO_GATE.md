# Gate de áudio — piloto Salmo 13

Estado: VOICE_RESEARCH_COMPLETE_PENDING_OWNER_SELECTION_AND_ZERO_CREDIT_ROUTE
Data: 2026-11-17 (America/Sao_Paulo)

## Situação comprovada

- Conta Creative Claw conectada e consultada em modo somente leitura.
- Saldo atual: 0 créditos.
- Não há voz clonada salva.
- Há limite de uma voz sintética projetada, mas não foi criada.
- Nenhuma narração foi gerada nesta etapa.
- Nenhuma cobrança, compra ou alteração de plano foi realizada.

## Critério editorial

A voz do Verbo no Chão deve soar humana, próxima, contemplativa e confiável. O objetivo é sustentar reflexão bíblica sem tom de locutor publicitário, sem teatralidade artificial e sem promessas emocionais exageradas.

Para o piloto, a melhor família técnica pesquisada foi `speech/elevenlabs-v4`, com suporte a português do Brasil, marcação de entrega, timestamps de palavras e uso comercial conforme o plano/licença efetivamente disponível. A elegibilidade comercial final ainda precisa ser confirmada na conta antes de publicação.

## Pesquisa de catálogo

A busca retornou 29 vozes compatíveis com português brasileiro. As duas melhores candidatas para teste são:

1. **Lucas — Natural, Calm and Steady**
   - modelo: `speech/elevenlabs-v4`
   - voice_id: `SVgp5d1fyFQRW1eQbwkq`
   - perfil catalogado: masculino, brasileiro, calmo, narrativo e estável
   - decisão: recomendação principal

2. **Will — Deep, Smooth and Affectionate**
   - modelo: `speech/elevenlabs-v4`
   - voice_id: `CstacWqMhJQlnfLPxRG4`
   - perfil catalogado: masculino, brasileiro, profundo, suave e afetivo
   - decisão: alternativa de contraste

Amanda Kelly — Sweet, Warm and Clear foi mantida como alternativa feminina, não como escolha principal, para preservar uma assinatura sonora mais sóbria no primeiro piloto.

## Pesquisa de rota gratuita e comercial

A pesquisa oficial mostrou que “free” não é automaticamente compatível com monetização:

- ElevenLabs Free permite uso não comercial com atribuição; direitos comerciais aparecem nos planos pagos. Portanto, não é aprovado como rota de publicação monetizada.
- Google Cloud Text-to-Speech oferece cotas mensais sem custo em vários modelos, mas exige faturamento ativado e pode cobrar automaticamente após o limite. A própria documentação autoriza uso em aplicações/mídia conforme os termos do Google Cloud.
- Azure Speech F0 oferece 0,5 milhão de caracteres neurais por mês; ainda exige conta/serviço Azure e verificação dos termos aplicáveis antes de publicação.
- Amazon Polly informa ausência de restrições de armazenamento e reutilização do áudio e oferece nível gratuito para novos clientes, mas depende de conta AWS e da janela/condições do Free Tier.

Conclusão operacional: nenhuma dessas rotas está conectada ao motor nesta sessão, e nenhuma conta de faturamento será criada ou usada sem autorização específica. A rota Creative Claw continua sendo a mais integrada, mas está bloqueada por saldo zero e por sua própria política de geração.

## Configuração técnica prevista

Quando houver uma rota de geração autorizada e com saldo:

- modelo: `speech/elevenlabs-v4`;
- idioma: texto integral em português brasileiro; usar `extras.language_code: "pt"` apenas se necessário;
- `extras.timestamps: true`;
- saída inicial: `mp3_44100_128`;
- usar somente `extras.voice_settings.stability` e `similarity_boost`;
- não usar SSML, velocidade, style ou speaker boost no v4;
- inserir pausas por pontuação e, se necessário, tags curtas de entrega;
- revisar pronúncia de nomes, referências e números antes da versão longa;
- transcrever/revisar o áudio retornado antes de sincronizar legendas.

## Travas

- Não gerar áudio com saldo zero.
- Não criar voz sintética ou clonar voz sem necessidade editorial e autorização específica.
- Não declarar licença comercial sem verificar os termos do plano e do provedor no momento da geração.
- Não substituir a voz recomendada silenciosamente.
- Um áudio gerado deve receber asset ID, URL, hash, duração e transcript antes da montagem.
- A montagem só avança com narração validada, trilha legalmente utilizável e legendas sincronizadas.

## Próximo gate

Destravar uma rota de voz sem gasto não comprovado ou obter autorização específica para créditos; em seguida gerar uma única amostra curta com Lucas, validar pronúncia, naturalidade e duração, e só então produzir a narração completa.
