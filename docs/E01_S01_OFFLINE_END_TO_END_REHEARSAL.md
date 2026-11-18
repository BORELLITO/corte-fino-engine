# S01 end-to-end offline rehearsal — no free-GPU credits

**Reason:** the full render workflow previously had individual FFmpeg, Gradio payload, JSON and reference-frame tests, but no check that the *whole* provider-response-to-physical-MP4-to-five-frame-reference handoff actually worked. One live free ZeroGPU retry is pending, and false confidence would waste it.

New test `tests/test_e01_s01_gradio_end_to_end_offline.py` synthesizes a throwaway 5.85-second 480×848/24fps moving video test pattern with local FFmpeg, inserts a fake `gradio_client` in Python memory and invokes the REAL `agents/e01_ltx23_s01_v2_render.run()` implementation with a mocked provider runtime stage RUNNING. This exercises actual source copy, FFprobe, full FFmpeg decoding, SHA256, seven-ish JPG samples, exact report JSON and the REAL `make_candidate_frames()` producing five SHA256-pinned PNGs, temporal motion score and a contact sheet.

Adversarial cases: a provider that is paused **must make no Gradio request**, and a provider that returns no MP4 **must exit nonzero, save no-video report and create no reference frames**. All user/source/music/rights/scene approval flags remain false. No provider API is called, no user media is used, no credits consumed. The synthetic pattern is **not** a real E01 shot and is never added to the repository as footage or published.

Workflow `.github/workflows/verbo-no-chao-e01-s01-offline-e2e.yml` provisions FFmpeg in a dedicated runner to prevent the physical tests being skipped on a GitHub runner without codecs. It will prove production-chain software correctness, not external provider availability, free GPU quota, actor integrity, notebook/rain narrative fidelity or 1080×1920 master output. The scheduled one-shot public test is separate and remains unchanged.

Operational guideline: always preserve the **first live S01 MP4** if valid, but only approve it as canonical after the director visually checks actual first/last/middle frames, rain, closed notebook, actor anonymity, scene length, color, one-world continuity and source licence. Do not automatically repeat a failed public generation or release the master.
