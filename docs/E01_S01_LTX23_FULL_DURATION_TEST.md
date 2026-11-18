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

## Gate físico adicional (18/11/2026)

Foi identificado um segundo risco de **falso sucesso**: o fluxo antigo dizia `PHYSICAL_AI_VIDEO_VERIFIED_SCENE_DURATION_CHECKED` para qualquer MP4 decodificável, mesmo quando `covers_requested_scene=false`, codec inadequado, vídeo horizontal ou FPS errado. Isso permitiria um novo preview de 2 segundos aparecer como sucesso de 5,74 segundos.

**Correção:** `assess_video_eligibility()` exige simultaneamente decodificação integral, duração mínima S01, geometria retrato, tamanho nativo de preview >=480×848, 24fps com tolerância de 0,15, número mínimo de quadros quando informado, codec aceito, SHA-256 e JPGs de inspeção. Se qualquer condição falha, o workflow sai **2**, mantém o MP4 e JSON como evidência temporária e NÃO promove ao editor. Um sucesso técnico de vídeo continua marcado como `EDITORIAL_REVIEW_ONLY`, não como master nem direitos aprovados. Testes adversariais cobrem vídeos encurtados, FPS 0/0, geometria horizontal e SHA inválido.

### Licença de modelo — atualização de fonte primária

O [Help Center oficial LTX](https://help.ltx.io/hc/en-us/articles/37290270398610-Who-owns-the-content-I-create-with-LTX) esclarece que o uso de pesos abertos sob a licença Community **é gratuito para entidades com receita anual inferior a US$ 10 milhões**; acima disso, ou para revenda de modelo/produto concorrente, é necessário contrato comercial. A Lightricks não reivindica titularidade do output, mas permanecem restrições de uso, propriedade de terceiros e política de conteúdo; ver [texto vinculante do modelo LTX-2.x](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x). Esta análise identifica um caminho possivelmente compatível com criadores independentes, **sem declarar a situação contratual individual verificada**. O gate `rights_cleared=false` continua.

## Real execution trigger for the single deferred retest

The workflow is `workflow_dispatch` **or** a precisely filtered push to `contracts/e01_ltx23_s01_one_shot_trigger_20261118.json` **with exact commit message** `vnc-e01-s01-one-shot-free-retest-20261118`. Any incidental code/doc commit does not invoke the video generator. Concurrency protects against simultaneous jobs. The trigger file is intentionally **absent** until the existing once-only automation's scheduled time.

At the scheduled check, the automation should:
1. Verify it has not executed or already produced the full S01 (checks GitHub Actions run list, SHA and Drive backup);
2. Verify previous quota-reset window elapsed;
3. **Create, exactly once**, that absent trigger JSON through GitHub create_file on branch `verbo-no-chao/e01-stock-curation-gate-v1` with the exact commit message. This uses current HEAD code, unlike rerunning a prior workflow at an old commit. Do **not** use outdated `rerun_failed_workflow_run_jobs`;
4. Read generated GitHub Actions status and physical proof. A BLOCKED/FAILURE is not a video. If success with MP4, evaluate FFprobe, duration, SHA, and sample frames; preserve private Drive, never publish.
No recurring task or automatic credit retry was enabled. The existing one-off task remains the only scheduled execution.
