from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from publisher.core import normalize_account_identity, validate_manifest
from publisher.control import (
    load_ledger,
    new_ledger,
    publication_key,
    reconciliation_summary,
    record_receipt,
    save_ledger,
)
from publisher.google_io import (
    FOLDER_ID,
    load_creator_learning_history_from_drive,
    prepare_batches,
    save_creator_feedback_to_drive,
    save_creator_learning_history_to_drive,
    scheduled_publish_at,
)
from publisher.performance import (
    creator_feedback,
    load_performance_ledger,
    merge_performance_into_history,
    new_learning_history,
    new_performance_ledger,
    record_performance_snapshot,
    save_performance_ledger,
    sync_publication_receipts,
)
from publisher.metrics_io import (
    apply_metrics_result,
    build_metrics_package,
    load_metrics_result_from_drive,
    load_run_state_from_drive,
    restore_run_state_files,
    save_metrics_package_to_drive,
    save_run_state_to_drive,
)
from publisher.tiktok_io import PUBLIC_TIKTOK_VISIBILITY, publish_tiktok, validate_browser_visibility


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def report(manifest: dict, ledger: dict | None = None) -> dict:
    """Return planned slots enriched with receipts when a control ledger exists."""
    ledger_entries = (ledger or {}).get("entries", {}) if isinstance(ledger, dict) else {}
    youtube = []
    tiktok = []
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["youtube_publish_at"]):
        key = publication_key(manifest["run_id"], clip["index"], "youtube")
        receipt = ledger_entries.get(key, {})
        youtube.append({
            "index": clip["index"],
            "publication_key": key,
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["youtube_publish_at"],
            "title": clip["copy"]["youtube_title"],
            "status": receipt.get("state", "NOT_IN_PACKAGE" if ledger is not None else "pending_browser"),
            "video_id": receipt.get("remote_id"),
            "remote_url": receipt.get("remote_url"),
            "account_verified": receipt.get("account_verified", False),
        })
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["tiktok_publish_at"]):
        key = publication_key(manifest["run_id"], clip["index"], "tiktok")
        receipt = ledger_entries.get(key, {})
        tiktok.append({
            "index": clip["index"],
            "publication_key": key,
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["tiktok_publish_at"],
            "caption": clip["copy"]["tiktok_caption"],
            "status": receipt.get("state", "NOT_IN_PACKAGE" if ledger is not None else "pending_browser"),
            "publish_id": receipt.get("remote_id"),
            "remote_url": receipt.get("remote_url"),
            "account_verified": receipt.get("account_verified", False),
            "visibility": PUBLIC_TIKTOK_VISIBILITY,
            "privacy_check": "required_before_schedule",
        })
    statuses = [item["status"] for item in youtube + tiktok]
    return {
        "date": manifest.get("date"),
        "timezone": manifest.get("timezone", "America/Sao_Paulo"),
        "batches": manifest.get("batches", []),
        "youtube": youtube,
        "tiktok": tiktok,
        "summary": {
            "total": len(statuses),
            "planned_in_package": len(ledger_entries) if ledger is not None else len(statuses),
            "not_in_package": sum(status == "NOT_IN_PACKAGE" for status in statuses),
            "scheduled_or_complete": sum(status in {"SCHEDULED", "PUBLIC", "VERIFIED", "METRICS_PENDING", "MEASURED", "LEARNED"} for status in statuses),
            "pending_or_processing": sum(status in {"pending_browser", "BROWSER_READY", "ACCOUNT_VERIFIED", "UPLOAD_STARTED", "UPLOADED"} for status in statuses),
            "attention": sum(status in {"BLOCKED_WRONG_ACCOUNT", "STALE_MEDIA", "UPLOAD_FAILED", "SCHEDULE_FAILED", "WRONG_VISIBILITY", "MISSED_SLOT", "POST_NOT_FOUND", "PLATFORM_RESTRICTED", "FYP_INELIGIBLE", "RECONCILIATION_REQUIRED"} for status in statuses),
        },
    }


