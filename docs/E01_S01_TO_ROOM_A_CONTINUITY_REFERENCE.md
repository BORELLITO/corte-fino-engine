# E01 — same actor and room: director-approved S01 first-frame handoff

**Decision:** The known problem is no coherent source shot of 5.74 seconds for S01. Earlier tests proved real AI moving MP4 for 2.04s, not a final S01. The scheduled one-shot LTX 5.8s retest is preserved. This change uses ZERO GPU credits and makes NO new video request.

## Provider interface: verified directly

The official public Gradio implementation at https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py currently defines `generate_video(input_image,prompt,duration,enhance_prompt,seed,randomize_seed,height,width)`. It explicitly maps an input image into `ImageConditioningInput(path,frame_idx=0,strength=1.0)`. Thus **image-to-video** first-frame guidance is available for the later ROOM_A scenes without manually using websites. It is **not a character identity lock**, especially when cameras change angle. Each future scene needs its own storyboard-aligned, reviewed first frame; copying a wide S01 shot into S02 closeup cannot introduce an analog clock faithfully by itself.

## Actionable implementation

- New `agents/e01_s01_video_anchor.py` automatically receives the S01 generated MP4 and the hard-gated output report *after* S01's scheduled render. It rejects no-file, too-short, wrong width/height/fps, mismatched SHA256, provider run failures and unearned rights/scene approvals.
- It analyses actual FFmpeg-decoded **6 samples/second** frames at 72×128 grayscale, checking measurable adjacent-luma variation. This screens out literal static-frame videos. A positive difference **does not prove semantic action**: rain, notebook state, hands, actor and anatomy still require editor frame review.
- It extracts 5 exact reference PNGs from the physical S01 video at 0.0, 0.9, 2.35, 3.85, 5.45 seconds (all within 0..5.74), composes a five-frame contact sheet and records SHA256 for each and the source in `continuity_reference_evidence.json`.
- Files are included in the **short-lived GitHub Actions artifact** already created by workflow `verbo-no-chao-e01-s01-v2-probe.yml`; not committed to the repository nor automatically passed to followup scenes. Private Drive archival after validation is handled separately by existing one-off automation.
- `contracts/e01_room_a_reference_handoff_v1.json` enumerates **exactly 8 ROOM_A scenes** (S01, S02, S06, S07, S08, S09, S11, S12) with immutable timeline and no invented asset SHA/rights/approval. The storyboard must remain canonical.
- The single-world CI plan calls the reference-blueprint validator, and new adversarial tests prevent false first-frame approval and reject zero-motion fake videos.

## Gates and responsibilities

The senior editor is responsible for inspecting and deciding scene fidelity (night, closed notebook, window rain, back-facing anonymous adult, same jacket/room, natural temporal motion). Until a real source has been inspected and approved, the anchor report remains `FRAME_ANCHOR_CANDIDATES_AWAIT_DIRECTORIAL_VISUAL_QA` and `reference_promoted_to_i2v=false`. Neither metadata nor automated motion detection guarantees a coherent actor or filming.

Original locked E01 WAV SHA256 `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e`; script SHA256 `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6`; 28 ASS captions. All unchanged. Master 1080×1920, music licensing, generated content disclosure and publication remain BLOCKED. Do not imply current 480×848/24fps preview meets native 1080×1920/30fps.
