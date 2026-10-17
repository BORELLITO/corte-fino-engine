from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from publisher.cli import report
from publisher.core import (BRANDING_CAPTION_MARGIN_V, BRANDING_FORMAT, BRANDING_LOGO_POSITION, BRANDING_VERSION, MANIFEST_VERSION, TIKTOK_CAPTION_LIMIT, TIKTOK_HOURS, YOUTUBE_DESCRIPTION_LIMIT, YOUTUBE_HOURS, YOUTUBE_TITLE_LIMIT, assign_slots, build_title, copy_dict, copy_quality_issues, detect_topic, format_copy_text, local_publish_at, make_copy, natural_index, normalize_transcript, validate_credit_source, validate_manifest)
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
    assert "#apostas" in pack.tiktok_caption
    assert "#corteFino" not in pack.tiktok_caption
    assert "#TikTok" not in pack.tiktok_caption
    assert "#Shorts" not in pack.tiktok_caption
    assert "#Shorts" not in pack.youtube_description
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
    assert "#debate" in pack.tiktok_caption
    assert "#cortefino" not in pack.tiktok_caption.casefold()
    assert "#tiktok" not in pack.tiktok_caption.casefold()
    assert all("jikei" not in tag.lower() for tag in pack.youtube_tags)


def test_title_uses_the_strongest_hook():
    pack = make_copy("A casa sempre ganha. O problema é quando a pessoa perde tudo no vício de aposta.")
    assert "PERDE TUDO" in pack.youtube_title


def test_titles_are_uppercase_and_have_no_punctuation():
    pack = make_copy("A casa sempre ganha. O problema é quando a pessoa perde tudo no vício de aposta.")
    assert pack.youtube_title == pack.youtube_title.upper()
    assert not any(char in pack.youtube_title for char in ".,;:!?—–-")
    assert pack.tiktok_caption.split("\n", 1)[0] == pack.youtube_title


def test_credit_source_must_be_the_original_channel():
    assert validate_credit_source("Redcast Feminismo") == "Redcast Feminismo"
    with pytest.raises(ValueError, match="nunca use Corte Fino"):
        validate_credit_source("Corte Fino Publisher")
    with pytest.raises(ValueError, match="fonte original"):
        validate_credit_source("", required=True)
    with pytest.raises(ValueError, match="nunca use Corte Fino"):
        make_copy(
            "A inteligência artificial está mudando o trabalho. O ser humano pode virar o gargalo.",
            "Corte Fino",
        )


def test_copy_uses_natural_credit_and_exactly_two_emojis():
    pack = make_copy(
        "A inteligência artificial está mudando o trabalho. O ser humano pode virar o gargalo.",
        "Flow Podcast",
        "434",
    )
    assert "Créditos: Flow Podcast, episódio 434." in pack.tiktok_caption
    assert "—" not in pack.tiktok_caption
    assert "🧠" in pack.tiktok_caption
    assert "⚖️" in pack.tiktok_caption


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


def test_copy_evidence_stays_related_to_the_selected_hook():
    pack = make_copy(
        "A casa sempre ganha. Roda umas donates aí, né? "
        "Não é outro sentimento além de raiva de ver essa pessoa que não quer somar?"
    )
    assert pack.evidence
    assert "raiva" in pack.evidence[0].casefold()


def _valid_manifest():
    pack = copy_dict(make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?"
    ))
    clips = [
        {
            "index": index,
            "drive_id": f"drive-{index}",
            "name": f"fonte - {index:02d}.mp4",
            "size": 100000,
            "md5_checksum": f"md5-{index}",
            "transcript": "A transcrição validada tem conteúdo suficiente para o corte.",
            "schedule": {"youtube_hour": youtube_hour, "tiktok_hour": tiktok_hour},
            "copy": pack,
        }
        for index, (youtube_hour, tiktok_hour) in enumerate(zip(YOUTUBE_HOURS, TIKTOK_HOURS), 1)
    ]
    return {
        "version": MANIFEST_VERSION,
        "run_id": "run-1",
        "date": "2026-10-11",
        "timezone": "America/Sao_Paulo",
        "drive_folder_id": "folder-1",
        "rights": {"authorized": True, "status": "AUTORIZADO"},
        "branding": {
            "version": BRANDING_VERSION,
            "format": BRANDING_FORMAT,
            "logo_position": BRANDING_LOGO_POSITION,
            "caption_margin_v": BRANDING_CAPTION_MARGIN_V,
        },
        "clips": clips,
    }


