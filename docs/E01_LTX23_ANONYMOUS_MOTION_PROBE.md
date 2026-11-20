# E01 — Second independent free GPU route: official LTX 2.3 Distilled

**Status at commit:** configured and awaiting run; **not a finished video**.

## Why this option
The prior Wan public ZeroGPU test ran 500 seconds and timed out without an MP4. A new official Space by the LTX model developer `Lightricks/LTX-2-3` displays **Running on Zero** and has a Gradio `generate_video` endpoint that supports 1–10-second AI videos with a fictional, faceless anonymous subject.

The production gate remains **closed**. This makes **one 2.0-second, 576×1024 (vertical) AI motion test** from a text-only prompt, no voice or personal uploads, and never calls paid APIs, checks out a trial, publishes, or spends money. Actual accepted source is checked by real ffprobe, full FFmpeg decode, SHA256 and timecode. **A 2-second video will NOT fill the 5.74-second S01** and is below native master 1080×1920. Even a valid MP4 only proves moving media bytes.

## Safer execution
- First call the public official HF runtime API **read-only**; fail-closed if stage not `RUNNING`.
- Use official Gradio endpoint `/generate_video` exactly once, text-only; no tokens or user files.
- Limit network render to **155 seconds**, job to six minutes. No background cron, no retry if provider is queued/paused.
- Save only short-lived 1-day evidence (video if physically returned and verified; otherwise a JSON explaining why nothing was acquired).
- A timeout leaves prior `PROVIDER_RUNNING_RENDER_UNVERIFIED` (or `STARTED_NO_FOOTAGE`) as evidence; it must never count as generated video.
- Do not put URLs to private sessions, media, real people or any tokens into GitHub.

## Licensing and prior decisions
LTX 2.3 uses **LTX-2 Community License** with restrictions; it is **not Apache 2.0**, so never mark commercial clearance automatic. Check the terms against actual use before publishing. User's audiovisual rule remains *photoreal motion footage only*; generative AI video is disclosed as fictional and not misrepresented as a filmed historical or documentary event.

References:
- Official Space: https://huggingface.co/spaces/Lightricks/LTX-2-3
- Source and Gradio endpoint: https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py
- Model and license: https://huggingface.co/Lightricks/LTX-2.3
- HF anonymous daily GPU pool: https://huggingface.co/docs/hub/spaces-api-endpoints
- Rejected anonymous service Free.ai: https://free.ai/video/text-to-video/ — 30k cost per render but only 6k anonymous tokens.
- Prior failed Wan run: https://github.com/BORELLITO/corte-fino-engine/actions/runs/44279375769

**Not modified:** canonical E01 text SHA, audio SHA, ASS cue boundaries, twelve-scene plan, rights ledger, publication locks, main branch, previous PRs. **Never** report film completion without returned MP4 plus physical inspection.
