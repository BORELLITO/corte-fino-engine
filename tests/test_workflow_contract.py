from pathlib import Path

PUBLISHER_WORKFLOW = Path(".github/workflows/corte-fino-publisher.yml")
GENERATOR_WORKFLOW = Path(".github/workflows/corte-fino.yml")


def test_publisher_requires_two_exact_drive_folders_and_periods():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "folder_1:" in text
    assert "folder_2:" in text
    assert "date_1:" in text
    assert "date_2:" in text
    assert "period_1:" in text
    assert "period_2:" in text
    assert "PUBLISHER_BROWSER_ONLY: \"1\"" in text
    assert "PUBLISHER_TIKTOK_DIRECT_ENABLED: \"0\"" in text
    assert "REQUESTED_EPISODE_1" in text
    assert "REQUESTED_EPISODE_2" in text
    assert "python -m publisher.cli prepare" in text
    assert "python -m publisher.cli browser-package" in text
    assert "publisher/state/browser_package.json" in text


def test_publication_api_scheduler_is_removed():
    assert not Path(".github/workflows/corte-fino-publisher-tiktok-schedule.yml").exists()


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