def test_manifest_v5_validates_copy_rights_and_branding():
    validate_manifest(_valid_manifest())


def test_manifest_rejects_publisher_as_persisted_credit_source():
    manifest = _valid_manifest()
    manifest["source"] = {"name": "Corte Fino", "episode": ""}
    with pytest.raises(RuntimeError, match="nunca use Corte Fino"):
        validate_manifest(manifest)


def test_manifest_rejects_old_copy_without_paragraphs():
    manifest = _valid_manifest()
    manifest["clips"][0]["copy"]["tiktok_caption"] = manifest["clips"][0]["copy"]["tiktok_caption"].replace("\n\n", " ")
    with pytest.raises(RuntimeError, match="parágrafos"):
        validate_manifest(manifest)


def test_manifest_can_be_persisted_without_public_transcripts():
    manifest = _valid_manifest()
    for clip in manifest["clips"]:
        clip.pop("transcript")
    validate_manifest(manifest)


def test_manifest_rejects_mismatched_branding_contract():
    manifest = _valid_manifest()
    manifest["branding"]["logo_position"] = "center"
    with pytest.raises(RuntimeError, match="HUD/legenda"):
        validate_manifest(manifest)


def test_manifest_rejects_duplicate_publication_slots():
    manifest = _valid_manifest()
    manifest["clips"][1]["schedule"]["youtube_hour"] = manifest["clips"][0]["schedule"]["youtube_hour"]
    with pytest.raises(RuntimeError, match="horários duplicados"):
        validate_manifest(manifest)


def test_copy_qa_rejects_lowercase_sentence_starts():
    pack = make_copy(
        "A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Você concorda com essa aposta?"
    )
    pack.youtube_description = pack.youtube_description.replace("Quem deveria", "quem deveria", 1)
    assert "início de frase não está em maiúscula" in copy_quality_issues(pack)


def test_rights_gate_does_not_accept_string_false():
    manifest = _valid_manifest()
    manifest["rights"]["authorized"] = "false"
    with pytest.raises(RuntimeError, match="direitos não confirmados"):
        validate_manifest(manifest, require_rights=True)


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
            assert "trashed = false" in query
            return Request({"files": [{"id": f"video-{index}", "name": f"fonte - {index:02d}.mp4", "mimeType": "video/mp4"} for index in range(1, 6)]})

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


def test_drive_folder_with_extra_child_is_rejected():
    class Request:
        def execute(self, **kwargs):
            return {
                "files": [
                    *[
                        {"id": f"video-{index}", "name": f"fonte - {index:02d}.mp4", "mimeType": "video/mp4"}
                        for index in range(1, 6)
                    ],
                    {"id": "folder-extra", "name": "Relatorio", "mimeType": "application/vnd.google-apps.folder"},
                ]
            }

    class Files:
        def list(self, **kwargs):
            return Request()

    class Drive:
        def files(self):
            return Files()

    with pytest.raises(RuntimeError, match="arquivos extras"):
        resolve_publication_folder(Drive(), "exact-folder")


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
    monkeypatch.setenv("PUBLISHER_TIKTOK_ENV", "production")
    assert choose_privacy_level(creator) == "PUBLIC_TO_EVERYONE"
    monkeypatch.setenv("PUBLISHER_TIKTOK_ENV", "sandbox")
    monkeypatch.setenv("PUBLISHER_TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")
    assert choose_privacy_level(creator) == "SELF_ONLY"


