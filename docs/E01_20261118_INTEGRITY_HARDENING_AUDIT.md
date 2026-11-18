# VERBO NO CHÃO — Integrity, audiovisual and release hardening
Date: 2026-11-18. Scope: E01 and shared clean-room cloud orchestrator. Status: **DRAFT BRANCH / NOT MERGED / NO RELEASE**.

## Protected baseline

- Parent branch: `verbo-no-chao/e01-stock-curation-gate-v1`, base SHA `bdd26ea2d536372e423e95dbb6e693c702093bdd`, PR #41 is DRAFT.
- Original E01 storyboard: 12 shots from 0 to 70.425s; 8 recurring-room scenes; 28 captions.
- Canonical v2 script SHA `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6`, WAV SHA `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`, ASS SHA `0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a`.
- No edits to `main`, bootstrap, Salmo 13, canonical script/audio/captions, stock editorial decisions, private media, licenses or publication settings.

## Confirmed faults and fixes on this branch

1. **SHA laundering:** `orchestrator/runflow.py` used to replace provider-declared artifact digests with hashes of whatever files happened to exist, allowing a false match. Now it preserves declarations and checks actual SHA-256 before render and again in `engine.quality_gates`.
2. **Unbound / absent media:** previous cloud validation could omit physical audio/music/captions/output artifact evidence entirely while relying on self-declared PASS. All four media bindings and real files are now mandatory for artifact-backed previews, and declared audio/music/output hashes must match the same files the render reads.
3. **Fabricated preview or release:** a media SHA matching arbitrary non-video bytes is not proof of video. Preview-ready and publishable states now require real media probe and full FFmpeg decode. Release-grade sources also require actual dimensions >=1080x1920 and non-looped temporal coverage; a resized small storyboard tile cannot automatically qualify.
4. **Legacy flag laundering and forged publication:** cloud runflow no longer overwrites `legacy_projects_used=True`, and cannot accept `PUBLISHED` from a provider JSON. Publication requires an independent, explicitly authorized external publisher.
5. **PCM16 contract conflict:** the E01 original persisted WAV is 24-kHz mono PCM16, whereas the legacy fixture required floating-point-only format; both legitimate formats are now represented without rewriting the Salmo 13 fixture.
6. **Unhandled malformed JSON, unsafe paths and numeric edge cases:** invalid state types, section types, nested unhashable values, nonfinite intervals, bool segment counts, NUL/traversal paths and huge source media hashes are handled conservatively. Streaming hashing avoids loading entire media files into memory.
7. **Audio mix falsely labeled ducking:** fixed 0.12-volume music was not voice-driven. Core FFmpeg renderer now uses true sidechain compression controlled by the voice signal and an output limiter. A local synthetic-source FFmpeg filter test passed.
8. **Potential source overwrite and temporal repetition:** render refuses pre-existing outputs, avoids collision with input source paths, and removes `-stream_loop -1`; each source must physically last through its requested out-time. A finished clip must match the expected 12-shot timeline duration.
9. **Unsafe subtitle filename characters:** the FFmpeg subtitle filtergraph now requires a restricted local .ass/.srt/.vtt filename; unusual or malicious filtergraph characters are blocked.
10. **Manual one-shot replay of provider GPU:** the S01 LTX workflow on this *candidate branch* now refuses manual execution and requires an ADD-only nonce with exact payload, message, and exactly one history event for that path. The existing scheduled original-branch job is deliberately untouched; this change is not yet active there.

## Evidence

- Broad unittest suite: `tests/test_vnc_integrity_hardening_20261118.py` adds adversarial tests of real bytes vs falsely declared SHA, missing media, malformed JSON/path, illegal publishing, fake non-decodable video, real PCM16 and preservation of pilot behavior.
- Physical integration: `tests/test_vnc_audio_ducking_physical.py`, workflow `verbo-no-chao-qa-hardening-physical.yml`, real local FFmpeg 1.2-s synthetic audio sidechain and 0.55-s synthetic motion source that cannot be silently repeated to 2 s. These sources are test fixtures only, never E01 footage.
- The original remote LTX S01 retry has its own previously scheduled one-shot task (15:37 America/Sao_Paulo, 18 Nov), which was not run or modified by this audit. No GPU generation, billing, login, upload or publication is performed here.
- Latest exact CI runs/commit must be checked before merging. A SUCCESS is an integrity result for the tested code, not a commercial right, final master or scene-director approval.

## Residual blockers — deliberately NOT claimed fixed

- There is no editor-approved 5.74-second cinematic S01 in the source-of-truth master; existing 2.04-second AI proof is editorially rejected.
- 12 final coherent 1080x1920 original moving shots are still missing; the old 70.43-second rough cut is a technical preview built from low-resolution stills.
- Source permissions and commercial TTS/voice runtime rights require explicit provider documentation; music with usable rights is not finalized.
- GitHub Actions still cannot access all private user-Library binary sources directly; a verified private-provider or Drive-to-runner transfer must precede an actual cloud master.
- Semantic scene fidelity, source rights, actor continuity and actual platform publication evidence are not proven by this CI.
- This hardening branch is intentionally isolated. Do not merge during or ahead of the scheduled one-off S01 attempt without evaluating its event/nonce dependency.

## Rollback

Do not merge the PR; retain parent SHA `bdd26ea2d536372e423e95dbb6e693c702093bdd`. This branch changes only general-purpose verification, rendering and tests plus the S01 workflow. Existing media backup and canonical assets are not edited.
