from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from publisher.cli import browser_package, diagnostic_package, report
from publisher.core import (
    BRANDING_CAPTION_MARGIN_V,
    BRANDING_FORMAT,
    BRANDING_LOGO_POSITION,
    BRANDING_VERSION,
    DAY_PERIOD_HOURS,
    MANIFEST_VERSION,
    NIGHT_PERIOD_HOURS,
    TIKTOK_CAPTION_LIMIT,
    TIKTOK_HOURS,
    YOUTUBE_DESCRIPTION_LIMIT,
    YOUTUBE_HOURS,
    YOUTUBE_TITLE_LIMIT,
    assign_slots,
    build_title,
    copy_dict,
    copy_quality_issues,
    detect_topic,
    format_copy_text,
    local_publish_at,
    make_copy,
    natural_index,
    normalize_period,
    normalize_transcript,
    validate_credit_source,
    validate_manifest,
)
from publisher.google_io import normalize_folder_id, publication_day, publish_youtube, resolve_publication_folder
from publisher.tiktok_io import TikTokError, choose_privacy_level, publish_tiktok


def test_numbering_and_periods():
    assert natural_index("corte_fino_01_vertical.mp4") == 1
    assert natural_index("VIDEO - 05.mp4") == 5
    assert normalize_period("Bloco A") == "daily"
    assert normalize_period("evening") == "daily"


def test_slots_are_five_per_day_and_ranked():
    clips = [
        {"index": index, "copy": {"viral_score": float(index)}, "schedule": {}}
        for index in range(1, 6)
    ]
    assign_slots(clips, DAY_PERIOD_HOURS)
    assert sorted(clip["schedule"]["youtube_hour"] for clip in clips) == list(DAY_PERIOD_HOURS)
    assert sorted(clip["schedule"]["tiktok_hour"] for clip in clips) == list(DAY_PERIOD_HOURS)
    assert list(YOUTUBE_HOURS) == [10, 12, 14, 16, 18]
    assert TIKTOK_HOURS == YOUTUBE_HOURS
    strongest = max(clips, key=lambda item: item["copy"]["viral_score"])
    assert strongest["schedule"]["youtube_hour"] == 10


def test_copy_contract():
    pack = make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?",
        "Flow Podcast",
        "434",
    )
    assert pack.topic == "apostas"
    assert pack.youtube_title == pack.youtube_title.upper()
    assert len(pack.youtube_title) <= YOUTUBE_TITLE_LIMIT
    assert len(pack.tiktok_caption) <= TIKTOK_CAPTION_LIMIT
    assert len(pack.youtube_description) <= YOUTUBE_DESCRIPTION_LIMIT
    assert "Créditos: Flow Podcast, episódio 434." in pack.tiktok_caption
    assert "—" not in pack.tiktok_caption
    assert "#cortefino" not in pack.tiktok_caption.casefold()
    assert len(pack.youtube_tags) == 20
    assert copy_quality_issues(pack) == []


def test_copy_rejects_wrong_credit():
    assert validate_credit_source("Redcast Feminismo") == "Redcast Feminismo"
    with pytest.raises(ValueError, match="nunca use Corte Fino"):
        validate_credit_source("Corte Fino Publisher")
    with pytest.raises(ValueError, match="fonte original"):
        validate_credit_source("", required=True)


def test_copy_formatting_and_topic():
    assert detect_topic("O presidente falou do governo e o congresso respondeu.") == "politica"
    normalized = normalize_transcript("A politica e o casino prejudicam a audiencia.")
    assert normalized == "A política e o cassino prejudicam a audiência."
    assert format_copy_text("a frase começa,com erro . outra frase sem ponto", final_punctuation=True) == "A frase começa, com erro. Outra frase sem ponto."
    title = build_title("Bom, pessoal, essa é a verdade sobre responsabilidade", "geral")
    assert not title.startswith("BOM, PESSOAL")


