# VERBO NO CHÃO — Google Flow | pesquisa oficial e plano de teste gratuito (E01 v2)

**Status:** OPÇÃO RECOMENDADA, NÃO TESTADA EM CONTA DO PROJETO. Nada foi gerado, nenhum crédito foi usado, nenhuma plataforma foi autenticada nesta execução. Preservar PR #41 em rascunho.

## Por que é a alternativa mais promissora

- Brasil consta entre as regiões suportadas (Google Flow Help). Disponibilidade requer maioridade e conta Google elegível.
- Sem assinatura: **50 créditos diários** segundo a ajuda oficial (não acumulativos). Créditos/custos estão sujeitos a alteração e limite de frequência.
- **Veo 3.1 Lite**: vídeos de 4, 6 ou 8 segundos em **720p**, ambos os formatos; **10 créditos por saída** para não Ultra, conforme suporte Google em 18/11/2026. A documentação deixa claro que múltiplas saídas na mesma solicitação podem cobrar múltiplas gerações.
- **12 cenas** do E01 cabem em clipes de 8 segundos individualmente (o maior plano tem menos de 8 segundos); **120 créditos** seria o piso aritmético para 12 saídas bem-sucedidas sem retrabalho, ou **mínimo teórico de 3 dias** usando apenas 50 créditos/dia; NÃO é uma promessa de produção concluída ou disponibilidade real.
- O serviço permite **frames iniciais/finais** e **referências de personagem/objetos**, necessários para continuidade da mesma pessoa anônima, caderno, janela e casaco. A continuidade não é garantida pelo recurso; exige QA.
- O Google informa SynthID invisível em todos os outputs e configuração da marca d'água visível; há casos regionais de marca obrigatória fora do Brasil. Confirmar a saída real antes de qualquer uso.
- **Qualidade:** free 720p é utilizável para teste/roughcut, mas **NÃO atende a trava de mídia nativa 1080×1920** do master. Não afirmar upscale como captação nativa.
- **Direitos:** Google não reivindica titularidade de conteúdo original gerado, conforme termos gerais, mas isso não substitui regras específicas e direitos de terceiros. Licença, uso comercial e monetização ainda precisam de checagem editorial do projeto.
- **YouTube:** caso use tomadas fotorrealistas geradas por IA, verificar obrigatoriedade de divulgar conteúdo sintético no upload. Nunca apresentar cena gerada como registro documental de injustiça real.

## Comparação rápida com outras opções pesquisadas

| Plataforma | Grátis comprovado? | Limite que afeta um canal monetizável |
|---|---|---|
| **Google Flow** | Sim, 50 créditos/dia; Veo Lite 10/criação | Vídeo 720p gratuito; 1080p e direitos por terceiros ainda são gates |
| Krea | Sim, 100 unidades/dia | Licença comercial aparece a partir de plano pago |
| Pika | Gratuito limitado, sem franquia mensal no plano Free atual | Free sem licença comercial, inclusive créditos comprados |
| LTX Studio | Créditos de exploração | Free/Lite uso pessoal; comercial nos planos superiores |
| PixVerse | FAQ cita créditos diários | Direito comercial e qualidade de saída precisam de verificação por conta/versão |

## Teste-piloto autorizado apenas quando houver conta acessível e créditos confirmados

1. Abrir https://flow.google.com/ com a conta Google apropriada e verificar os créditos **do próprio Flow**. Não presumir login por existir conexão do Google Drive.
2. Criar um projeto privado com nome `VERBO NO CHÃO — E01 V2 — TESTES` (sem publicar/compartilhar).
3. Selecionar **Vídeo → Veo 3.1 Lite → Retrato (9:16) → 8 segundos → UMA saída → 720p**; desligar som de saída nas configurações do projeto se a opção estiver disponível.
4. Conferir custo exibido **10 créditos / uma saída** antes de gerar. Se diferente, interromper, atualizar plano, sem comprar créditos.
5. Usar o prompt de **S01** abaixo. Só avançar às outras 11 cenas após revisar quadro a quadro: anatomia das mãos, ator, caderno, janela, uniformidade e ausência de texto/marcas.
6. Para as oito cenas no mesmo ambiente, usar *o mesmo frame/ingrediente visual* aprovado da S01 como referência, ao invés de depender apenas de descrições textuais. Sempre revisar se a referência preserva a identidade visual.
7. Salvar arquivo privado, registrar plataforma/modelo/termos da geração e SHA, executar `agents/e01_candidate_media_intake.py` em ambiente autorizado. Nunca armazenar MP4 bruto no GitHub público.
8. A geração de teste **não** autoriza master, uso comercial ou publicação. Respeitar script/WAV/ASS já fixados e autorização do proprietário para publicar.

## Parâmetros globais (vale para os 12 prompts)

**Provider:** Google Flow / Veo 3.1 Lite | **Target:** 9:16 portrait, 720p, 8s, 1 output, no dialogue, mute original audio when available.

**Coerência:** mesmo adulto anônimo de casaco grafite, mãos naturais, mesa antiga, janela e caderno escuro nas cenas ROOM_A. Cinema realista discreto em carvão/âmbar; movimento natural de vídeo gerado. Não usar referências de pessoas reais, rostos reconhecíveis, logotipos, letras ou títulos em cena. Área inferior ~20–22% visualmente desocupada para legendas. Nenhuma geração poderá ser rotulada como filmagem de câmera.

