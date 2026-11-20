# Producer V1 — provedor do pacote de prévia

`producer/` materializa o `package.json` que `orchestrator.runflow` já valida. Não altera gates, contratos nem estados.

**Fluxo:** spec do episódio → voz Kokoro por cena → footage (cadeia `local:`/`pixabay`/`pexels`, sem repetir clipe, respeitando rejeições de `contracts/*rejection*.json`) → trilha procedural original → legendas ASS alinhadas por ASR → `package.json` → render + gates → `PREVIEW_READY`.

**Regras que continuam valendo:** `publication_authorized=false`; direitos de voz/imagem/monetização `PENDING`; `approved_sources_only` força catálogo local aprovado (use no E01); legenda só é `synchronized` se alinhada por ASR e verificada.

**Rodar:** workflow *Produzir episódio (preview)* (precisa do workflow na branch padrão) ou `python -m producer.cli episodes/X.json --out build/X --footage local:catalog,pixabay`.
**Secrets:** `PIXABAY_API_KEY` (opcional `PEXELS_API_KEY`, emissão pausada). Nunca no repositório.
**Atenção:** artefatos de Actions em repositório público são acessíveis a qualquer conta com acesso de leitura; não gerar prévia com mídia privada enquanto o repo for público.

**Entrega das prévias:** o job `deliver` cria um **rascunho de release** (privado, não publicado) com `chat_preview.mp4` (540x960, leve) e o MP4 completo. A prévia é entregue ao proprietário no chat, sem precisar abrir o GitHub. Isso também evita expor mídia em artefatos públicos de Actions.


## Voz (decisão de 2026-11-20)

O dono rejeitou o Kokoro como robótico e aprovou de ouvido a voz **Mark** (ElevenLabs, `eleven_v4`, pt-BR).
- Segredo necessário: `ELEVENLABS_API_KEY` (plano pago Starter+ para uso comercial; plano grátis NÃO tem licença comercial).
- Spec: `"voice": {"provider": "elevenlabs", "voice_id": "AER0pA6w0SVtfnFMyfXG", "model_id": "eleven_v4"}`. Sem `provider`, continua Kokoro.
- Tags de direção como `[short pause]` entram no áudio e são removidas das legendas.
- Direitos de voz continuam `PENDING` até o dono revisar os termos da voz da biblioteca; publicação segue não autorizada.