def browser_package(manifest: dict) -> dict:
    """Build the exact payload consumed by the Cloud Web Browser flow."""
    validate_manifest(manifest, require_rights=True)
    timezone = ZoneInfo(manifest["timezone"])
    posts = []
    for clip in sorted(manifest["clips"], key=lambda item: item["schedule"]["youtube_publish_at"]):
        youtube_at = scheduled_publish_at(manifest, clip, "youtube")
        tiktok_at = scheduled_publish_at(manifest, clip, "tiktok")
        youtube_local = datetime.fromisoformat(youtube_at.replace("Z", "+00:00")).astimezone(timezone)
        tiktok_local = datetime.fromisoformat(tiktok_at.replace("Z", "+00:00")).astimezone(timezone)
        posts.append(
            {
                "index": clip["index"],
                "publication_keys": {
                    "youtube": publication_key(manifest["run_id"], clip["index"], "youtube"),
                    "tiktok": publication_key(manifest["run_id"], clip["index"], "tiktok"),
                },
                "batch_id": clip["batch_id"],
                "batch_index": clip["batch_index"],
                "drive_folder_id": clip["drive_folder_id"],
                "drive_folder_url": f"https://drive.google.com/drive/folders/{clip['drive_folder_id']}",
                "drive_id": clip["drive_id"],
                "file_name": clip["name"],
                "youtube": {
                    "publish_at": youtube_at,
                    "publish_at_local": youtube_local.strftime("%Y-%m-%d %H:%M"),
                    "publication_mode": "schedule",
                    "account_guard": {
                        "required": True,
                        "expected": manifest["target_accounts"]["youtube"],
                    },
                    "language": "pt-BR",
                    "category_id": "24",
                    "made_for_kids": False,
                    "contains_synthetic_media": False,
                    "title": clip["copy"]["youtube_title"],
                    "description": clip["copy"]["youtube_description"],
                    "tags": clip["copy"]["youtube_tags"],
                },
                "tiktok": {
                    "publish_at": tiktok_at,
                    "publish_at_local": tiktok_local.strftime("%Y-%m-%d %H:%M"),
                    "publication_mode": "schedule",
                    "account_guard": {
                        "required": True,
                        "expected": manifest["target_accounts"]["tiktok"],
                    },
                    "visibility": validate_browser_visibility(PUBLIC_TIKTOK_VISIBILITY),
                    "visibility_label": "Todos (público)",
                    "privacy_check": "required_before_schedule",
                    "verify_after_publish": True,
                    "caption": clip["copy"]["tiktok_caption"],
                },
            }
        )
    package = {
        "version": 4,
        "source_manifest_version": manifest["version"],
        "run_id": manifest["run_id"],
        "target_accounts": dict(manifest["target_accounts"]),
        "timezone": manifest["timezone"],
        "rights_authorized": True,
        "receipt_required": True,
        "tiktok_global_rule": "Nunca agendar sem confirmar Todos (público).",
        "posts": posts,
    }
    validate_browser_package(package)
    return package


