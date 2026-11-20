# REGRAS PERMANENTES DE LEGENDA — VERBO NO CHÃO (v1, 20/11/2026)

Valem para TODOS os próximos vídeos. Prioridade alta: pontuação, espaçamento, quebra de linha, posicionamento e simetria.
Status: implementadas e testadas no pipeline (`agents/e01_v2_caption_pipeline.py`); aprovação final é visual/auditiva do usuário.

## 1. Karaokê (regra do usuário)
- Só a palavra que está sendo falada fica lilás (`#C4B0F2`, provisório). Todas as outras ficam brancas, antes E depois da vez delas.
- Nada de preenchimento acumulado (`\kf` proibido). Um evento por estado, mesmo texto/posição: nada se mexe.
- Em intervalos de até 0,20 s entre palavras o destaque é mantido até a próxima (sem piscar); em pausas maiores apaga.

## 2. Posição e tamanho (medidos em 3 telas de HUD)
- 1080×1920; fonte Atkinson Hyperlegible Next Bold, ASS 107; contorno 7, sombra 3.
- Margens laterais 180 px (x útil 180–900, longe da coluna de ícones à direita); margem inferior 576 px (acima da HUD inferior).
- Máx. 2 linhas; texto até 700 px por linha (medido com a própria fonte); centralizado.

## 3. Quebra de linha e de legenda
- Nunca terminar linha ou legenda em artigo/preposição/conjunção/pronome ("a", "de", "em", "que", "uma", "não"…) sem pontuação, nem em determinante ("essa", "mesma", "primeiros"…).
- "capítulo um" e pares equivalentes nunca se separam.
- Preferir quebrar após vírgula/dois-pontos; legenda nunca atravessa dois períodos; evitar palavra órfã e linhas muito desiguais; linha de baixo ≥ linha de cima (pirâmide).
- Preferir legendas que sejam orações inteiras (4–6 palavras); pontuação sempre colada à palavra anterior; nenhuma linha começa com pontuação.

## 4. Tempo de leitura
- Legenda aparece 0,10 s antes da primeira palavra e permanece até 0,35 s depois da última (mín. 1,0 s se houver folga), sem encostar na vizinha (0,04 s).

## 5. Controle
- Toda legenda que ainda quebra uma regra recebe `rule_violations` e DEVE ser revista por humano antes de aprovar. Nunca esconder.
- Casos residuais no E01 (voz Johnes, fonte 107): "diante de uma / sociedade ferida.", "Os primeiros / versos", "A fé não precisa / fingir", "responsável em / favor de alguém." — geometria de 700 px não permite quebra perfeita em 2 linhas; decisão do usuário pendente.
- O léxico de palavras que não podem terminar linha é em português e heurístico: NÃO substitui a revisão visual de cada episódio novo.

## Pontuação exibida (regra permanente)
- Ponto final nunca é exibido. `, : ;` somem no fim da legenda; vírgula e dois-pontos internos ficam. `?` e `!` ficam.
- Sem travessão, hífen decorativo ou reticências. Nenhuma linha começa com pontuação.
- Quebras de linha definidas por plano curado (`contracts/e01_v3_caption_plan_v1.json`), validado contra o roteiro canônico e as regras tipográficas. Largura máxima 715 px.
- Resíduo conhecido, NÃO RESOLVIDO: "diante de uma / sociedade ferida" (limite geométrico de 2 linhas).
