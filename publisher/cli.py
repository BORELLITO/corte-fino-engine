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
    prepare_batches,
    scheduled_publish_at,
)
from publisher.tiktok_io import PUBLIC_TIKTOK_VISIBILITY, publish_tiktok, validate_browser_visibility


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def report(manifest: dict) -> dict:
    """Return the ten planned browser-only slots."""
    youtube = []
    tiktok = []
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["youtube_publish_at"]):
        youtube.append({
            "index": clip["index"],
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["youtube_publish_at"],
            "title": clip["copy"]["youtube_title"],
            "status": "pending_browser",
            "video_id": None,
        })
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["tiktok_publish_at"]):
        tiktok.append({
            "index": clip["index"],
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["tiktok_publish_at"],
            "caption": clip["copy"]["tiktok_caption"],
            "status": "pending_browser",
            "publish_id": None,
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
            "scheduled_or_complete": sum(status in {"scheduled", "SCHEDULED", "PUBLISH_COMPLETE", "published"} for status in statuses),
            "pending_or_processing": sum(status in {"pending", "pending_browser", "PENDING", "PROCESSING"} for status in statuses),
            "attention": sum(status in {"FAILED", "CANCELED", "recovery_required"} for status in statuses),
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
    parser.add_argument("command", choices=["prepare", "browser-package", "diagnostic-package", "report", "youtube", "tiktok", "verify-tiktok", "preflight", "validate-browser-package", "init-ledger", "record-receipt", "reconcile"])
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
    parser.add_argument("--youtube-account", default=os.environ.get("PUBLISHER_YOUTUBE_ACCOUNT", "@cortefinoshorts"), help="canal/handle esperado no YouTube Studio")
    parser.add_argument("--tiktok-account", default=os.environ.get("PUBLISHER_TIKTOK_ACCOUNT", "cortefinoshorts"), help="usuário esperado no TikTok Studio")
    parser.add_argument("--ledger", default="publisher/state/control_ledger.json")
    parser.add_argument("--package", default="", help="browser/diagnostic package usado para limitar o ledger")
    parser.add_argument("--publication-key", default="")
    parser.add_argument("--observed-account", default="")
    parser.add_argument("--receipt-state", default="")
    parser.add_argument("--remote-id", default="")
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--remote-reference", default="", help="referência visual/remota do Studio quando não houver ID/URL")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    path = Path(args.manifest)

    if args.command == "verify-tiktok":
        print(json.dumps({"status": "browser_only", "message": "A conta será validada visualmente no TikTok Studio pelo Cloud Web Browser."}, ensure_ascii=False, indent=2))
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
                {"folder_id": args.folder_id, "date": date_1, "period": args.period_1, "source_name": args.source_name, "source_episode": args.source_episode, "rights_authorized": rights},
                {"folder_id": args.folder_2_id, "date": date_2, "period": args.period_2, "source_name": args.source_name_2, "source_episode": args.source_episode_2 or args.source_episode, "rights_authorized": rights},
            ],
            path,
            rights_status=os.environ.get("PUBLISHER_RIGHTS_STATUS", "revisão manual necessária"),
            target_youtube=args.youtube_account,
            target_tiktok=args.tiktok_account,
        )
        print(json.dumps({"status": "prepared", "batches": 2, "clips": len(data["clips"])}, ensure_ascii=False))
        return 0

    data = load(path)
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
        save_ledger(Path(args.ledger), ledger)
        print(json.dumps({"status": "ledger_initialized", "entries": len(ledger["entries"]), "path": args.ledger}, ensure_ascii=False))
        return 0
    if args.command == "record-receipt":
        if not args.publication_key or not args.observed_account or not args.receipt_state:
            raise SystemExit("record-receipt exige --publication-key, --observed-account e --receipt-state.")
        ledger_path = Path(args.ledger)
        ledger = load_ledger(ledger_path)
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
        save_ledger(ledger_path, ledger)
        print(json.dumps({"status": "receipt_recorded", "publication_key": args.publication_key, "state": ledger["entries"][args.publication_key]["state"]}, ensure_ascii=False))
        return 0
    if args.command == "reconcile":
        ledger = load_ledger(Path(args.ledger))
        print(json.dumps(reconciliation_summary(ledger), ensure_ascii=False, indent=2))
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
        print(json.dumps({"status": "ok", "public_posts": len(package["posts"]), "visibility": PUBLIC_TIKTOK_VISIBILITY}, ensure_ascii=False))
        return 0
    if args.command == "youtube":
        from publisher.google_io import publish_youtube
        print(json.dumps(publish_youtube(data, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    elif args.command == "tiktok":
        print(json.dumps(publish_tiktok(data, dry_run=args.dry_run, due_only=args.due_only, allow_immediate=args.allow_immediate), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

