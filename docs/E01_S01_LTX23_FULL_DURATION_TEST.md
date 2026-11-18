# E01 S01 V2 — full-duration LTX23 motion proof (not final scene)

Attempt one controlled free anonymous generation using official `Lightricks/LTX-2-3` Space. Prior successful actual 2.04s MP4 is locked in separate artifact and private Drive; do not overwrite.

## Source and risk investigation (2026-11-18)

Official Gradio Space Python defines 1–10 seconds, **24fps**, rounds to **8n+1 frames**, and sets shared ZeroGPU GPU budget `@spaces.GPU(duration=75)`. Thus request **5.8s** yields **145 frames ~6.04s**, covering locked S01 **5.74s** with margin. Text-only 480×848 target is a ~9:16 reduction from the prior 576×1024 proof, chosen for public GPU memory/time reliability. It remains below native master 1080×1920.

Source official code: https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py

Hard negatives in new prompt: exactly ONE CLOSED notebook, rain streaks prominently visible, no exposed face, same charcoal jacket, no extra notebooks, no title/letter/logo or supernatural picture. Main shot remains slow push-in and caption space lower 22%. Prompt edit is a creative acquisition tactic, not proof that AI complied.

The workflow makes **one request** after read-only runtime preflight; no user account, card, uploaded media, paid API, forced trial or auto retry. Limits it to 175 seconds local / 75-second GPU provider. Produces MP4, SHA256, FFmpeg decode and 1fps sample JPGs only when provider physically returns bytes. Passing CI with status `BLOCKED_*` is not a success on footage; inspect the report and media bytes.

Even with a physically complete 6s video: media is AI-generated fiction, not camera evidence, and full 1080×1920/30fps cinematic production, source rights (LTX-2 Community License), actor/notebook continuity, music/audio/commercial use and publication remain **BLOCKED**.

**No write to main/other branches, no merge or publication.** New clip is subject to scene-by-scene visual review before promotion.