def _valid_manifest():
    pack_a = copy_dict(make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?",
        "Canal A",
        "1",
    ))
    pack_b = copy_dict(make_copy(
        "A inteligência artificial está mudando o trabalho. O ser humano pode virar o gargalo quando a ferramenta substitui decisões.",
        "Canal B",
        "2",
    ))
    clips = []
    batches = [
        ("A", "folder-a", "2026-10-18", "daily", list(DAY_PERIOD_HOURS), pack_a),
        ("B", "folder-b", "2026-10-19", "daily", list(NIGHT_PERIOD_HOURS), pack_b),
    ]
    for batch_no, (batch_id, folder, day, period, hours, pack) in enumerate(batches):
        local = [
            {"index": batch_no * 5 + index, "batch_id": batch_id, "batch_index": index, "drive_folder_id": folder,
             "drive_id": f"drive-{batch_id}-{index}", "name": f"{batch_id}-{index:02d}.mp4",
             "size": 100000, "md5_checksum": f"md5-{batch_id}-{index}", "transcript": "transcrição validada com conteúdo suficiente",
             "copy": dict(pack), "schedule": {}}
            for index in range(1, 6)
        ]
        assign_slots(local, hours)
        for clip in local:
            at = local_publish_at(date.fromisoformat(day), clip["schedule"]["youtube_hour"])
            clip["schedule"]["youtube_publish_at"] = at
            clip["schedule"]["tiktok_publish_at"] = at
        clips.extend(local)
    return {
        "version": MANIFEST_VERSION,
        "run_id": "run-1",
        "date": "2026-10-18",
        "timezone": "America/Sao_Paulo",
        "drive_folder_id": "folder-a",
        "drive_folder_ids": ["folder-a", "folder-b"],
        "youtube_hours": list(YOUTUBE_HOURS),
        "tiktok_hours": list(TIKTOK_HOURS),
        "batches": [
            {"batch_id": "A", "drive_folder_id": "folder-a", "date": "2026-10-18", "period": "daily", "hours": list(DAY_PERIOD_HOURS), "source": {"name": "Canal A", "episode": "1"}},
            {"batch_id": "B", "drive_folder_id": "folder-b", "date": "2026-10-19", "period": "daily", "hours": list(NIGHT_PERIOD_HOURS), "source": {"name": "Canal B", "episode": "2"}},
        ],
        "rights": {"authorized": True, "status": "AUTORIZADO"},
        "source": {"name": "Canal A", "episode": "1"},
        "sources": [{"name": "Canal A", "episode": "1"}, {"name": "Canal B", "episode": "2"}],
        "branding": {"version": BRANDING_VERSION, "format": BRANDING_FORMAT, "logo_position": BRANDING_LOGO_POSITION, "caption_margin_v": BRANDING_CAPTION_MARGIN_V},
        "clips": clips,
    }


def test_manifest_v7_validates_ten_clips_across_two_days():
    validate_manifest(_valid_manifest())


def test_manifest_rejects_duplicate_slot():
    manifest = _valid_manifest()
    manifest["clips"][1]["schedule"]["youtube_publish_at"] = manifest["clips"][0]["schedule"]["youtube_publish_at"]
    manifest["clips"][1]["schedule"]["tiktok_publish_at"] = manifest["clips"][0]["schedule"]["tiktok_publish_at"]
    with pytest.raises(RuntimeError, match="conflito|duplicados"):
        validate_manifest(manifest)


def test_manifest_rejects_five_clip_or_old_manifest():
    manifest = _valid_manifest()
    manifest["clips"] = manifest["clips"][:5]
    with pytest.raises(RuntimeError, match="10 cortes"):
        validate_manifest(manifest)


def test_manifest_rejects_duplicate_drive_file():
    manifest = _valid_manifest()
    manifest["clips"][1]["drive_id"] = manifest["clips"][0]["drive_id"]
    with pytest.raises(RuntimeError, match="arquivo Drive duplicado"):
        validate_manifest(manifest)


def test_manifest_rejects_invalid_period():
    manifest = _valid_manifest()
    manifest["batches"][0]["period"] = "invalid"
    with pytest.raises(RuntimeError, match="Período inválido"):
        validate_manifest(manifest)


def test_manifest_rejects_two_batches_on_same_date():
    manifest = _valid_manifest()
    manifest["batches"][1]["date"] = manifest["batches"][0]["date"]
    with pytest.raises(RuntimeError, match="5 por dia exige datas diferentes"):
        validate_manifest(manifest)


def test_manifest_rejects_missing_source_or_rights():
    manifest = _valid_manifest()
    manifest["rights"]["authorized"] = False
    with pytest.raises(RuntimeError):
        validate_manifest(manifest, require_rights=True)
    manifest["source"]["name"] = "Corte Fino"
    with pytest.raises(RuntimeError, match="nunca use Corte Fino"):
        validate_manifest(manifest)


def test_manifest_rejects_source_crossed_between_batches():
    manifest = _valid_manifest()
    manifest["batches"][1]["source"]["name"] = "Canal A"
    with pytest.raises(RuntimeError, match="fontes declaradas"):
        validate_manifest(manifest)


def test_drive_link_is_hard_boundary():
    assert normalize_folder_id("https://drive.google.com/drive/folders/abc123?usp=sharing") == "abc123"
    assert normalize_folder_id("abc123") == "abc123"


def test_publication_day_boundary():
    tz = ZoneInfo("America/Sao_Paulo")
    assert publication_day(datetime(2026, 10, 17, 8, 59, tzinfo=tz)).isoformat() == "2026-10-17"
    assert publication_day(datetime(2026, 10, 17, 9, 0, tzinfo=tz)).isoformat() == "2026-10-18"


def test_privacy_level_is_explicit():
    assert choose_privacy_level({"privacy_level_options": ["PUBLIC_TO_EVERYONE", "SELF_ONLY"]}, "PUBLIC_TO_EVERYONE") == "PUBLIC_TO_EVERYONE"
    with pytest.raises(TikTokError):
        choose_privacy_level({"privacy_level_options": ["SELF_ONLY"]}, "PUBLIC_TO_EVERYONE")