def test_tiktok_publish_checks_expected_account(monkeypatch):
    monkeypatch.setenv("PUBLISHER_TIKTOK_EXPECTED_USERNAME", "cortefinoshorts")
    with pytest.raises(TikTokError, match="Conta TikTok incorreta"):
        tiktok_io._assert_expected_username({"creator_username": "outra_conta"})
    with pytest.raises(TikTokError, match="Conta TikTok incorreta"):
        tiktok_io._assert_expected_username({})


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
        "rights": {"authorized": True},
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

    result = publish_tiktok(
        manifest,
        due_only=True,
        now=datetime(2026, 10, 10, 10, 30, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert result == [{"index": 1, "status": "PROCESSING", "publish_id": "publish-1"}]
    assert markers == [{"cf_tiktok_status": "PROCESSING", "cf_tiktok_date": "2026-10-10"}]


def test_tiktok_reconciles_pending_id_after_manifest_date_changes(monkeypatch):
    class Request:
        def execute(self, **kwargs):
            return {
                "id": "drive-1",
                "name": "fonte - 01.mp4",
                "size": 100,
                "mimeType": "video/mp4",
                "md5Checksum": "abc",
                "parents": ["folder-1"],
                "appProperties": {"cf_tiktok_publish_id": "publish-old"},
            }

    class Files:
        def get(self, **kwargs):
            return Request()

    class Drive:
        def files(self):
            return Files()

    manifest = {
        "date": "2026-10-09",
        "drive_folder_id": "folder-1",
        "rights": {"authorized": True},
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

    result = publish_tiktok(
        manifest,
        due_only=True,
        now=datetime(2026, 10, 10, 10, 30, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert result == [{"index": 1, "status": "PROCESSING", "publish_id": "publish-old"}]


def test_tiktok_direct_publish_requires_explicit_feature_flag(monkeypatch):
    monkeypatch.setenv("PUBLISHER_TIKTOK_DIRECT_ENABLED", "0")
    manifest = {
        "date": "2026-10-10",
        "rights": {"authorized": True},
        "clips": [],
    }
    with pytest.raises(TikTokError, match="Metricool"):
        publish_tiktok(manifest, due_only=True)


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


def test_tiktok_due_selection_skips_completed_clips_and_chooses_next_slot(monkeypatch):
    manifest = {
        "date": "2026-10-10",
        "drive_folder_id": "folder-1",
        "clips": [
            {
                "index": index,
                "drive_id": f"drive-{index}",
                "name": f"fonte - {index:02d}.mp4",
                "size": 100,
                "md5_checksum": f"md5-{index}",
                "schedule": {"tiktok_hour": hour},
                "copy": {"tiktok_caption": f"Legenda {index}"},
            }
            for index, hour in enumerate(TIKTOK_HOURS, 1)
        ],
    }

    class Request:
        def __init__(self, data):
            self.data = data

        def execute(self, **kwargs):
            return self.data

    class Files:
        def get(self, **kwargs):
            index = int(kwargs["fileId"].split("-")[-1])
            properties = (
                {"cf_tiktok_publish_id": "publish-1", "cf_tiktok_status": "PUBLISH_COMPLETE"}
                if index == 1
                else {}
            )
            clip = manifest["clips"][index - 1]
            return Request({
                "id": clip["drive_id"],
                "name": clip["name"],
                "size": clip["size"],
                "mimeType": "video/mp4",
                "md5Checksum": clip["md5_checksum"],
                "parents": ["folder-1"],
                "appProperties": properties,
            })

    class Drive:
        def files(self):
            return Files()

    clips, prefetched = tiktok_io._select_due_clips(
        manifest,
        Drive(),
        datetime(2026, 10, 10, 13, 15, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert [clip["index"] for clip in clips] == [2]
    assert prefetched[1]["appProperties"]["cf_tiktok_status"] == "PUBLISH_COMPLETE"


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
        now=datetime(2026, 10, 10, 11, 15, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert len(result) == 1
    assert result[0]["index"] == 1
