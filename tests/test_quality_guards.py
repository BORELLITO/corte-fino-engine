from main import (
    CAPTION_ALLOWED_TOKENS,
    CAPTION_MARGIN_V,
    CAPTION_MAX_CPS,
    Candidate,
    Segment,
    caption_chunks,
    caption_layout,
    correct_caption_word,
    repair_short_caption_chunks,
    caption_spelling_issues,
    caption_spelling_warnings,
    enrich_clip,
    rights_info,
    build_filter_complex,
    VIDEO_AUDIO_BITRATE,
    VIDEO_AUDIO_MIN_BITRATE,
    VIDEO_BITRATE,
    VIDEO_BUFSIZE,
    VIDEO_CRF,
    VIDEO_MAXRATE,
    VIDEO_MINRATE,
    VIDEO_MIN_BITRATE,
    VIDEO_PRESET,
    LOGO_PATH,
    CLIP_DURATION_FLOOR_SECONDS,
    MIN_CLIP_SECONDS,
    MAX_CLIP_SECONDS,
    TARGET_CLIP_SECONDS,
    clip_duration_is_valid,
    caption_orthography_issues,
    contextual_correct_caption_word,
    build_candidates,
    narrative_quality,
    build_story_map,
    validate_narrative,
)


def test_caption_gate_flags_known_asr_error():
    assert "médo" in caption_spelling_issues(["Médo"])


def test_caption_safe_corrections_are_explicit_and_punctuation_safe():
    assert correct_caption_word("Médo") == "Medo"
    assert correct_caption_word("violins") == "Aviões"
    assert correct_caption_word("violins,") == "Aviões,"
    assert correct_caption_word("panoís") == "panoís"


def test_caption_context_repairs_asr_word_and_restores_natural_case():
    assert correct_caption_word("BALRRACHARIA") == "borracharia"
    assert contextual_correct_caption_word("balrracharia") == "borracharia"
    assert contextual_correct_caption_word("acontesimento", {}, "o", "foi") == "acontecimento"
    assert contextual_correct_caption_word("stf") == "STF"
    assert contextual_correct_caption_word(
        "BALRRACHARIA",
        {"title": "Lito", "channel": "Flow", "niche": "ciência e conhecimento"},
    ) == "borracharia"


def test_caption_revision_uses_contextual_spelling_and_source_terminal_punctuation():
    from main import caption_chunks

    words = [
        {"start": 0.0, "end": 0.35, "word": "BALRRACHARIA"},
        {"start": 0.35, "end": 0.70, "word": "NO"},
        {"start": 0.70, "end": 1.10, "word": "CEU"},
    ]
    chunks = caption_chunks(
        [Segment(0.0, 1.2, "BALRRACHARIA NO CEU.", words)],
        Candidate(0.0, 2.0, "BALRRACHARIA NO CEU.", 90),
        {"title": "Lito", "channel": "Flow", "niche": "ciência e conhecimento"},
    )
    rendered = " ".join(item["word"] for chunk in chunks for item in chunk)
    assert rendered == "Borracharia no céu."


def test_caption_punctuation_uses_pauses_without_punctuation_spam():
    from main import caption_chunks

    words = [
        {"start": 0.0, "end": 0.30, "word": "isso"},
        {"start": 0.30, "end": 0.60, "word": "é"},
        {"start": 0.60, "end": 0.90, "word": "importante"},
        {"start": 2.30, "end": 2.60, "word": "mesmo"},
    ]
    chunks = caption_chunks(
        [Segment(0.0, 2.8, "isso é importante mesmo.", words)],
        Candidate(0.0, 3.0, "isso é importante mesmo.", 90),
    )
    rendered = " ".join(item["word"] for chunk in chunks for item in chunk)
    assert rendered == "Isso é importante. Mesmo."
    assert ",," not in rendered


