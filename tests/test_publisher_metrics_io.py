from datetime import date, datetime, timezone

import pytest

from publisher.control import new_ledger, publication_key, record_receipt
from publisher.core import (
    BRANDING_CAPTION_MARGIN_V,
    BRANDING_FORMAT,
    BRANDING_LOGO_POSITION,
    BRANDING_VERSION,
    DAY_PERIOD_HOURS,
    MANIFEST_VERSION,
    TIKTOK_HOURS,
    YOUTUBE_HOURS,
    assign_slots,
    copy_dict,
    local_publish_at,
    make_copy,
)
from publisher.metrics_io import (
    apply_metrics_result,
    build_metrics_package,
    build_run_state,
    validate_run_state,
)
from publisher.performance import new_performance_ledger


def manifest():
    pack = copy_dict(make_copy(
        "A inteligência artificial mudou o trabalho e criou um conflito que termina com uma consequência clara.",
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
                "transcript": "transcrição privada que não deve persistir no run state",
                "creator_receipt": {
                    "version": 1,
                    "trigger": "treta",
                    "creator_score": 88,
                },
                "video_profile": {"duration": 68.0},
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
        "run_id": "run-metrics",
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


def ledgers():
    data = manifest()
    control = new_ledger(data)
    for index in range(1, 11):
        for platform, account in (("youtube", "@cortefinoshorts"), ("tiktok", "cortefinoshorts")):
            key = publication_key(data["run_id"], index, platform)
            record_receipt(
                control,
                key,
                observed_account=account,
                state="PUBLIC",
                remote_id=f"{platform}-{index}",
                remote_url=f"https://example.test/{platform}/{index}",
            )
    performance = new_performance_ledger(data, control)
    return data, control, performance


def test_run_state_redacts_transcripts_but_keeps_operational_truth():
    data, control, performance = ledgers()
    state = build_run_state(data, control, performance)
    validate_run_state(state)
    assert state["run_id"] == data["run_id"]
    assert state["manifest"]["transcripts"] == "redacted"
    assert all("transcript" not in clip for clip in state["manifest"]["clips"])
    assert len(state["control_ledger"]["entries"]) == 20
    assert len(state["performance_ledger"]["entries"]) == 20


def test_metrics_package_contains_only_due_verified_unsnapshotted_items():
    data, control, performance = ledgers()
    first = publication_key(data["run_id"], 1, "youtube")
    performance["entries"][first]["snapshots"]["24h"] = {
        "horizon": "24h",
        "captured_at": "2026-10-22T15:00:00Z",
        "metrics": {"shown_in_feed": 500},
        "classification": "LEARNING_ELIGIBLE",
        "learning_eligible": True,
    }
    package = build_metrics_package(
        control,
        performance,
        horizon="24h",
        now=datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
    )
    keys = {item["publication_key"] for item in package["items"]}
    assert first not in keys
    assert len(package["items"]) == 19
    youtube = next(item for item in package["items"] if item["platform"] == "youtube")
    assert "shown_in_feed" in youtube["required_fields"]
    assert "viewed_rate" in youtube["required_fields"]
    tiktok = next(item for item in package["items"] if item["platform"] == "tiktok")
    assert "fyp_eligible" in tiktok["required_fields"]


def test_metrics_package_skips_items_before_horizon_is_due():
    _, control, performance = ledgers()
    package = build_metrics_package(
        control,
        performance,
        horizon="72h",
        now=datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc),
    )
    assert package["items"] == []


def test_metrics_result_rejects_wrong_observed_account():
    data, control, performance = ledgers()
    package = build_metrics_package(
        control,
        performance,
        horizon="24h",
        now=datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
    )
    item = next(row for row in package["items"] if row["platform"] == "youtube")
    result = {
        "version": 1,
        "kind": "studio_metrics_result",
        "run_id": data["run_id"],
        "horizon": "24h",
        "items": [{
            "publication_key": item["publication_key"],
            "platform": "youtube",
            "observed_account": "@canalerrado",
            "metrics": {"shown_in_feed": 1000, "views": 600, "viewed_rate": 65},
        }],
    }
    with pytest.raises(RuntimeError, match="Conta observada divergente"):
        apply_metrics_result(control, performance, package, result)


def test_batch_metrics_apply_records_learning_eligible_snapshot():
    data, control, performance = ledgers()
    package = build_metrics_package(
        control,
        performance,
        horizon="24h",
        now=datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
    )
    item = next(row for row in package["items"] if row["platform"] == "youtube")
    result = {
        "version": 1,
        "kind": "studio_metrics_result",
        "run_id": data["run_id"],
        "horizon": "24h",
        "items": [{
            "publication_key": item["publication_key"],
            "platform": "youtube",
            "observed_account": "@CorteFinoShorts",
            "metrics": {
                "shown_in_feed": 1800,
                "views": 950,
                "viewed_rate": 66,
                "avg_percentage_viewed": 84,
                "shares": 15,
                "comments": 9,
                "restrictions": "none",
            },
            "evidence": "YouTube Studio Shorts analytics",
        }],
    }
    apply_metrics_result(control, performance, package, result)
    snapshot = performance["entries"][item["publication_key"]]["snapshots"]["24h"]
    assert snapshot["classification"] == "LEARNING_ELIGIBLE"
    assert snapshot["learning_eligible"] is True


def test_result_cannot_inject_key_that_was_not_in_collection_package():
    data, control, performance = ledgers()
    package = build_metrics_package(
        control,
        performance,
        horizon="24h",
        now=datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
    )
    result = {
        "version": 1,
        "kind": "studio_metrics_result",
        "run_id": data["run_id"],
        "horizon": "24h",
        "items": [{
            "publication_key": "run-metrics:99:youtube",
            "platform": "youtube",
            "observed_account": "@cortefinoshorts",
            "metrics": {"shown_in_feed": 500},
        }],
    }
    with pytest.raises(RuntimeError, match="publication_key inesperada"):
        apply_metrics_result(control, performance, package, result)
