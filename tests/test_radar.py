from datetime import datetime, timezone

from radar.corte_fino_radar import (
    QuerySignal,
    VideoCandidate,
    build_queries,
    comment_analysis,
    finalize_score,
    is_political,
    parse_iso8601_duration,
    parse_traffic,
    query_gap_score,
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
        "Cortes do Flow",
        "Cortes do Inteligência",
        "RedCast",
        "Podpah",
    ]