def test_short_caption_tail_is_joined_without_breaking_safe_layout():
    chunks = [
        [
            {"start": 53.92, "end": 54.2, "word": "a"},
            {"start": 54.2, "end": 54.5, "word": "gente"},
            {"start": 54.5, "end": 54.7, "word": "vai"},
            {"start": 54.7, "end": 54.8, "word": "lavar"},
            {"start": 54.8, "end": 54.9, "word": "roupa"},
            {"start": 54.9, "end": 55.0, "word": "suja"},
        ],
        [{"start": 55.0, "end": 55.22, "word": "lá?"}],
    ]
    repaired = repair_short_caption_chunks(chunks)
    assert len(repaired) == 1
    assert repaired[0][-1]["word"] == "lá?"


def test_caption_gate_does_not_block_names_slang_or_valid_loanwords():
    labels = ["Bianquinha", "tigrinho", "bets", "descredibilizar", "bloqueava", "consegui"]
    assert caption_spelling_issues(labels) == []
    assert caption_spelling_warnings(labels) == []


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


def test_local_input_folder_uses_the_most_recent_mp4(monkeypatch, tmp_path):
    import os
    import main as engine

    old_source = tmp_path / "old.mp4"
    new_source = tmp_path / "new.mp4"
    old_source.write_bytes(b"old")
    new_source.write_bytes(b"new")
    os.utime(old_source, (100, 100))
    os.utime(new_source, (200, 200))
    monkeypatch.setattr(engine, "SOURCE_DIR", tmp_path)
    monkeypatch.delenv("SOURCE_FILE", raising=False)
    monkeypatch.delenv("SOURCE_URL", raising=False)
    source, info = engine.obtain_source(None)
    assert source == new_source
    assert info["channel"] == "Entrada local"


def test_top_five_is_closed():
    from main import MAX_CLIPS, REQUIRE_EXACT_TOP_FIVE
    assert REQUIRE_EXACT_TOP_FIVE is True
    assert MAX_CLIPS == 5


def test_clip_duration_contract_is_strictly_over_sixty_seconds():
    assert CLIP_DURATION_FLOOR_SECONDS == 60.0
    assert MIN_CLIP_SECONDS >= 61
    assert MIN_CLIP_SECONDS > CLIP_DURATION_FLOOR_SECONDS
    assert MIN_CLIP_SECONDS <= TARGET_CLIP_SECONDS <= MAX_CLIP_SECONDS
    assert clip_duration_is_valid(60.0) is False
    assert clip_duration_is_valid(60.01) is True
    assert clip_duration_is_valid(float(MIN_CLIP_SECONDS)) is True
    assert clip_duration_is_valid(float(MAX_CLIP_SECONDS)) is True
    assert clip_duration_is_valid(float(MAX_CLIP_SECONDS) + 0.01) is False
    assert clip_duration_is_valid(60.0, 61.0) is False
    assert clip_duration_is_valid(61.0, 61.0) is True


def test_caption_orthography_gate_keeps_case_accents_and_spacing_clean():
    words = [
        {"start": 0.0, "end": 0.3, "word": "essa"},
        {"start": 0.3, "end": 0.6, "word": "é"},
        {"start": 0.6, "end": 0.9, "word": "uma"},
        {"start": 0.9, "end": 1.2, "word": "você"},
        {"start": 1.2, "end": 1.5, "word": "entendeu?"},
        {"start": 2.5, "end": 2.8, "word": "voce"},
        {"start": 2.8, "end": 3.1, "word": "agora."},
    ]
    from main import capitalize_caption_sentence_starts
    capitalize_caption_sentence_starts(words)
    assert [item["word"] for item in words] == [
        "Essa", "é", "uma", "você", "entendeu?", "Você", "agora."
    ]
    assert caption_orthography_issues(words) == []


