# VERBO NO CHÃO — E01 S10 | Audit checkpoint, 2026-11-19

**Decision: REJECT Pexels ID 9490306 FOR S10 ONLY.** Candidate physically verified but not editorially acceptable. This document is part of isolated research, **not a scene approval or master release**.

## Canonical invariants
- Project `VERBO_NO_CHAO_EXCLUSIVO` only. S10 `VNC-E01V2-S10`, timestamp `55.56–62.16`, 6.60 seconds, narration block `application`, captions `[22,23,24]`.
- Original approved E01 script `c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6` and WAV `4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e` untouched.
- Storyboard: two anonymous adults, seated at simple table, mutual listening/compassionate body language; no invented healing or authentic testimony, no invasive touching, no recognizable faces implying endorsement; restrained 9:16/charcoal-amber/caption safe zone.

## Source proof
- Original public page: https://www.pexels.com/video/a-woman-talking-to-her-friend-while-sitting-at-a-table-9490306/
- Creator: Yaroslav Shuraev. Pexels public page described 2160×3840, 25 fps, about 17 seconds.
- Physical verification: [Actions #44491955202](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44491955202): original MP4 19,127,730 bytes, **16.56s**, **2160×3840**, **25 fps**, H.264, **full-stream FFmpeg decode PASS**.
- Exact original SHA-256: `cfecb6aa945c25258728a5155840ae03a1ca636866a4719137c29c8dec75c35e`.
- Two true temporal review windows (0–6.6s, 8–14.6s) and an additional native 1080×1920 center lower-body crop; evidence SHA-256 values in `contracts/e01_s10_real_stock_editorial_rejections_20261119.json`.
- **No raw source MP4 committed**, no source uploaded to a public Git repository, no model API, billing or publishing.

## Director visual rejection (actual frames)
1. One adult in white clothing is sitting **on the tabletop** holding an apple; another adult faces an open study book. The observed context is **studying/teaching**, not mutual support.
2. A prominent identifiable face and recognizable profile occur across the frames. The lower-body crop reduces face visibility but retains books, apple and study context; it cannot establish actual compassionate mutual listening.
3. Cool studio/daylight lighting and white clothing differ from the canonical subtle charcoal/amber aesthetic.
4. It would be editorially misleading to imply these people are experiencing distress, providing faith-based counseling, receiving care, or endorsing the narration.

**Decision: reject even though source resolution and duration pass.** Do not cut/zoom/mirror/reuse this asset to fake a suitable S10. Per-scene exclusion only; canonical immutable exclusions and other projects remain unmodified.

## License and gates
- Pexels terms: https://www.pexels.com/license/ permit free use but prohibit representing identifiable people as endorsing the message, or presenting them in an offensive manner. These constraints require **contextual rights review**, not automatic promotion.
- `commercial_rights_cleared=false`, `editorial_approved=false`, `allowed_in_master=false`, `publication_authorized=false`.
- Automated scene gate: `agents/e01_source_precision_gate.py` reads the frozen S10 record before selecting a known video for the S10 research shortlist.
- Tests: `tests/test_e01_s10_pexels_9490306_physical_qa.py` and `tests/test_e01_s10_source_rejection_20261119.py`. CI [Engine Gates #44492395265](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44492395265) reported **455 tests, 13 skipped, zero failures**, with 13 specialist/coordinator jobs green at [#44492395270](https://github.com/BORELLITO/corte-fino-engine/actions/runs/44492395270).

## Evidence archive and rollback
- Backup ZIP SHA256: `871f6ff4e628430483054b5fcea222aea84628ba78b10097ce2e8792f026beb5`.
- Private Library: `/VERBO_NO_CHAO/E01_V2_ROUGHCUT/S10_QA/VERBO_NO_CHAO_E01_S10_QA_CHECKPOINT_20261119.zip`.
- GitHub changes confined to this VNC research branch; no merge to `main`, no change to operational PR #41 or pending S01 safety PR #45.
- Rollback: close the draft research PR; the canonical E01 storyboard, WAV, subtitles, pilot Salmo 13 and publishing remain intact.

## Next action
Rather than collect more study-room or pseudo-therapy stock, require **actual faceless supportive conversation at a modest indoor table with human gestures**, first screening frames/context and licensing before physical research. Another route is original authorized real footage, not a fake animation from JPEG. **S10 remains UNSOURCED** and E01 master/publication remain BLOCKED.
