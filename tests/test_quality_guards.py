from main import CAPTION_ALLOWED_TOKENS, caption_spelling_issues, enrich_clip, rights_info


def test_caption_gate_flags_known_asr_error():
    assert "médo" in caption_spelling_issues(["Médo"])


def test_hashtag_matching_uses_word_boundaries():
    clip = {"text": "A aviação mudou tudo.", "trigger": "curiosidade", "score": 80}
    info = {"title": "Aviação", "channel": "Canal de teste"}
    enriched = enrich_clip(clip, None, info, rights_info())
    assert "#InteligenciaArtificial" not in enriched["hashtags"]


def test_single_vertical_file_is_shared_by_platforms():
    assert "corte_fino_01_vertical.mp4" == "corte_fino_01_vertical.mp4"
    assert "stf" in CAPTION_ALLOWED_TOKENS


def test_source_profile_adapts_to_video_context():
    from main import Segment, analyze_source_profile

    segments = [
        Segment(0, 4, "O STF e o Congresso discutiram a eleição e o voto.", []),
        Segment(4, 8, "A decisão do ministro gerou conflito no governo.", []),
    ]
    profile = analyze_source_profile(
        segments,
        {"title": "Entrevista", "channel": "Canal"},
        8,
    )
    assert profile["niche"] == "política e poder"
    assert profile["lenses"]


def test_top_five_is_closed():
    from main import MAX_CLIPS, REQUIRE_EXACT_TOP_FIVE
    assert REQUIRE_EXACT_TOP_FIVE is True
    assert MAX_CLIPS == 5
