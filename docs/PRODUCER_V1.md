# Producer V1 — provedor do pacote de prévia

`producer/` materializa o `package.json` que `orchestrator.runflow` já valida. Não altera gates, contratos nem estados.

**Fluxo:** spec do episódio → voz Kokoro por cena → footage (cadeia `local:`/`pixabay`/`pexels`, sem repetir clipe, respeitando rejeições de `contracts/*rejection*.json`) → trilha procedural original → legendas ASS alinhadas por ASR → `package.json` → render + gates → `PREVIEW_READY`.

**Regras que continuam valendo:** `publication_authorized=false`; direitos de voz/imagem/monetização `PENDING`; `approved_sources_only` força catálogo local aprovado (use no E01); legenda só é `synchronized` se alinhada por ASR e verificada.

**Rodar:** workflow *Produzir episódio (preview)* (precisa do workflow na branch padrão) ou `python -m producer.cli episodes/X.json --out build/X --footage local:catalog,pixabay`.
**Secrets:** `PIXABAY_API_KEY` (opcional `PEXELS_API_KEY`, emissão pausada). Nunca no repositório.
**Atenção:** artefatos de Actions em repositório público são acessíveis a qualquer conta com acesso de leitura; não gerar prévia com mídia privada enquanto o repo for público.

**Entrega das prévias:** o job `deliver` cria um **rascunho de release** (privado, não publicado) com `chat_preview.mp4` (540x960, leve) e o MP4 completo. A prévia é entregue ao proprietário no chat, sem precisar abrir o GitHub. Isso também evita expor mídia em artefatos públicos de Actions.


## Voz (decisão de 2026-11-20)

O dono rejeitou o Kokoro como robótico e aprovou de ouvido a voz **Mark** (ElevenLabs, `eleven_v4`, pt-BR). O Kokoro foi removido do produtor.
- Segredos: `ELEVENLABS_API_KEY` (plano pago Starter+ para uso comercial; o grátis NÃO tem licença comercial) e, opcional, `OPENAI_API_KEY` para a reserva.
- Padrão do spec: `"voice": {"provider": "elevenlabs", "voice_id": "AER0pA6w0SVtfnFMyfXG", "model_id": "eleven_v4"}`.
- Reserva (OpenAI gpt-4o-mini-tts, voz `ash`, instruída para soar calma e acolhedora): entra SÓ se a voz Mark estiver indisponível (404, 5xx, rede). Erros de chave, cobrança ou cota (401/402/403/429) bloqueiam, nunca caem para a reserva. Um episódio nunca mistura narradores. A reserva NÃO foi aprovada de ouvido: o dono precisa ouvir antes de publicar com ela.
- Tags como `[short pause]` entram no áudio e são removidas das legendas.
- Direitos de voz continuam `PENDING` até o dono revisar os termos da voz da biblioteca; publicação segue não autorizada.
- A camada legada do Kokoro (pesquisa, evidências, ONNX, voice preview do E01) continua no repositório como registro histórico e fora do caminho de produção.