def test_narrative_gate_requires_autonomous_start_context_and_closure():
    complete = [
        Segment(
            0, 22,
            "A história começa quando o convidado explica o problema que ninguém queria discutir.",
            [],
        ),
        Segment(
            22, 44,
            "Depois ele mostra os fatos, apresenta o conflito principal e explica por que aquela decisão mudou o resultado para muita gente.",
            [],
        ),
        Segment(
            44, 66,
            "No fim, ele revela a consequência mais importante e fecha a ideia dizendo que a responsabilidade continua sendo de quem escolhe.",
            [],
        ),
    ]
    quality = narrative_quality(complete, 0, 3)
    assert quality["passed"] is True
    assert quality["word_count"] >= 45
    assert quality["sentence_count"] >= 2
    assert quality["natural_start"] is True
    assert quality["natural_end"] is True
    assert quality["terminal_ending"] is True
    assert quality["arc_analysis"]["structure_score"] > 0

    dependent = [
        complete[0],
        Segment(
            22, 44,
            "porque o convidado mostra os fatos e apresenta o conflito principal da discussão.",
            [],
        ),
        complete[2],
    ]
    dependent_quality = narrative_quality(dependent, 1, 3)
    assert dependent_quality["passed"] is False
    assert any("meio de uma ideia" in issue for issue in dependent_quality["issues"])

    incomplete = [
        complete[0],
        Segment(
            22, 66,
            "Depois ele mostra os fatos, apresenta o conflito principal e termina de",
            [],
        ),
    ]
    incomplete_quality = narrative_quality(incomplete, 0, 2)
    assert incomplete_quality["passed"] is False
    assert any("palavra dependente" in issue for issue in incomplete_quality["issues"])


def test_candidate_builder_can_close_on_the_last_transcript_segment():
    segments = [
        Segment(0, 22, "A história começa quando o convidado explica o problema que ninguém queria discutir.", []),
        Segment(22, 44, "Depois ele mostra os fatos, apresenta o conflito principal e explica por que aquela decisão mudou o resultado para muita gente.", []),
        Segment(44, 66, "No fim, ele revela a consequência mais importante e fecha a ideia dizendo que a responsabilidade continua sendo de quem escolhe.", []),
    ]
    candidates = build_candidates(segments, {})
    assert any(candidate.end == 66 for candidate in candidates)


def test_narrative_does_not_treat_silence_or_transcript_end_as_conclusion():
    dangling = [
        Segment(
            0, 22,
            "A história começa quando o convidado explica o problema que ninguém queria discutir.",
            [],
        ),
        Segment(
            22, 44,
            "Depois ele mostra os fatos, apresenta o conflito principal e explica por que aquela decisão mudou o resultado.",
            [],
        ),
        Segment(
            44, 66,
            "No fim, ele revela o que aconteceu e continua falando sobre",
            [],
        ),
    ]
    quality = narrative_quality(dangling, 0, 3)
    assert quality["passed"] is False
    assert any("conclusão natural" in issue for issue in quality["issues"])


def test_narrative_allows_a_complete_pronoun_opening_with_editorial_warning():
    segments = [
        Segment(
            0, 22,
            "Ele explica o problema que ninguém queria discutir e mostra por que a decisão foi tomada.",
            [],
        ),
        Segment(
            22, 44,
            "Depois apresenta os fatos, compara as versões e detalha o conflito que mudou o resultado.",
            [],
        ),
        Segment(
            44, 66,
            "No fim, ele revela a consequência principal e conclui que a responsabilidade continua sendo de quem escolhe.",
            [],
        ),
    ]
    quality = narrative_quality(segments, 0, 3)
    assert quality["passed"] is True
    assert quality["contextual_pronoun_opening"] is True
    assert any("abertura pronominal" in warning for warning in quality["warnings"])


