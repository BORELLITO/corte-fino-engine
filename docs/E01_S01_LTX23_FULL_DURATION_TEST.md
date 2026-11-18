# E01 S01 V2 — full-duration LTX23 motion proof (not final scene)

Attempt one controlled free anonymous generation using official `Lightricks/LTX-2-3` Space. Prior successful actual 2.04s MP4 is locked in separate artifact and private Drive; do not overwrite.

## Source and risk investigation (2026-11-18)

Official Gradio Space Python defines 1–10 seconds, **24fps**, rounds to **8n+1 frames**, and sets shared ZeroGPU GPU budget `@spaces.GPU(duration=75)`. Thus request **5.8s** yields **145 frames ~6.04s**, covering locked S01 **5.74s** with margin. Text-only 480×848 target is a ~9:16 reduction from the prior 576×1024 proof, chosen for public GPU memory/time reliability. It remains below native master 1080×1920.

Source official code: https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py

Hard negatives in new prompt: exactly ONE CLOSED notebook, rain streaks prominently visible, no exposed face, same charcoal jacket, no extra notebooks, no title/letter/logo or supernatural picture. Main shot remains slow push-in and caption space lower 22%. Prompt edit is a creative acquisition tactic, not proof that AI complied.

The workflow makes **one request** after read-only runtime preflight; no user account, card, uploaded media, paid API, forced trial or auto retry. Limits it to 175 seconds local / 75-second GPU provider. Produces MP4, SHA256, FFmpeg decode and 1fps sample JPGs only when provider physically returns bytes. Passing CI with status `BLOCKED_*` is not a success on footage; inspect the report and media bytes.

Even with a physically complete 6s video: media is AI-generated fiction, not camera evidence, and full 1080×1920/30fps cinematic production, source rights (LTX-2 Community License), actor/notebook continuity, music/audio/commercial use and publication remain **BLOCKED**.

**No write to main/other branches, no merge or publication.** New clip is subject to scene-by-scene visual review before promotion.

## Executado, bloqueio real e correção fail-closed — 18/11/2026

O **primeiro pedido físico de 5.8s/480×848** terminou com **bloqueio de cota** (não gerou MP4). Evidência do artefato do workflow [44286003054](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44286003054): `AppError`, `ZeroGPU quota (112s requested vs. 9s left)`, indicação de reset em **7:21:22** no momento do erro. Essa indicação é fornecida pelo serviço e não garante disponibilidade futura.

Um reteste de integração [44286817587](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44286817587) retornou `RuntimeError: provider_returned_no_video`. Nenhum dos dois forneceu material audiovisual utilizável. O protótipo prévio de **2.041667s** continua intacto, sob backup privado.

**Falha corrigida na instrumentação:** o código original devolvia `exit 0` mesmo sem mídia, resultando em workflow verde enganoso. O novo `agents/e01_ltx23_s01_v2_render.py` emite **exit 2** quando há bloqueio e registra a classificação de cota com quantidade requerida, saldo e janela estimada, sem persistir links de autenticação. `tests/test_e01_ltx23_s01_v2_render.py` cobre o parsing de cota e a proibição de promoção ao master.

**Circuit breaker operacional:** o workflow `.github/workflows/verbo-no-chao-e01-s01-v2-probe.yml` agora é **somente `workflow_dispatch`**; alterações comuns em código NÃO iniciam novas gerações. Foi criada uma automação **única** para reavaliar quando a janela indicada se recuperar, sem gastar, fazer login ou publicar. A ação futura está programada e sua execução/sucesso ainda **não** estão comprovados.

Licenciamento: o repositório do modelo identifica a **LTX-2 Community License**, que exige uma análise do direito de uso conforme as condições e eventual patamar de receita; isso **não concede aprovação comercial automática**. Fonte: https://huggingface.co/Lightricks/LTX-2.3 e https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2

**Entrega atual:** prova anterior de 2 segundos e testes do motor preservados; **cena completa 5.74s não gerada**, retake sem aprovação editorial, publicação bloqueada.