def diagnostic_package(manifest: dict) -> dict:
    """Build a three-post controlled test that isolates distribution variables.

    The diagnostic package never replaces the normal ten-post package. It picks
    three clips from one batch, keeps the source/topic cluster together and
    assigns wider local gaps so the operator can measure distribution before
    increasing volume again.
    """
    validate_manifest(manifest, require_rights=True)
    timezone = ZoneInfo(manifest["timezone"])
    batches = {
        str(batch.get("batch_id", "")).strip().upper(): batch
        for batch in manifest.get("batches", [])
        if isinstance(batch, dict)
    }
    grouped: dict[str, list[dict]] = {}
    for clip in manifest["clips"]:
        grouped.setdefault(str(clip.get("batch_id", "")).strip().upper(), []).append(clip)
    eligible = [
        (sum(float(item.get("copy", {}).get("viral_score", 0) or 0) for item in clips) / max(len(clips), 1), batch_id, clips)
        for batch_id, clips in grouped.items()
        if batch_id in batches and len(clips) == 5
    ]
    if not eligible:
        raise RuntimeError("Diagnóstico de distribuição exige ao menos um lote completo de cinco cortes.")
    _, batch_id, batch_clips = max(eligible, key=lambda row: (row[0], row[1]))
    selected = sorted(
        batch_clips,
        key=lambda item: (-float(item.get("copy", {}).get("viral_score", 0) or 0), int(item.get("batch_index", 0))),
    )[:3]
    batch_day = date.fromisoformat(str(batches[batch_id]["date"]))
    slots = ((11, 30), (16, 30), (20, 30))
    posts = []
    for clip, (hour, minute) in zip(selected, slots):
        local_at = datetime.combine(batch_day, time(hour=hour, minute=minute), tzinfo=timezone)
        utc_at = local_at.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
        posts.append({
            "index": clip["index"],
            "publication_keys": {
                "youtube": publication_key(manifest["run_id"], clip["index"], "youtube"),
                "tiktok": publication_key(manifest["run_id"], clip["index"], "tiktok"),
            },
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "drive_folder_id": clip["drive_folder_id"],
            "drive_folder_url": f"https://drive.google.com/drive/folders/{clip['drive_folder_id']}",
            "drive_id": clip["drive_id"],
            "file_name": clip["name"],
            "diagnostic_slot": local_at.strftime("%Y-%m-%d %H:%M"),
            "youtube": {
                "publish_at": utc_at,
                "publish_at_local": local_at.strftime("%Y-%m-%d %H:%M"),
                "publication_mode": "manual_controlled_test",
                "account_guard": {
                    "required": True,
                    "expected": manifest["target_accounts"]["youtube"],
                },
                "language": "pt-BR",
                "category_id": "24",
                "made_for_kids": False,
                "contains_synthetic_media": False,
                "title": clip["copy"]["youtube_title"],
                "description": clip["copy"]["youtube_description"],
                "tags": clip["copy"]["youtube_tags"],
                "tags_count": len(clip["copy"]["youtube_tags"]),
                "verify_after_publish": True,
                "post_publish_checks": [
                    "visibility_public",
                    "restrictions_none",
                    "recognized_as_short",
                    "shown_in_feed_after_24h",
                    "viewed_vs_swiped_after_24h",
                ],
            },
            "tiktok": {
                "publish_at": utc_at,
                "publish_at_local": local_at.strftime("%Y-%m-%d %H:%M"),
                "publication_mode": "manual_controlled_test",
                "account_guard": {
                    "required": True,
                    "expected": manifest["target_accounts"]["tiktok"],
                },
                "visibility": validate_browser_visibility(PUBLIC_TIKTOK_VISIBILITY),
                "visibility_label": "Todos (público)",
                "privacy_check": "required_before_publish",
                "verify_after_publish": True,
                "caption": clip["copy"]["tiktok_caption"],
                "post_publish_checks": [
                    "account_check_ok",
                    "visibility_public",
                    "for_you_eligibility",
                    "originality_or_reuse_notice",
                    "views_after_2h",
                    "views_after_24h",
                ],
            },
        })
    package = {
        "version": 5,
        "mode": "distribution_diagnostic",
        "run_id": manifest["run_id"],
        "target_accounts": dict(manifest["target_accounts"]),
        "expected_posts": 3,
        "source_manifest_version": manifest["version"],
        "timezone": manifest["timezone"],
        "rights_authorized": True,
        "receipt_required": True,
        "selected_batch_id": batch_id,
        "strategy": "3 posts, one source cluster, 11:30 / 16:30 / 20:30, manual controlled test",
        "do_not_repost_identical_files": True,
        "tiktok_global_rule": "Confirmar Todos (público) e elegibilidade do Para Você após publicar.",
        "youtube_global_rule": "Registrar Mostrado no feed e Visualizaram x deslizaram após 24h.",
        "posts": posts,
    }
    validate_browser_package(package)
    return package


