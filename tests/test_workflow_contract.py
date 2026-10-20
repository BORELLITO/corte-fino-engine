from pathlib import Path

PUBLISHER_WORKFLOW = Path(".github/workflows/corte-fino-publisher.yml")
PUBLISHER_CI = Path(".github/workflows/corte-fino-publisher-ci.yml")
GENERATOR_WORKFLOW = Path(".github/workflows/corte-fino.yml")
TIKTOK_API_WORKFLOW = Path(".github/workflows/tiktok-sandbox-token.yml")
ROOT_README = Path("README.md")


def test_publisher_requires_two_exact_drive_folders_and_daily_grid():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "folder_1:" in text
    assert "folder_2:" in text
    assert "date_1:" in text
    assert "date_2:" in text
    assert "period_1:" in text
    assert "period_2:" in text
    assert "options: [daily]" in text
    assert "PUBLISHER_BROWSER_ONLY: \"1\"" in text
    assert "youtube_account:" in text
    assert "tiktok_account:" in text
    assert "PUBLISHER_YOUTUBE_ACCOUNT" in text
    assert "PUBLISHER_TIKTOK_ACCOUNT" in text
    assert "REQUESTED_EPISODE_1" in text
    assert "REQUESTED_EPISODE_2" in text
    assert "source_episode_1:" in text
    assert "source_episode_2:" in text
    assert "python -m publisher.cli prepare" in text
    assert "python -m publisher.cli browser-package" in text
    assert "python -m publisher.cli diagnostic-package" in text
    assert "publisher/state/browser_package.json" in text
    assert "publisher/state/diagnostic_package.json" in text


def test_operational_state_is_not_committed_to_public_git():
    text = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "git add -f publisher/state" not in text
    assert "git push" not in text
    assert "actions/upload-artifact@v4" in text
    assert "retention-days: 1" in text
    assert "publisher/state/" in Path(".gitignore").read_text(encoding="utf-8")


def test_publisher_ci_runs_on_changes():
    text = PUBLISHER_CI.read_text(encoding="utf-8")
    assert "pull_request:" in text
    assert "push:" in text
    assert "tests/test_publisher_control.py" in text
    assert "python -m py_compile" in text


def test_publication_api_scheduler_is_removed():
    assert not Path(".github/workflows/corte-fino-publisher-tiktok-schedule.yml").exists()
    assert not TIKTOK_API_WORKFLOW.exists()


def test_publisher_has_no_metricool_route():
    assert "Metricool" not in PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    assert "Metricool" not in Path("publisher/tiktok_io.py").read_text(encoding="utf-8")
    assert "Metricool" not in Path("publisher/README.md").read_text(encoding="utf-8")
    assert "tiktokapis" not in Path("publisher/tiktok_io.py").read_text(encoding="utf-8")


def test_root_docs_match_browser_only_five_per_day_contract():
    text = ROOT_README.read_text(encoding="utf-8")
    assert "Publicar 5 por Dia" in text
    assert "Cloud Web Browser" in text
    assert "TikTok Sandbox" not in text


def test_both_motors_require_manual_dispatch():
    publisher = PUBLISHER_WORKFLOW.read_text(encoding="utf-8")
    generator = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in publisher
    assert "workflow_dispatch:" in generator


def test_generator_does_not_trigger_or_register_the_publisher():
    text = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "latest_batch.json" not in text
    assert "Registrar lote exato do Publisher" not in text


def test_creator_upload_destination_has_no_publisher_or_hardcoded_fallback():
    text = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "PUBLISHER_DRIVE_FOLDER_ID" not in text
    assert "15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da" not in text


def test_creator_manual_and_drive_sources_share_the_same_readiness_gate():
    text = GENERATOR_WORKFLOW.read_text(encoding="utf-8")
    assert 'if os.environ.get("SOURCE_FILE", "").strip()' in text
    assert 'status != "READY_FOR_HUMAN_REVIEW"' in text
    assert 'env.PROCESSING_READY == \'1\'' in text

