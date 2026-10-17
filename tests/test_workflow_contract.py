from pathlib import Path

PUBLISHER_WORKFLOW = Path(".github/workflows/corte-fino-publisher.yml")
TIKTOK_WORKFLOW = Path(".github/workflows/corte-fino-publisher-tiktok-schedule.yml")
GENERATOR_WORKFLOW = Path(".github/workflows/corte-fino.yml")


def test_publisher_requires_two_exact_drive_folders_and_periods():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "folder_1:" in text
    assert "folder_2:" in text
    assert "date_1:" in text
    assert "date_2:" in text
    assert "period_1:" in text
    assert "period_2:" in text
    assert "PUBLISHER_TIKTOK_DIRECT_ENABLED: \"1\"" in text
    assert "python -m publisher.cli prepare" in text
    assert "python -m publisher.cli youtube" in text


def test_tiktok_is_direct_and_automatic():
    text = TIKTOK_WORKFLOW.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert 'cron: "0 11-23 * * *"' in text
    assert 'cron: "0 0-1 * * *"' in text
    assert "python -m publisher.cli tiktok --due-only" in text
    assert "Metricool" not in text


def test_publisher_has_no_metricool_route():
    assert "Metricool" not in PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "Metricool" not in Path("publisher/tiktok_io.py").read_text(encoding="utf-8")
    assert "Metricool" not in Path("publisher/README.md").read_text(encoding="utf-8")


def test_both_motors_require_manual_dispatch():
    publisher = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    generator = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in publisher
    assert "workflow_dispatch:" in generator


def test_generator_does_not_trigger_or_register_the_publisher():
    text = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "latest_batch.json" not in text
    assert "Registrar lote exato do Publisher" not in text

