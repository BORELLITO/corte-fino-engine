from datetime import date

import pytest

import publisher.performance as performance
from main import creator_feedback_adjustment
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
from publisher.google_io import _creator_receipt_from_item
from publisher.performance import (
    creator_feedback,
    new_performance_ledger,
    record_performance_snapshot,
    sync_publication_receipts,
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
                "creator_receipt": {
                    "version": 1,
                    "clip_index": batch_index,
                    "trigger": "treta" if index % 2 else "curiosidade",
                    "creator_score": 82.0 + index,
                    "start_seconds": index * 10.0,
                    "end_seconds": index * 10.0 + 68.0,
                    "source_fingerprint": "abc123",
                    "niche": "tecnologia",
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
        "run_id": "run-performance",
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


def public_control(data):
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
            )
    return control


def test_creator_metadata_roundtrips_from_drive_app_properties():
    receipt = _creator_receipt_from_item({
        "appProperties": {
            "cf_meta_version": "1",
            "cf_clip_index": "3",
            "cf_trigger": "treta",
            "cf_score": "91.5",
            "cf_start": "120.25",
            "cf_end": "188.4",
            "cf_source_hash": "abc123",
            "cf_niche": "política e poder",
        }
    })
    assert receipt["clip_index"] == 3
    assert receipt["trigger"] == "treta"
    assert receipt["creator_score"] == 91.5
    assert receipt["start_seconds"] == 120.25
    assert receipt["niche"] == "política e poder"


def test_performance_cannot_train_before_publication_is_verified():
    data = manifest()
    control = new_ledger(data)
    ledger = new_performance_ledger(data, control)
    key = publication_key(data["run_id"], 1, "youtube")
    with pytest.raises(RuntimeError, match="PUBLIC/VERIFIED"):
        record_performance_snapshot(
            ledger,
            key,
            horizon="24h",
            metrics={"shown_in_feed": 1000, "views": 500, "viewed_rate": 60},
        )


def test_sync_receipts_unlocks_metrics_only_after_public_state():
    data = manifest()
    control = new_ledger(data)
    ledger = new_performance_ledger(data, control)
    key = publication_key(data["run_id"], 1, "youtube")
    record_receipt(
        control,
        key,
        observed_account="@cortefinoshorts",
        state="PUBLIC",
        remote_id="yt-1",
    )
    sync_publication_receipts(ledger, control)
    record_performance_snapshot(
        ledger,
        key,
        horizon="24h",
        metrics={
            "shown_in_feed": 1000,
            "views": 600,
            "viewed_rate": 64,
            "avg_percentage_viewed": 82,
            "shares": 12,
            "comments": 8,
        },
    )
    entry = ledger["entries"][key]
    assert entry["publication_verified"] is True
    assert entry["latest_classification"] == "LEARNING_ELIGIBLE"
    assert entry["learning_eligible"] is True


def test_low_distribution_is_recorded_but_excluded_from_learning():
    data = manifest()
    control = public_control(data)
    ledger = new_performance_ledger(data, control)
    key = publication_key(data["run_id"], 1, "youtube")
    record_performance_snapshot(
        ledger,
        key,
        horizon="24h",
        metrics={"shown_in_feed": 12, "views": 4, "viewed_rate": 75, "avg_percentage_viewed": 95},
    )
    entry = ledger["entries"][key]
    assert entry["latest_classification"] == "INSUFFICIENT_DISTRIBUTION"
    assert entry["learning_eligible"] is False


def test_restricted_or_fyp_ineligible_posts_do_not_train_creator():
    data = manifest()
    control = public_control(data)
    ledger = new_performance_ledger(data, control)

    yt = publication_key(data["run_id"], 1, "youtube")
    record_performance_snapshot(
        ledger,
        yt,
        horizon="24h",
        metrics={"shown_in_feed": 1200, "views": 800, "restrictions": "copyright"},
    )
    assert ledger["entries"][yt]["latest_classification"] == "PLATFORM_RESTRICTED"
    assert ledger["entries"][yt]["learning_eligible"] is False

    tt = publication_key(data["run_id"], 1, "tiktok")
    record_performance_snapshot(
        ledger,
        tt,
        horizon="24h",
        metrics={"views": 900, "reach": 700, "fyp_eligible": False},
    )
    assert ledger["entries"][tt]["latest_classification"] == "FYP_INELIGIBLE"
    assert ledger["entries"][tt]["learning_eligible"] is False


def test_feedback_stays_advisory_with_small_sample():
    data = manifest()
    control = public_control(data)
    ledger = new_performance_ledger(data, control)
    for index in range(1, 4):
        key = publication_key(data["run_id"], index, "youtube")
        record_performance_snapshot(
            ledger,
            key,
            horizon="24h",
            metrics={
                "shown_in_feed": 1000 + index,
                "views": 600,
                "viewed_rate": 60 + index,
                "avg_percentage_viewed": 80 + index,
                "shares": 10,
                "comments": 5,
            },
        )
    feedback = creator_feedback(ledger)
    assert feedback["status"] == "INSUFFICIENT_DATA"
    assert feedback["eligible_youtube_samples"] == 3
    assert all(prior["active"] is False for prior in feedback["trigger_priors"].values())
    assert all(prior["score_adjustment"] == 0 for prior in feedback["trigger_priors"].values())


def test_ready_feedback_is_bounded_and_creator_uses_only_active_priors(monkeypatch):
    monkeypatch.setattr(performance, "MIN_CREATOR_FEEDBACK_SAMPLES", 6)
    monkeypatch.setattr(performance, "MIN_TRIGGER_SAMPLES", 3)

    data = manifest()
    control = public_control(data)
    ledger = new_performance_ledger(data, control)
    for index in range(1, 7):
        key = publication_key(data["run_id"], index, "youtube")
        strong = index % 2 == 1
        record_performance_snapshot(
            ledger,
            key,
            horizon="24h",
            metrics={
                "shown_in_feed": 2500,
                "views": 1500,
                "viewed_rate": 78 if strong else 48,
                "avg_percentage_viewed": 105 if strong else 55,
                "shares": 35 if strong else 3,
                "comments": 20 if strong else 4,
            },
        )
    feedback = creator_feedback(ledger)
    assert feedback["status"] == "READY"
    assert feedback["trigger_priors"]["treta"]["active"] is True
    assert feedback["trigger_priors"]["curiosidade"]["active"] is True
    assert -2.0 <= feedback["trigger_priors"]["treta"]["score_adjustment"] <= 2.0
    assert -2.0 <= feedback["trigger_priors"]["curiosidade"]["score_adjustment"] <= 2.0

    assert creator_feedback_adjustment({"performance_feedback": feedback}, "treta") == feedback["trigger_priors"]["treta"]["score_adjustment"]
    inactive = {
        "status": "READY",
        "trigger_priors": {"treta": {"active": False, "score_adjustment": 99}},
    }
    assert creator_feedback_adjustment({"performance_feedback": inactive}, "treta") == 0.0
