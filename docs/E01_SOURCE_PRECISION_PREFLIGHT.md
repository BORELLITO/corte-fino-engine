# E01 — source precision preflight: zero generic stock, zero accidental rejection reuse

**Date 2026-11-18 | Director decision:** all 12 scene briefs are anchored directly to locked story timings, words, visual actions, camera-world grouping, two explicit queries and two hard negatives. The first eight `ROOM_A` shots require ONE anonymous person, same charcoal jacket, notebook, window, desk, light and first-scene reference. The 4 other shot groups may use licensed stock after actual visual review. **Nothing is admitted by this policy by default**.

## Why the fix matters
Previous workflows downloaded twelve different Pexels candidates, only to discover daylight, wrong furniture, generic cafes, modern corridors, readable Bible text and actor discontinuity after decode. The first version logged rejections but did not centrally deny known rejected video IDs *before network download*. We now block all **12 unique previously rejected Pexels IDs** and **13 SHA-256 fingerprints** (including the too-short LTX sample) across subsequent episode preflight and generic media intake.

`contracts/e01_source_precision_policy_v1.json` contains the frozen scene-specific queries and negative filters copied from the canonical single-world acquisition blueprint, not user-generated generic tags. `agents/e01_source_precision_gate.py` checks them against the independently preserved storyboard and director verdicts and fails closed on metadata drift, rejected source IDs, cross-scene vague queries, untrusted Pexels URLs, generic stock for `ROOM_A`, or any fictional source claims. New IDs that pass are **only eligible for downloading actual bytes and review**, not considered to exist, licensed, high quality, or usable.

`agents/e01_candidate_media_intake.py` now rejects physical MP4s matching any of the 13 known bad source hashes even if FFprobe and FFmpeg decoder succeed. Main `agents/e01_visual_single_world_gate.py` and `.github/workflows/verbo-no-chao-gates.yml` require this policy on every push. No changing older approved baseline/rejection data, no new video generation and no API charges.

**Creative director operational acceptance:** before accepting any future video, inspect real frame samples AND the meaningful action over the full scene, check clothing/actor/space, caption safe zone, physical length, temporal motion, historical specificity, false endorsement/depiction, content license, model/voice/music rights, and editing originality. An English Pexels title or a thumbnail NEVER proves any of these. Only create a new versioned *approval* contract with the physical SHA, run URL and reasons; never silently edit this frozen historical preflight to approve footage.

### Example new sourcing preflight (research only)

`python -m agents.e01_source_precision_gate --scene-id VNC-E01V2-S10 --video-id <actual_page_id> --page-url https://www.pexels.com/video/<verified_page_slug>-<actual_page_id>/ --query "<exact_first_scene_S10_query>"`.

A passing result means **eligible for physical media review only**. It is not permission for automated publication, recurring GPU use, an account login, or third-party contact. The identifier used in unit tests is deliberately synthetic and NOT a real recommendation.

**Known limitation:** software cannot guarantee narrative accuracy from structured metadata. In ambiguous footage, reject until directorial visual verification rather than falsely promising to "never" retrieve a wrong video.