def test_narrative_relaxed_fallback_keeps_context_and_closure_gates():
    segments = [
        Segment(0, 22, "A história explica o problema que ninguém queria discutir e mostra por que a decisão foi tomada", []),
        Segment(22, 44, "Depois apresenta os fatos, compara as versões e detalha o conflito que mudou o resultado", []),
        Segment(44, 66, "Tudo terminou bem.", []),
    ]
    strict = narrative_quality(segments, 0, 3)
    relaxed = narrative_quality(segments, 0, 3, relaxed=True)
    assert strict["passed"] is False
    assert relaxed["passed"] is True
    assert relaxed["quality_mode"] == "relaxed_contextual_fallback"


def test_narrative_opening_uses_full_block_not_first_asr_fragment():
    segments = [
        Segment(0, 1.2, "A", []),
        Segment(1.2, 4.0, "história começa quando o convidado explica o problema que ninguém queria discutir.", []),
        Segment(4.0, 24.0, "Depois ele mostra os fatos, apresenta o conflito principal e explica por que aquela decisão mudou o resultado para muita gente.", []),
        Segment(24.0, 44.0, "No fim, ele revela a consequência mais importante e fecha a ideia dizendo que a responsabilidade continua sendo de quem escolhe.", []),
    ]
    quality = narrative_quality(segments, 0, 4)
    assert quality["passed"] is True
    assert quality["autonomous_start"] is True


def test_relaxed_narrative_accepts_real_pause_as_closure_but_not_transcript_end():
    segments = [
        Segment(0, 18, "A história começa quando o convidado explica o problema que ninguém queria discutir", []),
        Segment(18, 38, "Depois ele mostra os fatos, apresenta o conflito principal e explica o resultado", []),
        Segment(38, 58, "Essa foi a consequência para muita gente", []),
        Segment(59.0, 62.0, "Agora ele muda de", []),
    ]
    quality = narrative_quality(segments, 0, 3, relaxed=True)
    assert quality["passed"] is True
    assert quality["gap_closure"] is True
    assert quality["natural_end"] is True

    at_transcript_end = narrative_quality(segments, 0, 4, relaxed=True)
    assert at_transcript_end["passed"] is False


def test_coverage_fallback_keeps_context_without_terminal_punctuation():
    segments = [
        Segment(0, 18, "A história começa quando o convidado explica o problema que ninguém queria discutir", []),
        Segment(18, 38, "Depois ele mostra os fatos, apresenta o conflito principal e explica o resultado", []),
        Segment(38, 58, "Essa foi a consequência para muita gente", []),
        Segment(59.0, 62.0, "Agora ele muda de assunto.", []),
    ]
    quality = narrative_quality(segments, 0, 3, relaxed=True, coverage=True)
    assert quality["passed"] is True
    assert quality["quality_mode"] == "coverage_contextual_fallback"
    assert quality["coverage_closure"] is True


def test_story_map_reads_the_source_as_temporal_editorial_blocks():
    segments = [
        Segment(0, 18, "O governo anunciou uma medida importante para o país.", []),
        Segment(18, 38, "Depois, especialistas explicaram os efeitos dessa decisão.", []),
        Segment(38, 60, "No fim, a consequência pode atingir milhões de pessoas.", []),
    ]
    story_map = build_story_map(segments, window_seconds=30)
    assert len(story_map) >= 2
    assert all(block["key_terms"] for block in story_map)
    assert all("resolution_hits" in block for block in story_map)


def test_editorial_score_gate_keeps_candidates_above_threshold(monkeypatch):
    from main import Candidate, select_candidates
    import main as engine

    previous_gate = engine.USE_EDITORIAL_SCORE_GATE
    previous_minimum = engine.MIN_EDITORIAL_SCORE
    try:
        engine.USE_EDITORIAL_SCORE_GATE = True
        engine.MIN_EDITORIAL_SCORE = 0.0
        monkeypatch.setattr(engine, "validate_captions", lambda *args, **kwargs: {"passed": True})
        monkeypatch.setattr(engine, "validate_narrative", lambda *args, **kwargs: {"passed": True})
        monkeypatch.setattr(
            engine,
            "build_candidates",
            lambda *args, **kwargs: [
                Candidate(0, 61, "fala forte sobre política", 80.0),
                Candidate(70, 131, "fala forte sobre segurança", 70.0),
            ],
        )
        selected, candidates = select_candidates([], {})
        assert candidates
        assert selected
        assert all(candidate.accepted for candidate in selected)
        assert all(candidate.duration > 60 for candidate in selected)
    finally:
        engine.USE_EDITORIAL_SCORE_GATE = previous_gate
        engine.MIN_EDITORIAL_SCORE = previous_minimum




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


