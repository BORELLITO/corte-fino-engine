# VERBO NO CHÃO — E01 v2: verificador de mídia para uma cena real

**Implementado:** pipeline de entrada de bytes locais para clipes reais/gerados, sem upload de material bruto para GitHub. Usa FFprobe + decodificação FFmpeg completa + SHA-256; verifica cena, duração, FPS e 9:16, bloqueando qualquer promoção automática ao master. Integra o plano de 12 cenas `contracts/e01_v2_visual_single_world_acquisition_v1.json` sem alterar áudio, roteiro nem as 28 legendas.

**Uso privado (somente após possuir MP4 da cena):**

```bash
python -m agents.e01_candidate_media_intake --video /private/E01_S01.mp4 --scene-id VNC-E01V2-S01 --origin ai_generated_video --out /private/E01_S01_QA.json
```

Origem também aceita: `camera_original` (filmagem original) e `stock_licensed_candidate`. Estes rótulos são declarações do operador, não autenticação de propriedade/identidade. Mesmo um MP4 1080×1920 íntegro **não passa automaticamente direitos comerciais, continuidade de personagem, avaliação de quadros, safe zone ou publicação**.

**Preflight externo de geração (18/11/2026):** a Creative Claw recebeu um pedido de amostra de S01 em Seedance 2.0 Mini, 5 segundos, 480p vertical e áudio desativado, mas devolveu `approval_required` e não renderizou nada. A cotação mostrou 15 créditos contra saldo zero. Não houve cobrança nem submissão de job. Não persistir URLs de aprovação assinadas no GitHub. Higgsfield mostrou conta Free, 10 créditos e um uso gratuito de ferramentas de troca/controle com vídeo de referência — não um texto-para-vídeo gratuito confirmado. Trial não ativada.

Um clipe de 5s, ainda que gerado, não cobre S01 (5,74s), nem a resolução do master 1080×1920. O motor registra `scene_length_covered=false` e `preview_only=true` nesse caso. AI vídeo com movimento gerado não deve ser rotulado como filmagem capturada por câmera.

**Teste reprodutível:** suíte de unidade cria internamente (sem upload) padrão sintético vertical H.264 de 6s para exercitar FFprobe, SHA e decode; o resultado precisa manter `approved_for_master=false`. Isso prova o verificador, **não** a existência de clipe cinematográfico pronto.

**Pendências:** obter mídia da cena com custo autorizado ou uso comprovadamente gratuito, fazer QA artístico do arquivo real, comprovar origem e direitos e continuar sem publicar.
