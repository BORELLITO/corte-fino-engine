import json

import radar.corte_fino_radar as radar_module
from datetime import datetime, timedelta, timezone

from radar.upload_reports_drive import normalize_folder_id

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
    preferred_source,
    query_gap_score,
    safe_url_label,
    term_hits,
    write_outputs,
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



def test_preferred_source_does_not_trust_lookalike_channel():
    assert preferred_source("Flow Podcast")
    assert preferred_source("RedCast [Oficial]")
    assert not preferred_source("Flow Podcast Fan Clips")
    assert not preferred_source("Meu Canal de Flow Podcast")


def test_momentum_real_interval_can_detect_acceleration():
    now = datetime.now(timezone.utc)
    candidate = VideoCandidate(
        video_id="momentum",
        title="Podcast",
        channel_title="Canal",
        channel_id="UC_M",
        category_id="22",
        made_for_kids=False,
        published_at=(now - timedelta(hours=12)).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=9000,
        like_count=200,
        comment_count=150,
        youtube_license="youtube",
        views_per_hour=750,
    )
    state = {
        "videos": {
            "momentum": [
                {
                    "ts": (now - timedelta(hours=6)).isoformat(),
                    "views": 3000,
                    "comments": 60,
                    "likes": 100,
                },
                {
                    "ts": (now - timedelta(hours=3)).isoformat(),
                    "views": 4500,
                    "comments": 80,
                    "likes": 120,
                },
            ]
        }
    }
    apply_momentum([candidate], state, now)
    assert candidate.recent_views_per_hour == 1500
    assert candidate.acceleration_ratio > 2
    assert candidate.momentum_state == "ACCELERATING"
    assert candidate.momentum_score > 50



def test_drive_folder_id_normalization():
    assert normalize_folder_id("abc123") == "abc123"
    assert normalize_folder_id(
        "https://drive.google.com/drive/folders/abc123?usp=sharing"
    ) == "abc123"



def test_short_semantic_terms_use_word_boundaries():
    assert term_hits("Felca fala sobre apostas", {"fe"}) == 0
    assert term_hits("Ele fala de fé e família", {"fe", "fé"}) == 1



def test_previous_score_is_loaded_from_state():
    now = datetime.now(timezone.utc)
    candidate = VideoCandidate(
        video_id="score-delta",
        title="Podcast",
        channel_title="Canal",
        channel_id="UC_SCORE",
        category_id="22",
        made_for_kids=False,
        published_at=(now - timedelta(hours=10)).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=10000,
        like_count=500,
        comment_count=300,
        youtube_license="youtube",
        views_per_hour=1000,
    )
    state = {
        "videos": {
            "score-delta": [
                {
                    "ts": (now - timedelta(hours=4)).isoformat(),
                    "views": 7000,
                    "comments": 200,
                    "likes": 400,
                    "score": 61.5,
                    "status": "PROMISING",
                }
            ]
        }
    }
    apply_momentum([candidate], state, now)
    assert candidate.previous_score == 61.5



def test_human_report_is_compact_and_local_time(tmp_path, monkeypatch):
    monkeypatch.setattr(radar_module, "OUTPUT_DIR", tmp_path)
    candidate = VideoCandidate(
        video_id="top1",
        title="Debate emocional",
        channel_title="Flow Podcast",
        channel_id="UC_FLOW",
        category_id="22",
        made_for_kids=False,
        published_at="2026-10-17T12:00:00+00:00",
        description="",
        duration_seconds=3600,
        view_count=250000,
        like_count=10000,
        comment_count=2500,
        youtube_license="youtube",
        source_queries=["relacionamento traição casamento"],
        radar_score=72.5,
        rank_status="HOT",
        momentum_state="RISING",
        momentum_score=70,
        confidence_score=75,
        cutability_score=80,
        velocity_score=80,
        controversy_score=70,
        emotion_score=60,
        source_score=100,
    )
    signal = QuerySignal(
        query="relacionamento traição casamento",
        source="editorial_theme",
        youtube_total_results=1000,
        gap_score=55,
    )
    write_outputs(
        [candidate],
        [],
        [signal],
        top_n=5,
        generated_at=datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc),
    )
    report = (tmp_path / "radar_latest.md").read_text(encoding="utf-8")
    assert "17/10/2026 12:00 BRT" in report
    assert "## 🔥 Top 5" in report
    assert "## 🔎 Hipóteses de Search Gap" not in report
    assert "## 🗳️ Watchlist" not in report
    assert "## ⚠️ Regras de uso" not in report
    payload = json.loads(
        (tmp_path / "radar_latest.json").read_text(encoding="utf-8")
    )
    assert payload["search_gaps"][0]["query"] == "relacionamento traição casamento"


def test_output_hard_locks_to_five(tmp_path, monkeypatch):
    monkeypatch.setattr(radar_module, "OUTPUT_DIR", tmp_path)
    candidates = []
    for idx in range(7):
        candidates.append(
            VideoCandidate(
                video_id=f"v{idx}",
                title=f"Podcast {idx}",
                channel_title="Flow Podcast",
                channel_id="UC_FLOW",
                category_id="22",
                made_for_kids=False,
                published_at="2026-10-17T12:00:00+00:00",
                description="",
                duration_seconds=3600,
                view_count=100000 + idx,
                like_count=1000,
                comment_count=500,
                youtube_license="youtube",
                radar_score=80 - idx,
                rank_status="HOT",
            )
        )
    write_outputs(
        candidates,
        [],
        [],
        top_n=5,
        generated_at=datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc),
    )
    payload = json.loads(
        (tmp_path / "radar_latest.json").read_text(encoding="utf-8")
    )
    assert len(payload["ranked_nonpolitical"]) == 5



def test_weak_comment_heat_without_semantic_tension_is_dropped():
    candidate = VideoCandidate(
        video_id="weak-comments",
        title="Podcast genérico",
        channel_title="Canal",
        channel_id="UC_WEAK",
        category_id="22",
        made_for_kids=False,
        published_at=datetime.now(timezone.utc).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=100000,
        like_count=5000,
        comment_count=1000,
        youtube_license="youtube",
        political_or_electoral=False,
        velocity_score=90,
        engagement_score=80,
        comment_heat_score=22,
        comment_divergence=True,
        controversy_score=0,
        emotion_score=0,
        chapter_heat_score=0,
        search_gap_score=80,
        freshness_score=90,
        source_score=100,
        momentum_score=70,
        breakout_score=90,
        cutability_score=70,
    )
    finalize_score(candidate)
    assert candidate.radar_score is None
    assert candidate.rank_status == "DROP"


def test_strong_organic_comment_conflict_can_pass_without_keywords():
    candidate = VideoCandidate(
        video_id="organic-conflict",
        title="Podcast com conflito orgânico",
        channel_title="Canal",
        channel_id="UC_ORGANIC",
        category_id="22",
        made_for_kids=False,
        published_at=datetime.now(timezone.utc).isoformat(),
        description="",
        duration_seconds=3600,
        view_count=100000,
        like_count=5000,
        comment_count=3000,
        youtube_license="youtube",
        political_or_electoral=False,
        velocity_score=95,
        engagement_score=90,
        comment_heat_score=55,
        comment_divergence=True,
        controversy_score=0,
        emotion_score=0,
        chapter_heat_score=0,
        search_gap_score=50,
        freshness_score=90,
        source_score=25,
        momentum_score=80,
        breakout_score=90,
        cutability_score=70,
    )
    finalize_score(candidate)
    assert candidate.radar_score is not None