def validate_browser_package(package: dict) -> None:
    """Fail closed if any TikTok item is not explicitly public."""
    posts = package.get("posts") if isinstance(package, dict) else None
    targets = package.get("target_accounts") if isinstance(package, dict) else None
    if not isinstance(targets, dict) or not normalize_account_identity(targets.get("youtube")) or not normalize_account_identity(targets.get("tiktok")):
        raise RuntimeError("Pacote browser sem contas-alvo válidas.")
    expected_posts = 3 if package.get("mode") == "distribution_diagnostic" else 10
    if not isinstance(posts, list) or len(posts) != expected_posts:
        raise RuntimeError(f"Pacote browser inválido: esperado exatamente {expected_posts} publicações.")
    for post in posts:
        youtube = post.get("youtube") if isinstance(post, dict) else None
        tiktok = post.get("tiktok") if isinstance(post, dict) else None
        if not isinstance(youtube, dict):
            raise RuntimeError("Pacote browser inválido: bloco YouTube ausente.")
        if not isinstance(tiktok, dict):
            raise RuntimeError("Pacote browser inválido: bloco TikTok ausente.")
        for platform_name, block in (("youtube", youtube), ("tiktok", tiktok)):
            guard = block.get("account_guard")
            if not isinstance(guard, dict) or guard.get("required") is not True:
                raise RuntimeError(f"Pacote {platform_name} sem Account Identity Guard.")
            if normalize_account_identity(guard.get("expected")) != normalize_account_identity(targets.get(platform_name)):
                raise RuntimeError(f"Pacote {platform_name} com conta-alvo divergente.")
        tags = youtube.get("tags")
        if not isinstance(tags, list) or len(tags) != 20:
            raise RuntimeError("Pacote YouTube precisa carregar exatamente 20 tags nativas.")
        validate_browser_visibility(tiktok.get("visibility", ""))
        if tiktok.get("visibility_label") != "Todos (público)":
            raise RuntimeError("Pacote TikTok sem confirmação visual de audiência pública.")
        expected_privacy = "required_before_publish" if package.get("mode") == "distribution_diagnostic" else "required_before_schedule"
        if tiktok.get("privacy_check") != expected_privacy:
            raise RuntimeError("Pacote TikTok sem trava de privacidade antes da publicação.")
        if tiktok.get("verify_after_publish") is not True:
            raise RuntimeError("Pacote TikTok sem verificação pós-publicação.")
        if package.get("mode") == "distribution_diagnostic":
            youtube_checks = set(youtube.get("post_publish_checks") or [])
            tiktok_checks = set(tiktok.get("post_publish_checks") or [])
            if not {"shown_in_feed_after_24h", "viewed_vs_swiped_after_24h"} <= youtube_checks:
                raise RuntimeError("Diagnóstico YouTube sem métricas de distribuição obrigatórias.")
            if not {"for_you_eligibility", "originality_or_reuse_notice"} <= tiktok_checks:
                raise RuntimeError("Diagnóstico TikTok sem checagem de elegibilidade/originalidade.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Corte Fino Publisher")
    parser.add_argument("command", choices=[
        "prepare", "browser-package", "diagnostic-package", "report", "youtube", "tiktok",
        "verify-tiktok", "preflight", "validate-browser-package", "init-ledger",
        "record-receipt", "reconcile", "init-performance", "record-performance",
        "creator-feedback", "publish-feedback", "persist-state", "restore-state",
        "metrics-package", "apply-metrics-batch",
    ])
    parser.add_argument("--folder-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", FOLDER_ID))
    parser.add_argument("--folder-2-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_2_ID", ""))
    parser.add_argument("--manifest", default="publisher/state/current.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--due-only", action="store_true", help="publica no máximo um TikTok já vencido")
    parser.add_argument("--allow-immediate", action="store_true", help="confirma publicação imediata dos dez TikToks")
    parser.add_argument("--target-date", default="", help="compatibilidade: data do lote A; lote B assume o dia seguinte")
    parser.add_argument("--date-1", default="", help="data local do lote A (AAAA-MM-DD)")
    parser.add_argument("--date-2", default="", help="data local do lote B (AAAA-MM-DD)")
    parser.add_argument("--period-1", default="daily", help="grade diária de 5 posts; day/night aceitos só por compatibilidade")
    parser.add_argument("--period-2", default="daily", help="grade diária de 5 posts; day/night aceitos só por compatibilidade")
    parser.add_argument("--source-name", default=os.environ.get("PUBLISHER_SOURCE_NAME", ""), help="fonte do lote A")
    parser.add_argument("--source-episode", default=os.environ.get("PUBLISHER_SOURCE_EPISODE", ""), help="episódio do lote A")
    parser.add_argument("--source-name-2", default=os.environ.get("PUBLISHER_SOURCE_NAME_2", ""), help="fonte do lote B")
    parser.add_argument("--source-episode-2", default=os.environ.get("PUBLISHER_SOURCE_EPISODE_2", ""), help="episódio do lote B")
    parser.add_argument("--confirm-rights", action="store_true", help="confirma autorização das duas fontes")
    parser.add_argument("--youtube-account", default=os.environ.get("PUBLISHER_YOUTUBE_ACCOUNT", "@cortefinoshorts"))
    parser.add_argument("--tiktok-account", default=os.environ.get("PUBLISHER_TIKTOK_ACCOUNT", "cortefinoshorts"))
    parser.add_argument("--ledger", default="publisher/state/control_ledger.json")
    parser.add_argument("--package", default="", help="browser/diagnostic package usado para limitar o ledger")
    parser.add_argument("--publication-key", default="")
    parser.add_argument("--observed-account", default="")
    parser.add_argument("--receipt-state", default="")
    parser.add_argument("--remote-id", default="")
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--remote-reference", default="", help="referência visual/remota do Studio quando não houver ID/URL")
    parser.add_argument("--note", default="")
    parser.add_argument("--performance-ledger", default="publisher/state/performance_ledger.json")
    parser.add_argument("--horizon", default="", help="snapshot de performance: 1h, 6h, 24h ou 72h")
    parser.add_argument("--metrics-json", default="", help="objeto JSON com métricas observadas no Studio/Analytics")
    parser.add_argument("--feedback-output", default="publisher/state/creator_feedback.json")
    parser.add_argument("--run-id", default="", help="run_id persistido do Publisher")
    parser.add_argument("--state-batch-folder", default="", help="ID de uma pasta de lote para localizar o estado privado no Drive")
    parser.add_argument("--metrics-package", default="publisher/state/metrics_package.json")
    parser.add_argument("--metrics-result", default="", help="JSON preenchido pelo Work/Studio")
    args = parser.parse_args()

    path = Path(args.manifest)
    control_path = Path(args.ledger)
    performance_path = Path(args.performance_ledger)

    if args.command == "verify-tiktok":
        print(json.dumps({
            "status": "browser_only",
            "message": "A conta será validada visualmente no TikTok Studio pelo Cloud Web Browser.",
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "restore-state":
        if not args.run_id or not args.state_batch_folder:
            raise SystemExit("restore-state exige --run-id e --state-batch-folder.")
        state = load_run_state_from_drive(args.state_batch_folder, args.run_id)
        restore_run_state_files(
            state,
            manifest_path=path,
            control_path=control_path,
            performance_path=performance_path,
        )
        print(json.dumps({
            "status": "state_restored",
            "run_id": state["run_id"],
            "manifest": str(path),
            "control_ledger": str(control_path),
            "performance_ledger": str(performance_path),
        }, ensure_ascii=False))
        return 0

    if args.command == "preflight":
        data = load(path)
        print(json.dumps({"status": "ok", "manifest": browser_package(data)}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "prepare":
        date_1 = args.date_1 or args.target_date
        date_2 = args.date_2 or ((date.fromisoformat(date_1) + timedelta(days=1)).isoformat() if date_1 else "")
        if not args.folder_id or not args.folder_2_id:
            raise SystemExit("O preparo exige --folder-id e --folder-2-id.")
        if not date_1 or not date_2:
            raise SystemExit("O preparo exige --date-1; informe --date-2 ou deixe o lote B assumir o dia seguinte.")
        if not args.source_name.strip() or not args.source_name_2.strip():
            raise SystemExit("O preparo exige a fonte original de cada pasta; não reutilize a fonte do lote A por omissão.")
        rights = args.confirm_rights or os.environ.get("PUBLISHER_RIGHTS_AUTHORIZED", "").casefold() in {"1", "true", "yes", "sim", "on"}
        data = prepare_batches(
            [
                {
                    "folder_id": args.folder_id,
                    "date": date_1,
                    "period": args.period_1,
                    "source_name": args.source_name,
                    "source_episode": args.source_episode,
                    "rights_authorized": rights,
                },
                {
                    "folder_id": args.folder_2_id,
                    "date": date_2,
                    "period": args.period_2,
                    "source_name": args.source_name_2,
                    "source_episode": args.source_episode_2 or args.source_episode,
                    "rights_authorized": rights,
                },
            ],
            path,
            rights_status=os.environ.get("PUBLISHER_RIGHTS_STATUS", "revisão manual necessária"),
            target_youtube=args.youtube_account,
            target_tiktok=args.tiktok_account,
        )
        print(json.dumps({"status": "prepared", "batches": 2, "clips": len(data["clips"]), "run_id": data["run_id"]}, ensure_ascii=False))
        return 0

    data = load(path)

    if args.command == "persist-state":
        control = load_ledger(control_path)
        performance = load_performance_ledger(performance_path)
        remote = save_run_state_to_drive(data, control, performance)
        print(json.dumps({"status": "state_persisted", **remote}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "metrics-package":
        if not args.horizon:
            raise SystemExit("metrics-package exige --horizon 1h|6h|24h|72h.")
        control = load_ledger(control_path)
        performance = load_performance_ledger(performance_path)
        package = build_metrics_package(control, performance, horizon=args.horizon)
        target = Path(args.metrics_package)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        remote = save_metrics_package_to_drive(data, package)
        print(json.dumps({
            "status": "metrics_package_ready",
            "run_id": package["run_id"],
            "horizon": package["horizon"],
            "items": len(package["items"]),
            "path": str(target),
            "drive": remote,
        }, ensure_ascii=False))
        return 0

    if args.command == "apply-metrics-batch":
        package_path = Path(args.metrics_package)
        if not package_path.exists():
            raise SystemExit("Pacote de métricas não encontrado.")
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if args.metrics_result:
            result_path = Path(args.metrics_result)
            if not result_path.exists():
                raise SystemExit("Resultado de métricas não encontrado.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            result = load_metrics_result_from_drive(data, package["run_id"], package["horizon"])
        control = load_ledger(control_path)
        performance = load_performance_ledger(performance_path)
        apply_metrics_result(control, performance, package, result)
        save_performance_ledger(performance_path, performance)
        remote = save_run_state_to_drive(data, control, performance)
        learned = sum(1 for entry in performance["entries"].values() if entry.get("learning_eligible"))
        print(json.dumps({
            "status": "metrics_batch_applied",
            "run_id": performance["run_id"],
            "horizon": result["horizon"],
            "items": len(result.get("items", [])),
            "learning_eligible_total": learned,
            "state_drive": remote,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-ledger":
        selected_keys = None
        if args.package:
            package = json.loads(Path(args.package).read_text(encoding="utf-8"))
            selected_keys = {
                str(key)
                for post in package.get("posts", [])
                if isinstance(post, dict)
                for key in (post.get("publication_keys") or {}).values()
                if str(key).strip()
            }
            if not selected_keys:
                raise SystemExit("O pacote informado não contém publication_keys.")
        ledger = new_ledger(data, selected_keys)
        save_ledger(control_path, ledger)
        print(json.dumps({"status": "ledger_initialized", "entries": len(ledger["entries"]), "path": str(control_path)}, ensure_ascii=False))
        return 0

    if args.command == "record-receipt":
        if not args.publication_key or not args.observed_account or not args.receipt_state:
            raise SystemExit("record-receipt exige --publication-key, --observed-account e --receipt-state.")
        ledger = load_ledger(control_path)
        record_receipt(
            ledger,
            args.publication_key,
            observed_account=args.observed_account,
            state=args.receipt_state,
            remote_id=args.remote_id,
            remote_url=args.remote_url,
            remote_reference=args.remote_reference,
            note=args.note,
        )
        save_ledger(control_path, ledger)
        state_drive = None
        if performance_path.exists():
            performance = load_performance_ledger(performance_path)
            sync_publication_receipts(performance, ledger)
            save_performance_ledger(performance_path, performance)
            state_drive = save_run_state_to_drive(data, ledger, performance)
        print(json.dumps({
            "status": "receipt_recorded",
            "publication_key": args.publication_key,
            "state": ledger["entries"][args.publication_key]["state"],
            "state_drive": state_drive,
        }, ensure_ascii=False))
        return 0

    if args.command == "reconcile":
        ledger = load_ledger(control_path)
        print(json.dumps(reconciliation_summary(ledger), ensure_ascii=False, indent=2))
        return 0

    if args.command == "init-performance":
        if not control_path.exists():
            raise SystemExit("init-performance exige um control ledger existente.")
        control = load_ledger(control_path)
        performance = new_performance_ledger(data, control)
        save_performance_ledger(performance_path, performance)
        state_drive = save_run_state_to_drive(data, control, performance)
        print(json.dumps({
            "status": "performance_ledger_initialized",
            "entries": len(performance["entries"]),
            "path": str(performance_path),
            "state_drive": state_drive,
        }, ensure_ascii=False))
        return 0

    if args.command == "record-performance":
        if not args.publication_key or not args.horizon or not args.metrics_json:
            raise SystemExit("record-performance exige --publication-key, --horizon e --metrics-json.")
        try:
            metrics = json.loads(args.metrics_json)
        except json.JSONDecodeError as exc:
            raise SystemExit("--metrics-json precisa ser um objeto JSON válido.") from exc
        if not isinstance(metrics, dict):
            raise SystemExit("--metrics-json precisa conter um objeto JSON.")
        performance = load_performance_ledger(performance_path)
        if not control_path.exists():
            raise SystemExit("record-performance exige o control ledger para confirmar PUBLIC/VERIFIED.")
        sync_publication_receipts(performance, load_ledger(control_path))
        record_performance_snapshot(performance, args.publication_key, horizon=args.horizon, metrics=metrics)
        save_performance_ledger(performance_path, performance)
        control = load_ledger(control_path)
        state_drive = save_run_state_to_drive(data, control, performance)
        entry = performance["entries"][args.publication_key]
        print(json.dumps({
            "status": "performance_recorded",
            "publication_key": args.publication_key,
            "horizon": args.horizon,
            "classification": entry["latest_classification"],
            "learning_eligible": entry["learning_eligible"],
            "state_drive": state_drive,
        }, ensure_ascii=False))
        return 0

    if args.command == "publish-feedback":
        performance = load_performance_ledger(performance_path)
        history = load_creator_learning_history_from_drive(data) or new_learning_history()
        merge_performance_into_history(history, performance)
        feedback = creator_feedback(history)
        output = Path(args.feedback_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(feedback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        history_remote = save_creator_learning_history_to_drive(data, history)
        feedback_remote = save_creator_feedback_to_drive(data, feedback)
        print(json.dumps({
            "status": "creator_feedback_published",
            "feedback_status": feedback["status"],
            "eligible_youtube_samples": feedback["eligible_youtube_samples"],
            "history_entries": len(history["entries"]),
            "history_drive": history_remote,
            "feedback_drive": feedback_remote,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "creator-feedback":
        performance = load_performance_ledger(performance_path)
        feedback = creator_feedback(performance)
        output = Path(args.feedback_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(feedback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(feedback, ensure_ascii=False, indent=2))
        return 0

    if args.command == "browser-package":
        package = browser_package(data)
        print(json.dumps(package, ensure_ascii=False, indent=2))
        return 0

    if args.command == "diagnostic-package":
        package = diagnostic_package(data)
        print(json.dumps(package, ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-browser-package":
        package = json.loads(Path("publisher/state/browser_package.json").read_text(encoding="utf-8"))
        validate_browser_package(package)
        print(json.dumps({
            "status": "ok",
            "public_posts": len(package["posts"]),
            "visibility": PUBLIC_TIKTOK_VISIBILITY,
        }, ensure_ascii=False))
        return 0

    if args.command == "youtube":
        from publisher.google_io import publish_youtube
        print(json.dumps(publish_youtube(data, dry_run=args.dry_run), ensure_ascii=False, indent=2))
        return 0

    if args.command == "tiktok":
        print(json.dumps(
            publish_tiktok(data, dry_run=args.dry_run, due_only=args.due_only, allow_immediate=args.allow_immediate),
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    ledger = load_ledger(control_path) if control_path.exists() else None
    print(json.dumps(report(data, ledger), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

