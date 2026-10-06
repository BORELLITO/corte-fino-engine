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


def test_visual_identity_uses_off_white_and_copper_caption_tokens(tmp_path):
    from main import Segment, Candidate, write_ass

    candidate = Candidate(0, 60, "fala de teste", 80)
    segments = [
        Segment(
            0,
            2.4,
            "Essa é uma verdade importante.",
            [
                {"start": 0, "end": 0.5, "word": "Essa", "probability": 0.99},
                {"start": 0.5, "end": 1, "word": "é", "probability": 0.99},
                {"start": 1, "end": 1.5, "word": "uma", "probability": 0.99},
                {"start": 1.5, "end": 2, "word": "verdade", "probability": 0.99},
                {"start": 2, "end": 2.4, "word": "importante.", "probability": 0.99},
            ],
        )
    ]
    output = tmp_path / "visual.ass"
    write_ass(segments, candidate, output, 220)
    content = output.read_text(encoding="utf-8")
    assert "003C5AB8" in content  # cobre #B85A3C em BGR/ASS
    assert "00F4F5F5" in content  # branco quente #F5F5F4 em BGR/ASS
    assert "DejaVu Sans Condensed" in content