def test_output_encoding_profile_is_youtube_ready():
    assert VIDEO_CRF == 18
    assert VIDEO_PRESET == "medium"
    assert VIDEO_BITRATE == "8M"
    assert VIDEO_MINRATE == "6M"
    assert VIDEO_MAXRATE == "10M"
    assert VIDEO_BUFSIZE == "20M"
    assert VIDEO_MIN_BITRATE == 6000000
    assert VIDEO_AUDIO_BITRATE == "192k"
    assert VIDEO_AUDIO_MIN_BITRATE == 128000


def test_source_colors_are_preserved_and_hud_keeps_brand_palette():
    filter_complex = build_filter_complex("captions.ass")
    assert "saturation=0.22" not in filter_complex
    assert "saturation=0.80" not in filter_complex
    assert "gblur=sigma=22" in filter_complex
    assert "setsar=1" in filter_complex
    assert "flags=lanczos" in filter_complex
    assert "movie='" in filter_complex
    assert "corte_fino_logo.png" in filter_complex
    assert "loop=loop=-1" in filter_complex
    assert "drawbox=" not in filter_complex
    assert "drawtext=" not in filter_complex
    assert CAPTION_MARGIN_V == 430
    assert LOGO_PATH.name == "corte_fino_logo.png"


def test_caption_layout_respects_units_of_meaning():
    labels = "o governo anunciou uma nova medida importante".split()
    break_at, lengths = caption_layout(labels)
    assert break_at is not None
    left = " ".join(labels[:break_at])
    right = " ".join(labels[break_at:])
    assert not left.endswith((" de", " do", " da", " em", " para", " por"))
    assert not right.startswith(("de ", "do ", "da ", "em ", "para ", "por "))
    assert max(lengths) <= 32


def test_caption_quality_exposes_reading_speed_limit():
    assert CAPTION_MAX_CPS == 18.0


def test_caption_chunks_never_duplicate_words_when_splitting():
    words = [
        {"start": index * 0.12, "end": index * 0.12 + 0.08, "word": word}
        for index, word in enumerate("esta é uma legenda de teste para validar a logo oficial".split())
    ]
    text = " ".join(item["word"] for item in words)
    segment = Segment(start=0.0, end=2.0, text=text, words=words)
    candidate = Candidate(start=0.0, end=2.0, text=text, score=90)
    chunks = caption_chunks([segment], candidate)
    flattened = [item["word"] for chunk in chunks for item in chunk]
    assert flattened == ["Esta", "é", "uma", "legenda", "de", "teste", "para", "validar", "a", "logo", "oficial"]


def test_caption_sentence_after_punctuation_is_capitalized():
    segment = Segment(
        start=0.0,
        end=2.0,
        text="primeira frase. segunda frase.",
        words=[
            {"start": 0.0, "end": 0.8, "word": "primeira"},
            {"start": 0.8, "end": 1.0, "word": "frase."},
            {"start": 1.1, "end": 1.7, "word": "segunda"},
            {"start": 1.7, "end": 2.0, "word": "frase."},
        ],
    )
    chunks = caption_chunks([segment], Candidate(0.0, 2.0, segment.text, 90))
    assert [item["word"] for chunk in chunks for item in chunk] == [
        "Primeira", "frase.", "Segunda", "frase."
    ]

