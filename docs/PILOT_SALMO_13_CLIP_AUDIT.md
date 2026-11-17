# Auditoria do primeiro clipe cloud — Salmo 13

Estado: `CLIP_RENDERED_PENDING_ASSEMBLY`

Data da execução: 2026-11-17 (America/Sao_Paulo)

## Origem e escopo

- Projeto: Verbo no Chão — piloto Salmo 13.
- Regra clean-room: nenhum conteúdo, mídia, identidade, prompt ou fluxo operacional do Because Of This Stories foi utilizado.
- Superfície: LoreMotion, execução cloud via navegador gerenciado.
- Modelo: LTX 2.5, gratuito e ad-supported.
- Formato observado: vertical 9:16, 720p, 5 segundos.
- Prompt: paisagem contemplativa ao amanhecer, caminho junto a oliveiras, névoa, movimento lento de câmera, sem pessoas, texto, logotipos ou fala.
- Status observado: render concluído.

## Evidência observada

- URL direta do MP4 observada após a geração:
  https://videos.loremotion.com/videos/d005a3cb-6a93-461b-8c76-ed60b6d15a78.mp4
- Ação de download acionada no navegador.
- A persistência externa do arquivo baixado não foi confirmada; a URL é tratada como entrega temporária até armazenamento cloud durável ser validado.

## Direitos e monetização

- A interface pública do LoreMotion declara saída sem marca d'água e uso comercial, mas essa declaração ainda não foi confrontada com os Termos de Serviço em uma etapa jurídica dedicada.
- Gate atual: `RIGHTS_PENDING_VERIFICATION`.
- O clipe não está autorizado para publicação.
- Não houve gasto, pagamento ou publicação.

## Próximo gate automático

1. preservar o clipe em armazenamento cloud durável;
2. validar direitos/licença e retenção;
3. gerar/selecionar os demais planos visuais coerentes com o roteiro;
4. combinar narração, trilha, legendas e montagem;
5. executar QA audiovisual;
6. entregar somente após o estado `READY_FOR_OWNER_APPROVAL`.
