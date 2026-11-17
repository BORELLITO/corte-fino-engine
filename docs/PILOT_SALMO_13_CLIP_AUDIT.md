# Auditoria do primeiro clipe cloud — Salmo 13

Estado: `MULTI_SHOT_ASSETS_DURABLE_PENDING_VISUAL_QA_AND_HASH`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Escopo

- Projeto: Verbo no Chão — piloto Salmo 13.
- Regra clean-room: nenhum conteúdo, mídia, identidade, prompt ou fluxo operacional do Because Of This Stories foi utilizado.
- A auditoria registra as rotas de geração simbólica LoreMotion e aquisição de stock licenciado Pexels.
- Nenhum asset foi liberado automaticamente para publicação.

## Lote cloud persistido

| ID | Origem | Identificador durável | MIME | Dimensões | Duração | Estado |
|---|---|---|---|---|---:|---|
| S13-V01 | Pexels | `e4f8059a-5773-487d-8fb5-a769bf1dbf22` | video/mp4 | 1080×1920 | 17,045 s | persistido; QA técnico inicial |
| S13-V02 | Pexels | `096d4719-2826-4cce-ab34-456a75b40cd8` | video/mp4 | 1080×1920 | 34,027 s | persistido; QA técnico inicial |
| S13-V03 | Pexels | `75ad51e6-333a-4a65-ab9f-432fa929fb64` | video/mp4 | 1080×1920 | 46,100 s | persistido; QA técnico inicial |
| S13-V04 | Pexels | `349f6fa3-7e09-42ef-a421-ca82f63b0743` | video/mp4 | 2160×3840 | 15,015 s | persistido; revisão estética obrigatória |

Todos foram importados por rota cloud persistente e confirmados como vídeos verticais 9:16. As URLs permanentes, páginas de origem e demais dados estão no [ledger de direitos](PILOT_SALMO_13_RIGHTS_LEDGER.md).

## Rota LoreMotion observada anteriormente

- Modelo observado: LTX 2.5, gratuito e ad-supported.
- Formato: vertical 9:16, 720p, 5 segundos.
- URL: https://videos.loremotion.com/videos/d005a3cb-6a93-461b-8c76-ed60b6d15a78.mp4
- O MP4 foi transferido para o editor cloud Free.ai, que confirmou 5,0 s, 704×1280 e 9,5 MB, identificador `a66c7185-952f-4427-ad31-940b41e47129`.
- A transferência demonstrou transporte cloud, mas não armazenamento durável sob controle do projeto nem montagem final.
- O arquivo LoreMotion continua temporário e fora do lote principal até fechar termos, retenção e persistência.

## Direitos

- Pexels: licença pública gratuita para uso comercial sem atribuição obrigatória, sujeita às restrições de terceiros e da licença.
- LoreMotion: os Termos públicos consultados em 2026-11-17 indicam uso comercial e redistribuição sem royalties/atribuição, sujeitos aos termos do modelo: https://loremotion.com/terms/
- Pexels: fonte revisada; hash e QA visual final ainda pendentes.
- LoreMotion: `MODEL_PROVIDER_TERMS_PENDING`.
- Nenhum asset está liberado para publicação isoladamente.
- Não houve gasto, pagamento ou publicação.

## Limites e correções aplicadas

- O download direto pelo navegador cloud expirou em 30 e 120 segundos.
- A rota alternativa de importação direta cloud resolveu a persistência sem criar conta, inserir credenciais ou contornar limites.
- A montagem final não foi iniciada antes do QA visual e do ledger.
- S13-V04 será normalizado do 2160×3840 para o master 9:16 do piloto, somente após revisão de composição.

## Próximo gate automático

1. executar QA visual dos quatro planos na composição final;
2. confirmar espaço seguro para legendas e ausência de marcas/logos;
3. calcular/registrar hashes quando possível;
4. selecionar o conjunto definitivo;
5. gerar ou obter narração comercialmente autorizada;
6. montar com trilha, legendas e controle de volume;
7. entregar apenas no estado `READY_FOR_OWNER_APPROVAL`.
