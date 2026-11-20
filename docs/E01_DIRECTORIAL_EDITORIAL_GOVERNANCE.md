# VERBO NO CHÃO — E01 Editorial Director Approval Contract v1

**Delegated role:** The assistant acting as senior creative director owns **editorial selection and rejection** without repeatedly asking the channel owner to choose between mediocre footage. The owner retains authorization of external publication, account expenses, material brand/rights exceptions and destructive/irreversible operations. Technical media probes, failed AI renders, and conditional exploratory reviews never authorize cuts.

## Final decisions — November 18, 2026

Following factual review of **actual video frame samples** (not just model descriptions or still-search results), reject all seven individually reviewed candidates as canonical E01 footage:
1. S01 Pexels 8860242: daylight / no rain / no closed notebook;
2. S01 LTX 2.04-second genuine AI video: too short (5.74 required), notebook wrong, rain unclear;
3. S05 Pexels 37340388: distinctive sunlit stone courtyard, modern furniture and bright surfaces. Using it as historical Judah would be misleading;
4. S10 Pexels 4828603: casual coffee, no supportive gesture;
5. S10 Pexels 6381001: **supportive handclasp conveys meaning**, but sofa / denim / daytime / no simple shared table break the locked community scene. The previous conditional visual impression is **superseded by final REJECTED_FOR_E01_CANONICAL_SHOT**. Its graded 8-second MP4 was verified with hash 996cacfe98ed8169ef0931f45ea336ee520441c7b5b545c07178857d2fea5a35; 240 video frames / 30fps / 720x1280; subtle temporal motion, not a static photo. Eight sampled frames (0.5..7.5 seconds) do **not** constitute full semantic playback; no claim otherwise. Preserve privately in quarantine only.

**Proof of technical quality is not proof of scene suitability.** Shot acceptability requires meaning, exact scene behavior, one-world actor continuity, spatial/clothing/color coherence, usable caption zone, physical motion and durations, verified provenance, and review of source licensing. Threshold 4/5 individually in *meaning, continuity and visual quality*; a hard narrative error overrides an average rating. Only explicit AI-director evidence may mark new files as editorially approved. A changed original storyboard requires a documented creative approval rather than altering the script to fit stock.

## Legacy conditional exceptions now closed

The original first stock editorial contact sheet also contained a dim but contemporary corridor Pexels 6010698 provisionally tagged CONDITIONAL_METAPHOR for S05. The older second-batch frame review kept open-Bible footage Pexels 6860448 tagged CONDITIONAL_CONTEXT_ONLY for S08. After renewed inspection of the actual 15/50/85% frames, both are now REJECTED for the canonical E01: S05 resembles a modern shop/warehouse walkway with no ancient stone doorway; S08 shows brightly lit Bible reading (possibly readable text) and white outfit, not the recurring charcoal-dressed actor quietly praying with hands open beside the same notebook.

These are additional final decisions with original 64-character physical SHA256 and GitHub evidence. Earlier original review JSON remains unchanged as historical provenance; final editorial decisions take precedence over previous provisional ratings. The six already-rejected stock candidates across earlier batches stay rejected by their existing gate tests.

## Commercial/reuse safeguards

The [Pexels License](https://www.pexels.com/license/) generally permits free commercial use and modifications. This is not proof that subjects endorse the video's religious position, or a waiver of trademark/reputation restrictions. Avoid implying the stock person's individual faith or factual victimhood.

[YouTube's channel monetization policy](https://support.google.com/youtube/answer/1311392) distinguishes licensed stock use from monetizable original value: avoid stock montages with little transformation; preserve original narrative, commentary, editorial pacing, voice rights and substantively unique film language. Never claim monetization entitlement from a Pexels license.

Audio runtime rights and backing-music rights are independent from visual approval. Every shot being approved is necessary but not sufficient for the master; release and publication are separate gates.

## Implementation and evidence

- Source of truth: contracts/e01_director_editorial_decisions_v1.json (seven final verdicts, scene IDs, original source SHA-256 hashes, independent run URLs and rationale).
- Enforcer: agents/e01_editorial_director_gate.py is **fail closed**; it confirms original 182-word script/narration hashes, exact shot IDs, source hashes, editorial outcomes, score thresholds, previous conditional decision and all release=false.
- Connected to **agents/e01_visual_single_world_gate.py** so the project's single-world plan cannot pass if final verdicts are deleted or silently converted to APPROVED.
- Connected to GitHub Engine Gates as a separate executable CI step plus adversarial unit tests. Acceptance of new real cinematography must use a deliberate **new review contract/version**, never retroactively rewrite this historical verdict or relax the gate.
- No file in the older physical-probe contracts was deleted or rewritten, preserving audit and rollback.
- No merge to main, no publication, no production spend, no changing script/WAV/28 captions.
