from datetime import date

import pytest

from publisher.control import new_ledger, publication_key, reconciliation_summary, record_receipt
from publisher.core import (
    BRANDING_CAPTION_MARGIN_V,
    BRANDING_FORMAT,
    BRANDING_LOGO_POSITION,
    BRANDING_VERSION,
    DAY_PERIOD_HOURS,
    MANIFEST_VERSION,
    YOUTUBE_HOURS,
    TIKTOK_HOURS,
    assign_slots,
    copy_dict,
    local_publish_at,
    make_copy,
)


def manifest():
    pack = copy_dict(make_copy(
        "A inteligência artificial está mudando o trabalho. O ser humano pode virar o gargalo quando a ferramenta substitui decisões.",
        "Flow Podcast",
        "434",
    ))
    clips = []
    batches = []
    for batch_no, (batch_id, day, folder) in enumerate((
        ("A", "2026-10-21", "folder-a"),
        ("B", "2026-10-22", "folder-b"),
    )):
        local = []
        for batch_index in range(1, 6):
            index = batch_no * 5 + batch_index
            local.append({
                "index": index,
                "batch_id": batch_id,
                "batch_index": batch_index,
                "drive_folder_id": folder,
                "drive_id": f"drive-{batch_id}-{batch_index}",
                "name": f"{batch_id}-{batch_index:02d}.mp4",
                "size": 100000,
                "md5_checksum": f"md5-{batch_id}-{batch_index}",
                "transcript": "transcrição validada com conteúdo suficiente",
                "copy": dict(pack),
                "schedule": {},
            })
        assign_slots(local, DAY_PERIOD_HOURS)
        for clip in local:
            at = local_publish_at(date.fromisoformat(day), clip["schedule"]["youtube_hour"])
            clip["schedule"]["youtube_publish_at"] = at
            clip["schedule"]["tiktok_publish_at"] = at
        clips.extend(local)
        batches.append({
            "batch_id": batch_id,
            "drive_folder_id": folder,
            "date": day,
            "period": "daily",
            "hours": list(DAY_PERIOD_HOURS),
            "source": {"name": "Flow Podcast", "episode": "434"},
        })
    return {
        "version": MANIFEST_VERSION,
        "run_id": "run-control",
        "date": "2026-10-21",
        "timezone": "America/Sao_Paulo",
        "engine_commit": "test-sha",
        "target_accounts": {"youtube": "@cortefinoshorts", "tiktok": "cortefinoshorts"},
        "drive_folder_id": "folder-a",
        "drive_folder_ids": ["folder-a", "folder-b"],
        "youtube_hours": list(YOUTUBE_HOURS),
        "tiktok_hours": list(TIKTOK_HOURS),
        "batches": batches,
        "rights": {"authorized": True, "status": "AUTORIZADO"},
        "source": {"name": "Flow Podcast", "episode": "434"},
        "sources": [
            {"name": "Flow Podcast", "episode": "434"},
            {"name": "Flow Podcast", "episode": "434"},
        ],
        "branding": {
            "version": BRANDING_VERSION,
            "format": BRANDING_FORMAT,
            "logo_position": BRANDING_LOGO_POSITION,
            "caption_margin_v": BRANDING_CAPTION_MARGIN_V,
        },
        "clips": clips,
    }


def test_ledger_has_twenty_platform_entries():
    ledger = new_ledger(manifest())
    assert len(ledger["entries"]) == 20
    assert {entry["state"] for entry in ledger["entries"].values()} == {"BROWSER_READY"}


def test_wrong_account_is_fail_closed():
    ledger = new_ledger(manifest())
    key = publication_key("run-control", 1, "youtube")
    record_receipt(
        ledger,
        key,
        observed_account="@canalerrado",
        state="SCHEDULED",
        remote_url="https://youtube.com/shorts/example",
    )
    entry = ledger["entries"][key]
    assert entry["state"] == "BLOCKED_WRONG_ACCOUNT"
    assert entry["account_verified"] is False


def test_scheduled_receipt_requires_remote_identity():
    ledger = new_ledger(manifest())
    key = publication_key("run-control", 1, "youtube")
    with pytest.raises(RuntimeError, match="exige remote_id, remote_url ou remote_reference"):
        record_receipt(
            ledger,
            key,
            observed_account="@cortefinoshorts",
            state="SCHEDULED",
        )


def test_good_receipt_records_verified_account_and_remote_id():
    ledger = new_ledger(manifest())
    key = publication_key("run-control", 1, "youtube")
    record_receipt(
        ledger,
        key,
        observed_account="@CorteFinoShorts",
        state="SCHEDULED",
        remote_id="yt-1",
    )
    entry = ledger["entries"][key]
    assert entry["account_verified"] is True
    assert entry["state"] == "SCHEDULED"
    assert entry["remote_id"] == "yt-1"


def test_duplicate_remote_id_is_blocked():
    ledger = new_ledger(manifest())
    first = publication_key("run-control", 1, "youtube")
    second = publication_key("run-control", 2, "youtube")
    record_receipt(ledger, first, observed_account="@cortefinoshorts", state="SCHEDULED", remote_id="same")
    with pytest.raises(RuntimeError, match="remote_id já usado"):
        record_receipt(ledger, second, observed_account="@cortefinoshorts", state="SCHEDULED", remote_id="same")


def test_ambiguous_upload_blocks_blind_retry():
    ledger = new_ledger(manifest())
    key = publication_key("run-control", 1, "tiktok")
    record_receipt(
        ledger,
        key,
        observed_account="cortefinoshorts",
        state="UPLOAD_STARTED",
    )
    summary = reconciliation_summary(ledger)
    assert key in summary["ambiguous"]
    assert summary["safe_to_retry"] is False


def test_ledger_can_be_scoped_to_diagnostic_package():
    data = manifest()
    selected = {
        publication_key("run-control", index, platform)
        for index in (1, 2, 3)
        for platform in ("youtube", "tiktok")
    }
    ledger = new_ledger(data, selected)
    assert set(ledger["entries"]) == selected
    assert len(ledger["entries"]) == 6


def test_scheduled_receipt_accepts_studio_reference_when_url_is_unavailable():
    ledger = new_ledger(manifest())
    key = publication_key("run-control", 1, "tiktok")
    record_receipt(
        ledger,
        key,
        observed_account="https://www.tiktok.com/@cortefinoshorts",
        state="SCHEDULED",
        remote_reference="studio-row-2026-10-21-10:00",
    )
    entry = ledger["entries"][key]
    assert entry["account_verified"] is True
    assert entry["remote_reference"] == "studio-row-2026-10-21-10:00"
