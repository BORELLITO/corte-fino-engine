from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_WORKFLOW = ROOT / ".github" / "workflows" / "corte-fino-publisher.yml"
TIKTOK_SCHEDULE_WORKFLOW = ROOT / ".github" / "workflows" / "corte-fino-publisher-tiktok-schedule.yml"
GENERATOR_WORKFLOW = ROOT / ".github" / "workflows" / "corte-fino.yml"


def test_publisher_is_manual_only_and_requires_the_exact_drive_folder():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")

    assert "  schedule:" not in text
    assert 'drive_folder:\n        description: "URL ou ID exato da pasta do lote com os 5 MP4"\n        required: true' in text
    assert "latest_batch.json" not in text
    assert "github.event.schedule" not in text
    assert "PUBLISHER_ENABLED" not in text
    assert "normalize_folder_id" in text
    assert "REQUESTED_FOLDER" in text


def test_both_motors_require_manual_dispatch():
    generator = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    publisher = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in generator
    assert "  schedule:" not in generator
    assert "workflow_dispatch:" in publisher
    assert "  schedule:" not in publisher
    assert "group: corte-fino-motor-1" in generator
    assert "group: corte-fino-motor-2" in publisher


def test_publisher_manual_tiktok_mode_is_explicit():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")

    assert "inputs.mode == 'tiktok' || inputs.mode == 'all'" in text
    assert "python -m publisher.cli tiktok --allow-immediate" in text


def test_tiktok_schedule_uses_due_only_and_shared_publisher_lock():
    text = TIKTOK_SCHEDULE_WORKFLOW.read_text(encoding="utf-8")

    assert 'cron: "0 * * * *"' in text
    assert "workflow_dispatch:" in text
    assert "group: corte-fino-motor-2" in text
    assert "python -m publisher.cli tiktok --due-only" in text
    assert "PUBLISHER_TIKTOK_REFRESH_TOKEN" in text
    assert "PUBLISHER_GOOGLE_REFRESH_TOKEN" in text
    assert "latest_batch.json" not in text


def test_generator_does_not_trigger_or_register_the_publisher():
    text = GENERATOR_WORKFLOW.read_text(encoding="utf-8")

    assert "latest_batch.json" not in text
    assert "Registrar lote exato do Publisher" not in text
    assert "DRIVE_FOLDER_ID: ${{ secrets.DRIVE_FOLDER_ID || secrets.DRIVER_FOLDER_ID || secrets.PUBLISHER_DRIVE_FOLDER_ID" in text
