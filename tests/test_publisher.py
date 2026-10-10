from datetime import date, datetime
from zoneinfo import ZoneInfo

from publisher.core import YOUTUBE_HOURS, TIKTOK_HOURS, assign_slots, detect_topic, local_publish_at, make_copy, natural_index
from publisher.tiktok_io import publish_tiktok


def test_numbering():
    assert natural_index("corte_fino_01_vertical.mp4") == 1
    assert natural_index("VIDEO - 05.mp4") == 5


def test_bets_copy():
    pack = make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?"
    )
    assert pack.topic == "apostas"
    assert len(pack.youtube_title) <= 100
    assert pack.youtube_title == pack.youtube_title.upper()
    assert "#Apostas" in pack.tiktok_caption
    assert "#CorteFino" in pack.tiktok_caption
    assert "#Shorts" in pack.youtube_description
    assert "#Problema" not in pack.tiktok_caption
    assert pack.youtube_tags
    assert any("cassino" in tag.lower() for tag in pack.youtube_tags)
    assert sum(len(tag) for tag in pack.youtube_tags) + max(0, 2 * (len(pack.youtube_tags) - 1)) <= 500
    assert "A conversa coloca" not in pack.tiktok_caption


def test_five_slots_for_both_networks():
    clips = [
        {"index": index, "copy": {"viral_score": float(index)}, "schedule": {}}
        for index in range(1, 6)
    ]
    assign_slots(clips)
    assert sorted(clip["schedule"]["youtube_hour"] for clip in clips) == list(YOUTUBE_HOURS)
    assert sorted(clip["schedule"]["tiktok_hour"] for clip in clips) == list(TIKTOK_HOURS)


def test_politics():
    assert detect_topic("O presidente falou do governo e o congresso respondeu.") == "politica"


def test_general_copy_does_not_turn_transcription_noise_into_tags():
    pack = make_copy("E falo mais, Jikei, você tem sangue nas mãos, tá?")
    assert pack.topic == "geral"
    assert pack.tiktok_caption.endswith("#Debate #CorteFino #Shorts")
    assert all("jikei" not in tag.lower() for tag in pack.youtube_tags)


def test_timezone():
    assert "13:00:00" in local_publish_at(date(2026, 10, 10), 10)


def test_tiktok_dry_run_keeps_five_scheduled_posts():
    manifest = {
        "date": "2026-10-10",
        "clips": [
            {"index": index, "schedule": {"tiktok_hour": hour}, "copy": {"tiktok_caption": f"Legenda {index}"}}
            for index, hour in enumerate(TIKTOK_HOURS, 1)
        ],
    }
    result = publish_tiktok(manifest, dry_run=True)
    assert len(result) == 5
    assert [item["index"] for item in result] == [1, 2, 3, 4, 5]
    assert all(item["status"] == "dry_run" for item in result)


def test_tiktok_due_only_returns_one_post_for_the_current_window():
    manifest = {
        "date": "2026-10-10",
        "clips": [
            {"index": index, "schedule": {"tiktok_hour": hour}, "copy": {"tiktok_caption": f"Legenda {index}"}}
            for index, hour in enumerate(TIKTOK_HOURS, 1)
        ],
    }
    result = publish_tiktok(
        manifest,
        dry_run=True,
        due_only=True,
        now=datetime(2026, 10, 10, 10, 15, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert len(result) == 1
    assert result[0]["index"] == 1
