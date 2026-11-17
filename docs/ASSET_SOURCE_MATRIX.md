# Matriz de fontes de material — Verbo no Chão

Data da pesquisa: 2026-11-17 (America/Sao_Paulo)

## Objetivo

Expandir a seleção visual e sonora do Verbo no Chão sem depender de um único gerador, mantendo produção cloud, custo zero como padrão, coerência audiovisual e rastreabilidade de direitos.

Esta matriz é independente e clean-room. Não utiliza conteúdo, prompts, identidade, contratos, vozes, assets ou fluxo operacional do Because Of This Stories.

## Fontes prioritárias

| Fonte | Material | Uso comercial declarado | Atribuição | Regra operacional |
|---|---|---:|---:|---|
| Pexels | vídeo e foto | sim | não obrigatória | fonte visual padrão; evitar marcas, pessoas identificáveis em contexto sensível e cópias isoladas |
| Pixabay | vídeo, foto, música e efeitos | sim, dentro da Content License | não obrigatória | registrar a página do asset; verificar marcas, logos, pessoas e possíveis Content ID na música |
| Mixkit — Free License | vídeo, música, efeitos e templates | sim, conforme o tipo Free | geralmente não | confirmar que o item é Free, nunca Restricted; não usar música isolada nem registrar como própria |
| Coverr | vídeo e música | sim | não obrigatória | usar apenas downloads cobertos pela licença; ignorar Sponsored/premium e não redistribuir o arquivo isolado |
| Unsplash | foto | sim | não obrigatória | usar para stills e fundos; não vender a imagem sem transformação significativa |
| YouTube Audio Library | música e efeitos | sim para vídeos monetizados | depende do item | preferir Attribution not required; se CC, gerar e guardar a atribuição na descrição |

## Fontes condicionais

| Fonte | Condição | Risco |
|---|---|---|
| Wikimedia Commons | licença verificada na página individual; CC BY/CC BY-SA exige atribuição e, no segundo caso, atenção ao ShareAlike | o repositório não garante que todos os metadados estejam corretos |
| Openverse | usar como buscador; verificar a licença no site original antes do download | Openverse não valida a licença individual |
| Videvo | usar somente itens com licença comercial compatível; CC 3.0/Videvo Attribution exige crédito | licenças variam por arquivo e há conteúdo editorial |
| Videezy | permitido para comercial com atribuição quando a licença do item autorizar | padrão gratuito exige crédito e não pode ser Editorial/NonCommercial |
| Dareful | usar com registro da licença CC BY 4.0 e crédito | atribuição obrigatória |
| Free Music Archive | somente CC BY, CC BY-SA ou CC0, depois de conferir a página do track | NC não pode entrar no canal monetizado; ND não pode ser sincronizado em vídeo |
| Freesound | somente CC0 ou CC BY | CC BY-NC é proibido para conteúdo monetizado; licença varia por som |
| Incompetech | permitido para YouTube monetizado com crédito ao autor | guardar o texto de crédito correto |
| NASA | somente uso factual/editorial compatível e sem sugerir endosso; evitar logos, funcionários identificáveis e material de terceiros | não tratar toda mídia NASA como automaticamente liberada para promoção comercial |

## Fontes excluídas do padrão gratuito

- Motion Places: o download gratuito é apenas para avaliação; uso público/comercial exige licença Pro.
- Qualquer item marcado Sponsored, Premium, Editorial Only, NonCommercial, NoDerivatives ou com licença ausente.
- Qualquer clipe com marca, logo, personagem reconhecível, obra artística ou propriedade identificável quando a autorização correspondente não estiver clara.
- Conteúdo de redes sociais, agregadores, canais de “copyright free” e downloads sem página oficial de licença.
- Qualquer material que tenha sido usado, fornecido ou derivado do Because Of This Stories.

## Estratégia de seleção ampliada

1. Expandir cada briefing para termos em português e inglês, com variações semânticas de ambiente, luz, estação, textura, movimento de câmera e emoção.
2. Buscar primeiro Pexels, Pixabay, Mixkit, Coverr e Unsplash.
3. Consultar fontes condicionais apenas quando as prioritárias não cobrirem a intenção visual.
4. Priorizar paisagens, água, céu, jardins, flores, caminhos, mãos não identificáveis, objetos simbólicos e detalhes naturais que acompanhem a emoção da narração sem ilustrar literalmente cada frase.
5. Rejeitar imagens genéricas, repetidas, com estética de IA evidente, marcas, rostos não necessários, texto embutido ou conflito cultural/doutrinário.
6. Para música, começar pela YouTube Audio Library; usar Pixabay/Mixkit apenas após registrar licença, página e risco de Content ID.
7. Para cada asset aprovado, registrar: URL da página, URL do arquivo, título, autor, data de download, licença, exigência de crédito, restrições, hash do arquivo, uso previsto e estado do gate.

## Contrato mínimo do registro de direitos

Um asset só pode avançar para montagem quando o ledger contiver:

- `source_url`;
- `download_url`;
- `creator`;
- `license_name`;
- `license_url`;
- `commercial_use`;
- `attribution_required`;
- `third_party_risk`;
- `downloaded_at`;
- `sha256`;
- `project_use`;
- `rights_status`.

Estados permitidos: `PENDING_REVIEW`, `CLEARED`, `CLEARED_WITH_ATTRIBUTION`, `BLOCKED`.

## Automação futura

A busca pode ser automatizada por APIs quando houver credencial e autorização compatíveis. Pexels e Pixabay oferecem APIs gratuitas com limites e regras de cache; Openverse oferece API aberta, mas a licença deve ser verificada no item original. O motor não deve fazer downloads em massa, contornar limites ou tratar resultado de busca como autorização de uso.

## Veredito

O conjunto recomendado para o piloto é:

- visual: Pexels + Pixabay + Mixkit + Coverr + Unsplash;
- som: YouTube Audio Library primeiro, Pixabay/Mixkit como reserva;
- histórico, natureza, astronomia e referências específicas: Wikimedia Commons/NASA somente com verificação individual;
- geração AI: LoreMotion como uma rota entre várias, nunca como dependência única.

A matriz amplia substancialmente o leque sem relaxar os gates de direitos, originalidade, coerência ou monetização.
