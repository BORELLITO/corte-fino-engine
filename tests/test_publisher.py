from datetime import date, datetime
from zoneinfo import ZoneInfo

from publisher.cli import report
from publisher.core import (TIKTOK_CAPTION_LIMIT, TIKTOK_HOURS, YOUTUBE_DESCRIPTION_LIMIT, YOUTUBE_HOURS, YOUTUBE_TITLE_LIMIT, assign_slots, build_title, copy_quality_issues, detect_topic, format_copy_text, local_publish_at, make_copy, natural_index, normalize_transcript)
from publisher.google_io import normalize_folder_id, publication_day, reconcile_youtube_upload, resolve_publication_folder, verify_manifest_clip, wait_youtube_processing
from publisher.tiktok_io import TikTokError, choose_privacy_level, publish_tiktok
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
    normalized = normalize_transcript("Bom, pessoal, a politica e o casino prejudicam a audiencia. O impacto aparece quando ninguém confere a informação.")
    assert normalized == "Bom, pessoal, a política e o cassino prejudicam a audiência. O impacto aparece quando ninguém confere a informação."
    title = build_title("Bom, pessoal, essa é a verdade sobre responsabilidade", "geral")
    assert not title.startswith("BOM, PESSOAL")
    assert "…" not in title
    assert copy_quality_issues(make_copy(normalized)) == []
    assert make_copy(normalized).evidence
    assert make_copy(normalized).cta


def test_copy_editorial_qa_normalizes_casino_gender_without_blocking():
    normalized = normalize_transcript(
        "A casino aparece na discussão sobre vício e responsabilidade. O debate mostra como o dinheiro muda decisões."
    )
    assert normalized.startswith("O cassino")
    assert copy_quality_issues(make_copy(normalized)) == []


def test_copy_formatting_enforces_sentence_case_and_platform_limits():
    formatted = format_copy_text(
        "a frase começa,com erro . outra frase sem ponto",
        final_punctuation=True,
    )
    assert formatted == "A frase começa, com erro. Outra frase sem ponto."

    pack = make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?"
    )
    assert pack.youtube_title == pack.youtube_title.upper()
    assert len(pack.youtube_title) <= YOUTUBE_TITLE_LIMIT
    assert len(pack.tiktok_caption) <= TIKTOK_CAPTION_LIMIT
    assert len(pack.youtube_description) <= YOUTUBE_DESCRIPTION_LIMIT
    assert "  " not in pack.tiktok_caption
    assert "  " not in pack.youtube_description


def test_drive_folder_accepts_url_or_id():
    url = "https://drive.google.com/drive/folders/abc_123?usp=sharing"
    assert normalize_folder_id(url) == "abc_123"
    assert normalize_folder_id("abc_123") == "abc_123"


def test_drive_link_is_hard_content_boundary():
    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Files:
        def list(self, **kwargs):
            query = kwargs["q"]
            if "mimeType = 'video/mp4'" in query:
                return Request({"files": [{"id": f"video-{index}", "name": f"fonte - {index:02d}.mp4"} for index in range(1, 6)]})
            raise AssertionError("o Publisher não pode procurar subpastas")

    class Drive:
        def files(self):
            return Files()

    assert resolve_publication_folder(Drive(), "exact-folder") == "exact-folder"


def test_drive_parent_without_direct_videos_is_rejected():
    class Request:
        def execute(self, **kwargs):
            return {"files": []}

    class Files:
        def list(self, **kwargs):
            return Request()

    class Drive:
        def files(self):
            return Files()

    try:
        resolve_publication_folder(Drive(), "parent-folder")
    except RuntimeError as error:
        assert "diretamente exatamente os 5 vídeos" in str(error)
    else:
        raise AssertionError("uma pasta sem os cinco MP4s diretos deve bloquear a publicação")


def test_manifest_file_mutation_is_blocked_before_publication():
    class Request:
        def execute(self, **kwargs):
            return {
                "id": "drive-1",
                "name": "lote - 01.mp4",
                "size": 999,
                "mimeType": "video/mp4",
                "md5Checksum": "new-checksum",
                "parents": ["folder-1"],
                "trashed": False,
                "appProperties": {},
            }

    class Files:
        def get(self, **kwargs):
            return Request()

    class Drive:
        def files(self):
            return Files()

    manifest = {"drive_folder_id": "folder-1"}
    clip = {
        "index": 1,
        "drive_id": "drive-1",
        "name": "lote - 01.mp4",
        "size": 100,
        "md5_checksum": "old-checksum",
    }
    try:
        verify_manifest_clip(Drive(), manifest, clip)
    except RuntimeError as error:
        assert "mudou" in str(error)
    else:
        raise AssertionError("arquivo alterado depois do preparo deve ser bloqueado")


def test_publication_day_supports_boundary_and_manual_recovery_date():
    sao_paulo = ZoneInfo("America/Sao_Paulo")
    assert publication_day(datetime(2026, 10, 10, 8, 59, tzinfo=sao_paulo)) == date(2026, 10, 10)
    assert publication_day(datetime(2026, 10, 10, 9, 0, tzinfo=sao_paulo)) == date(2026, 10, 11)
    assert publication_day(target_date="2026-10-07") == date(2026, 10, 7)


def test_tiktok_privacy_level_is_explicit_and_available(monkeypatch):
    creator = {"privacy_level_options": ["SELF_ONLY", "PUBLIC_TO_EVERYONE"]}
    assert choose_privacy_level(creator) == "PUBLIC_TO_EVERYONE"
    monkeypatch.setenv("PUBLISHER_TIKTOK_ENV", "sandbox")
    monkeypatch.setenv("PUBLISHER_TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")
    assert choose_privacy_level(creator) == "SELF_ONLY"


def test_tiktok_existing_processing_id_is_reconciled_without_duplicate(monkeypatch):
    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Files:
        def get(self, **kwargs):
            return Request({
                "id": "drive-1",
                "name": "fonte - 01.mp4",
                "size": 100,
                "mimeType": "video/mp4",
                "md5Checksum": "abc",
                "parents": ["folder-1"],
                "appProperties": {"cf_tiktok_publish_id": "publish-1"},
            })

    class Drive:
        def files(self):
            return Files()

    manifest = {
        "date": "2026-10-10",
        "drive_folder_id": "folder-1",
        "clips": [{
            "index": 1,
            "drive_id": "drive-1",
            "name": "fonte - 01.mp4",
            "size": 100,
            "md5_checksum": "abc",
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


def test_tiktok_immediate_publish_is_blocked_by_default():
    manifest = {
        "date": "2026-10-10",
        "clips": [{"index": 1, "schedule": {"tiktok_hour": 10}, "copy": {"tiktok_caption": "Legenda"}}],
    }
    try:
        publish_tiktok(manifest)
    except TikTokError as error:
        assert "publicação imediata" in str(error).lower()
    else:
        raise AssertionError("publicação imediata deveria exigir confirmação explícita")


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


def test_youtube_processing_status_must_succeed_before_scheduled(monkeypatch):
    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Videos:
        def __init__(self):
            self.calls = 0

        def list(self, **kwargs):
            self.calls += 1
            status = "processing" if self.calls == 1 else "succeeded"
            return Request({"items": [{"processingDetails": {"processingStatus": status}}]})

    class YouTube:
        def __init__(self):
            self.videos_api = Videos()

        def videos(self):
            return self.videos_api

    monkeypatch.setattr("publisher.google_io.time.sleep", lambda seconds: None)
    youtube = YouTube()
    assert wait_youtube_processing(youtube, "youtube-1") == "succeeded"
    assert youtube.videos_api.calls == 2


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