## Prompts preparados para teste e revisão — NÃO RENDERIZADOS

### S01 — HOOK: pergunta sem resposta (0–5.74s; 5.74s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Night interior, lonely adult seated beside dark window with small notebook closed on table, reflective hands visible, silent tense negative space. Camera: slow push-in. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S02 — A dor da espera (5.74–10.62s; 4.88s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Close-up same anonymous adult hand resting on slightly worn wooden table near analog clock, warm light on fingertips, no numbers emphasized. Camera: subtle side dolly. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S03 — Violência e injustiça (10.62–16.76s; 6.14s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Grounded neighborhood exterior after rainfall, damaged public bench and empty street in dusk, distant anonymous silhouettes, compassionate social realism, no victims or blood. Camera: slow stabilized street-level move. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S04 — Habacuque: contexto (16.76–22.58s; 5.82s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Historically evocative close-up on handmade blank parchment and a human hand holding a reed pen by oil lamp, scholarly symbolic reenactment, not a portrait of Habakkuk. Camera: macro rack focus. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S05 — A lei perdeu a força (22.58–30.2s; 7.62s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Quiet ancient-looking stone corridor in twilight with worn steps and open doorway, subtle symbolic mood of unresolved justice, no soldiers or courtroom documents. Camera: tracking shot through corridor. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S06 — Não há resposta fácil (30.2–36s; 5.8s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Original notebook seen from overhead, pages blank except faint abstract marks not readable text, single shaft of late-night light, empty chair nearby. Camera: gentle top-down tilt. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S07 — Recusar normalizar o mal (36–43.16s; 7.16s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Same anonymous adult stands near a doorway looking toward city skyline on cloudy evening, subtle posture of moral resolve, no heroic fist or victory. Camera: slow silhouette reveal. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S08 — Fé sem fingimento (43.16–49.8s; 6.64s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Hands resting open on table in quiet prayer posture beside notebook, grounded modest room, light through curtains, no glowing beams or other supernatural effects. Camera: slow close focus drift. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S09 — Nomear o que está errado (49.8–55.56s; 5.76s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Same person's hands writing private notes in journal with all writing deliberately out of focus and unreadable, grounded documentary-like portrait. Camera: over-the-shoulder gentle push. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S10 — Apoio responsável (55.56–62.16s; 6.6s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Two anonymous adults seated in quiet community space with supportive posture, no physical coercion, natural mutual listening, hands on table. Camera: medium two-shot handheld stable. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S11 — A espera não acaba aqui (62.16–67.2s; 5.04s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Return to same modest room before sunrise, warm neutral sky visible behind closed notebook, silence and uncertainty persist. Camera: gentle wide shot. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

### S12 — Verdade e esperança — loop (67.2–70.425s; 3.225s)

```text
One uninterrupted 8-second portrait 9:16 cinematic video, original AI-generated scene, not documentary or archival material. Vertical 9:16, photorealistic AI-generated cinematic moving shot, grounded realistic lighting, quiet emotional realism, natural textures, 35mm lens feel; anonymous Brazilian adult protagonist in dark charcoal jacket where present; restrained slate-black and warm amber palette, ample contrast around caption zone; no text, no logos, no words, no miraculous or supernatural imagery, no graphics, no stock-photo aesthetic. Match composition of first scene: same notebook, window, anonymous hand now opening the cover slightly, first-frame loop alignment, no title inside scene. Camera: still lock-off with minimal movement. Natural moving subjects and subtle real-time physics, stable composition, no scene cuts. Maintain the same anonymous adult, charcoal jacket, modest room, worn desk, dark notebook and window whenever the scene contains the protagonist. For other contexts, do not pretend the filmed people are identifiable real victims or the historical prophet. Strict negatives: no readable words, logos, stock-photo poses, AI artifacts, face swaps, fantasy effects, religious iconography not supported by the narration, abrupt transitions. Reserve the bottom 22% of the vertical frame as clean negative space for future synchronized captions. No spoken dialogue or artificial voiceover.
```

## Fontes oficiais verificadas (18/11/2026)

- Conta Free e 50 créditos/dia: https://support.google.com/flow/answer/16353333
- Custo 10 créditos por Veo 3.1 Lite de 4/6/8s: https://support.google.com/flow/answer/16526234
- Recursos 9:16/frames/referências: https://support.google.com/flow/answer/16352836
- Brasil disponível: https://support.google.com/flow/answer/16353544
- Água invisível e marca visível: https://support.google.com/flow/answer/16353333
- Gestão de projetos e silêncio: https://support.google.com/flow/answer/16935308
- Propriedade de conteúdo original e ressalvas: https://policies.google.com/terms
- Conteúdo IA realista no YouTube: https://support.google.com/youtube/answer/14328491
- Pika não-comercial no Free: https://pika.art/faq
- LTX Free/Lite pessoal: https://help.ltx.io/hc/en-us/articles/32046651702290-Which-LTX-Studio-plans-include-a-commercial-use-license
- Krea Free e comercial no Basic: https://www.krea.ai/pricing

## Estado final e limites

**PROVIDER VALIDADO POR FONTES OFICIAIS; CONTA NÃO VERIFICADA; ZERO GERAÇÕES; ZERO MP4; DIREITOS E MASTER PENDENTES.** Esta rota não altera parâmetros aprovados de E01, não sobe arquivos e não chama API paga. É um handoff pronto para navegador conectado no Work, quando disponível.