def test_tiktok_api_publish_is_blocked_in_browser_only_mode(monkeypatch):
    monkeypatch.setenv("PUBLISHER_BROWSER_ONLY", "1")
    manifest = _valid_manifest()
    with pytest.raises(TikTokError, match="Cloud Web Browser"):
        publish_tiktok(manifest, due_only=True)


def test_youtube_api_publish_is_blocked_in_browser_only_mode(monkeypatch):
    monkeypatch.setenv("PUBLISHER_BROWSER_ONLY", "1")
    with pytest.raises(RuntimeError, match="Cloud Web Browser"):
        publish_youtube(_valid_manifest())


def test_youtube_dry_run_is_fully_local(monkeypatch):
    def fail_if_called():
        raise AssertionError("dry-run não pode abrir o Drive")

    monkeypatch.setattr("publisher.google_io.drive_service", fail_if_called)
    results = publish_youtube(_valid_manifest(), dry_run=True)
    assert len(results) == 10
    assert all(item["status"] == "dry_run" for item in results)


def test_browser_package_has_timezone_safe_studio_settings():
    package = browser_package(_valid_manifest())
    assert package["version"] == 3
    assert package["rights_authorized"] is True
    assert len(package["posts"]) == 10
    first = package["posts"][0]
    assert first["drive_folder_url"].startswith("https://drive.google.com/drive/folders/")
    assert first["youtube"]["publication_mode"] == "schedule"
    assert first["youtube"]["made_for_kids"] is False
    assert first["youtube"]["contains_synthetic_media"] is False
    assert first["tiktok"]["visibility"] == "PUBLIC_TO_EVERYONE"
    assert first["tiktok"]["visibility_label"] == "Todos (público)"
    assert first["tiktok"]["privacy_check"] == "required_before_schedule"
    assert first["tiktok"]["verify_after_publish"] is True
    assert first["youtube"]["publish_at_local"].endswith(":00")


def test_distribution_guard_builds_three_post_control():
    package = diagnostic_package(_valid_manifest())
    assert package["version"] == 4
    assert package["mode"] == "distribution_diagnostic"
    assert package["expected_posts"] == 3
    assert len(package["posts"]) == 3
    assert len({post["batch_id"] for post in package["posts"]}) == 1
    assert [post["diagnostic_slot"][-5:] for post in package["posts"]] == ["11:30", "16:30", "20:30"]
    for post in package["posts"]:
        assert post["youtube"]["publication_mode"] == "manual_controlled_test"
        assert post["youtube"]["tags_count"] == 20
        assert "shown_in_feed_after_24h" in post["youtube"]["post_publish_checks"]
        assert post["tiktok"]["privacy_check"] == "required_before_publish"
        assert "for_you_eligibility" in post["tiktok"]["post_publish_checks"]
        assert "originality_or_reuse_notice" in post["tiktok"]["post_publish_checks"]


def test_copy_qa_rejects_template_language():
    pack = make_copy(
        "A inteligência artificial está mudando o trabalho e pode substituir algumas decisões humanas.",
        "Canal Teste",
        "1",
    )
    pack.youtube_description = (
        "Uma conversa do convidado que provoca reflexão e merece ser ouvida até o fim.\n\n"
        + pack.youtube_description
    )
    issues = copy_quality_issues(pack)
    assert any("frase genérica proibida" in issue for issue in issues)


def test_browser_package_blocks_unconfirmed_rights():
    manifest = _valid_manifest()
    manifest["rights"]["authorized"] = False
    with pytest.raises(RuntimeError, match="direitos não confirmados"):
        browser_package(manifest)


def test_manifest_reports_malformed_schedule_without_crashing():
    manifest = _valid_manifest()
    manifest["clips"][0]["schedule"] = "invalid"
    with pytest.raises(RuntimeError, match="bloco de agendamento inválido"):
        validate_manifest(manifest)


def test_tiktok_dry_run_keeps_ten_scheduled_posts():
    manifest = _valid_manifest()
    results = publish_tiktok(manifest, dry_run=True)
    assert len(results) == 10
    assert {item["publish_at"][11:13] for item in results} == {"13", "15", "17", "19", "21"}


def test_report_contains_both_batches():
    data = report(_valid_manifest())
    assert len(data["youtube"]) == 10
    assert len(data["tiktok"]) == 10
    assert {item["batch_id"] for item in data["youtube"]} == {"A", "B"}
    assert {item["status"] for item in data["youtube"]} == {"pending_browser"}
    assert {item["status"] for item in data["tiktok"]} == {"pending_browser"}


def test_resolve_folder_rejects_extra_children():
    class FakeFiles:
        def list(self, **kwargs):
            class Request:
                def execute(self, **kwargs):
                    return {"files": [{"id": "1", "name": "01.mp4", "mimeType": "video/mp4"}] * 5 + [{"name": "extra.txt", "mimeType": "text/plain"}]}
            return Request()
    class FakeDrive:
        def __init__(self):
            self._files = FakeFiles()
        def files(self):
            return self._files
    with pytest.raises(RuntimeError, match="extras"):
        resolve_publication_folder(FakeDrive(), "folder")

