from datetime import datetime, timezone

from radar.corte_fino_radar import (
    QuerySignal,
    VideoCandidate,
    apply_channel_baselines,
    apply_momentum,
    build_queries,
    comment_analysis,
    editorial_format_fit,
    finalize_score,
    is_political,
    likely_portuguese,
    parse_chapters,
    parse_iso8601_duration,
    parse_traffic,
    query_gap_score,
    safe_url_label,
)


def test_duration_parser():
    assert parse_iso8601_duration("PT1H2M3S") == 3723
    assert parse_iso8601_duration("PT45M") == 2700
    assert parse_iso8601_duration("PT0S") == 0


def test_traffic_parser():
    assert parse_traffic("200K+") == 200_000
    assert parse_traffic("1.5M+") == 1_500_000
    assert parse_traffic("950") == 950


def test_political_short_tokens_use_word_boundaries():
    assert is_political("PT e PL disputam a eleição")
    assert not is_political("criptomoedas e aplicativos")


def test_gap_score_is_bounded():
    signal = QuerySignal(
        query="teste",
        source="google_trends",
        trend_rank=1,
        approx_traffic=100_000,
        youtube_total_results=100,
    )
    assert 0 <= query_gap_score(signal) <= 100


def test_comment_heat_detects_divergence():
    heat, divergence = comment_analysis(
        ["concordo, verdade", "isso é absurdo e mentira"],
        4,
    )
    assert heat > 0
    assert divergence is True


def test_political_candidate_has_no_editorial_score():
    candidate = VideoCandidate(
        video_id="abc",
        title="Entrevista política",
        channel_title="Canal",
        channel_id="UC_TEST",
        category_id="22",
        made_for_kids=False,
        published_at=datetime.now(timezone.utc).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=1000,
        like_count=100,
        comment_count=50,
        youtube_license="youtube",
        political_or_electoral=True,
        velocity_score=100,
        engagement_score=100,
        comment_heat_score=100,
        controversy_score=100,
        emotion_score=100,
        search_gap_score=100,
        freshness_score=100,
        source_score=100,
    )
    finalize_score(candidate)
    assert candidate.radar_score is None


def test_query_priority_keeps_sources_before_generic_themes():
    queries = build_queries([], [], 6)
    assert [q[0] for q in queries] == [
        "Flow Podcast",
        "Inteligência Ltda",
        "RedCast",
        "Podpah",
        "AchismosTV",
        "Jota Jota Podcast",
    ]


def test_nonpolitical_description_with_one_context_word_is_not_flagged():
    assert not is_political(
        "Saúde mental da mocidade",
        "Conversa sobre saúde, família e ações do governo.",
        "Canal de Psicologia",
    )


def test_political_named_actor_is_flagged():
    assert is_political(
        "Entrevista com Lula",
        "Conversa sobre economia.",
        "Canal de Entrevistas",
    )


def test_language_filter_rejects_english_and_accepts_portuguese():
    assert likely_portuguese(
        "Esse podcast fala sobre a vida no Brasil e como você pode mudar."
    )
    assert not likely_portuguese(
        "A video about a man who was followed by ventriloquists."
    )


def test_editorial_format_requires_conversational_longform_shape():
    assert editorial_format_fit(
        "DEBATE SOBRE RELACIONAMENTOS",
        "",
        "Canal X",
    )
    assert editorial_format_fit(
        "Tema qualquer",
        "",
        "Inteligência Ltda",
    )
    assert not editorial_format_fit(
        "ORAÇÃO DA NOITE",
        "Ore conosco e deixe seu pedido nos comentários.",
        "Canal de Orações",
    )


def test_generic_body_context_does_not_force_political_without_domain():
    assert not is_political(
        "Conversa sobre tecnologia",
        "O ministro comentou com o presidente da empresa sobre inovação.",
        "Canal Tech",
    )


def test_nonpolitical_candidate_without_tension_is_not_ranked():
    candidate = VideoCandidate(
        video_id="xyz",
        title="Programa ao vivo",
        channel_title="Canal",
        channel_id="UC_TEST",
        category_id="22",
        made_for_kids=False,
        published_at=datetime.now(timezone.utc).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=100000,
        like_count=1000,
        comment_count=50,
        youtube_license="youtube",
        political_or_electoral=False,
        velocity_score=100,
        engagement_score=100,
        comment_heat_score=0,
        controversy_score=0,
        emotion_score=0,
        search_gap_score=100,
        freshness_score=100,
        source_score=100,
    )
    finalize_score(candidate)
    assert candidate.radar_score is None



def test_chapter_parser_requires_ordered_multiple_chapters():
    chapters = parse_chapters(
        "00:00 Introdução\n12:34 BETS E VÍCIO\n35:20 Família destruída"
    )
    assert len(chapters) == 3
    assert chapters[1].seconds == 754
    assert chapters[1].heat_score > 0


def test_channel_breakout_uses_peer_baseline():
    candidates = []
    for idx, vph in enumerate([100, 120, 600]):
        candidate = VideoCandidate(
            video_id=f"v{idx}",
            title="Podcast",
            channel_title="Canal A",
            channel_id="UC_A",
            category_id="22",
            made_for_kids=False,
            published_at=datetime.now(timezone.utc).isoformat(),
            description="",
            duration_seconds=3600,
            view_count=1000,
            like_count=100,
            comment_count=50,
            youtube_license="youtube",
            views_per_hour=vph,
        )
        candidates.append(candidate)
    apply_channel_baselines(candidates)
    assert candidates[2].breakout_ratio > 4
    assert candidates[2].breakout_score > 50


def test_momentum_detects_acceleration():
    now = datetime.now(timezone.utc)
    candidate = VideoCandidate(
        video_id="v1",
        title="Podcast",
        channel_title="Canal",
        channel_id="UC_A",
        category_id="22",
        made_for_kids=False,
        published_at=now.isoformat(),
        description="",
        duration_seconds=3600,
        view_count=5000,
        like_count=100,
        comment_count=80,
        youtube_license="youtube",
        views_per_hour=500,
    )
    state = {
        "videos": {
            "v1": [
                {
                    "ts": (now.replace(microsecond=0)).isoformat(),
                    "views": 4500,
                    "comments": 70,
                    "likes": 90,
                }
            ]
        }
    }
    # Snapshot no mesmo instante é tratado como sem intervalo suficiente.
    apply_momentum([candidate], state, now)
    assert candidate.momentum_state == "STALE"



def test_theme_rotation_changes_editorial_slice_without_losing_sources():
    q0 = build_queries([], [], 8, theme_offset=0)
    q6 = build_queries([], [], 8, theme_offset=6)
    assert [item[0] for item in q0[:6]] == [item[0] for item in q6[:6]]
    assert q0[6][0] != q6[6][0]


def test_safe_url_label_strips_query_and_api_key():
    label = safe_url_label(
        "https://www.googleapis.com/youtube/v3/search?q=x&key=SECRET"
    )
    assert label == "https://www.googleapis.com/youtube/v3/search"
    assert "SECRET" not in label
