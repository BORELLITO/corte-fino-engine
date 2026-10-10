from datetime import date, datetime
from zoneinfo import ZoneInfo

from publisher.cli import report
from publisher.core import YOUTUBE_HOURS, TIKTOK_HOURS, assign_slots, build_title, copy_quality_issues, detect_topic, local_publish_at, make_copy, natural_index, normalize_transcript
from publisher.google_io import normalize_folder_id, publication_day, reconcile_youtube_upload
from publisher.tiktok_io import choose_privacy_level, publish_tiktok
import publisher.tiktok_io as tiktok_io


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
    assert "#TikTok" in pack.tiktok_caption
    assert "#Shorts" not in pack.tiktok_caption
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
    assert pack.tiktok_caption.endswith("#Debate #CorteFino #TikTok")
    assert all("jikei" not in tag.lower() for tag in pack.youtube_tags)


def test_title_uses_the_strongest_hook():
    pack = make_copy("A casa sempre ganha. O problema é quando a pessoa perde tudo no vício de aposta.")
    assert "PERDE TUDO" in pack.youtube_title


def test_copy_editorial_qa_cleans_fillers_and_safe_spelling_errors():
    normalized = normalize_transcript("Bom, pessoal, a politica e o casino prejudicam a audiencia.")
    assert normalized == "Bom, pessoal, a política e o cassino prejudicam a audiência."
    title = build_title("Bom, pessoal, essa é a verdade sobre responsabilidade", "geral")
    assert not title.startswith("BOM, PESSOAL")
    assert "…" not in title
    assert copy_quality_issues(make_copy(normalized)) == []


def test_drive_folder_accepts_url_or_id():
    url = "https://drive.google.com/drive/folders/abc_123?usp=sharing"
    assert normalize_folder_id(url) == "abc_123"
    assert normalize_folder_id("abc_123") == "abc_123"


def test_publication_day_supports_boundary_and_manual_recovery_date():
    sao_paulo = ZoneInfo("America/Sao_Paulo")
    assert publication_day(datetime(2026, 10, 10, 8, 59, tzinfo=sao_paulo)) == date(2026, 10, 10)
    assert publication_day(datetime(2026, 10, 10, 9, 0, tzinfo=sao_paulo)) == date(2026, 10, 11)
    assert publication_day(target_date="2026-10-07") == date(2026, 10, 7)


def test_tiktok_privacy_level_is_explicit_and_available():
    creator = {"privacy_level_options": ["SELF_ONLY", "PUBLIC_TO_EVERYONE"]}
    assert choose_privacy_level(creator) == "PUBLIC_TO_EVERYONE"


def test_tiktok_existing_processing_id_is_reconciled_without_duplicate(monkeypatch):
    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Files:
        def get(self, **kwargs):
            return Request({"id": "drive-1", "appProperties": {"cf_tiktok_publish_id": "publish-1"}})

    class Drive:
        def files(self):
            return Files()

    manifest = {
        "date": "2026-10-10",
        "clips": [{
            "index": 1,
            "drive_id": "drive-1",
            "schedule": {"tiktok_hour": 10},
            "copy": {"tiktok_caption": "Legenda de teste"},
        }],
    }
    markers = []
    monkeypatch.setattr(tiktok_io, "_refresh_access_token", lambda: "token")
    monkeypatch.setattr(tiktok_io, "_creator_info", lambda token: {"privacy_level_options": ["PUBLIC_TO_EVERYONE"]})
    monkeypatch.setattr(tiktok_io, "drive_service", lambda: Drive())
    monkeypatch.setattr(tiktok_io, "_wait_for_publish", lambda token, publish_id: ("PROCESSING", {"status": "PROCESSING"}))
    monkeypatch.setattr(tiktok_io, "marker", lambda drive, file_id, values: markers.append(values))
    monkeypatch.setattr(tiktok_io, "_post_clip", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deve criar outro post")))

    result = publish_tiktok(manifest, due_only=True)
    assert result == [{"index": 1, "status": "PROCESSING", "publish_id": "publish-1"}]
    assert markers == [{"cf_tiktok_status": "PROCESSING", "cf_tiktok_date": "2026-10-10"}]


def test_youtube_reconciliation_finds_recent_exact_title():
    class Request:
        def execute(self, **kwargs):
            return {"items": [{
                "id": {"videoId": "youtube-1"},
                "snippet": {"title": "TÍTULO FORTE", "publishedAt": "2026-10-10T12:00:00Z"},
            }]}

    class Search:
        def list(self, **kwargs):
            return Request()

    class YouTube:
        def search(self):
            return Search()

    assert reconcile_youtube_upload(YouTube(), "TÍTULO FORTE", "2026-10-10T11:55:00Z") == "youtube-1"


def test_report_exposes_remote_states_and_attention_count():
    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Files:
        def get(self, **kwargs):
            states = {
                "drive-y": {"cf_youtube_video_id": "youtube-1", "cf_youtube_upload_status": "SCHEDULED"},
                "drive-t": {"cf_tiktok_publish_id": "tiktok-1", "cf_tiktok_status": "PROCESSING"},
            }
            return Request({"appProperties": states[kwargs["fileId"]]})

    class Drive:
        def files(self):
            return Files()

    manifest = {
        "date": "2026-10-10",
        "timezone": "America/Sao_Paulo",
        "clips": [
            {"index": 1, "drive_id": "drive-y", "schedule": {"youtube_hour": 10, "tiktok_hour": 10}, "copy": {"youtube_title": "Título", "tiktok_caption": "Legenda"}},
            {"index": 2, "drive_id": "drive-t", "schedule": {"youtube_hour": 12, "tiktok_hour": 12}, "copy": {"youtube_title": "Título 2", "tiktok_caption": "Legenda 2"}},
        ],
    }
    data = report(manifest, drive=Drive())
    assert data["youtube"][0]["status"] == "scheduled"
    assert data["tiktok"][1]["status"] == "PROCESSING"
    assert data["summary"]["attention"] == 0


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
