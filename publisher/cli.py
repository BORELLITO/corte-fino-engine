from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from publisher.core import validate_manifest
from publisher.google_io import (
    FOLDER_ID,
    drive_service,
    prepare_batches,
    verify_google_accounts,
)
from publisher.tiktok_io import publish_tiktok, verify_tiktok_account


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def report(manifest: dict, drive=None) -> dict:
    """Return the ten planned slots and optional remote publication states."""
    remote: dict[str, dict] = {}
    if drive:
        for clip in manifest["clips"]:
            item = drive.files().get(fileId=clip["drive_id"], fields="id,appProperties").execute(num_retries=4)
            remote[str(clip["index"])] = item.get("appProperties", {})

    youtube = []
    tiktok = []
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["youtube_publish_at"]):
        properties = remote.get(str(clip["index"]), {})
        youtube_status = properties.get("cf_youtube_upload_status", "pending")
        if youtube_status == "PENDING":
            youtube_status = "recovery_required"
        if properties.get("cf_youtube_video_id") and youtube_status == "SCHEDULED":
            youtube_status = "scheduled"
        youtube.append({
            "index": clip["index"],
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["youtube_publish_at"],
            "title": clip["copy"]["youtube_title"],
            "status": youtube_status,
            "video_id": properties.get("cf_youtube_video_id"),
        })
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["tiktok_publish_at"]):
        properties = remote.get(str(clip["index"]), {})
        tiktok.append({
            "index": clip["index"],
            "batch_id": clip["batch_id"],
            "batch_index": clip["batch_index"],
            "publish_at": clip["schedule"]["tiktok_publish_at"],
            "caption": clip["copy"]["tiktok_caption"],
            "status": properties.get("cf_tiktok_status", "pending"),
            "publish_id": properties.get("cf_tiktok_publish_id") or properties.get("cf_tiktok_last_publish_id"),
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
            "pending_or_processing": sum(status in {"pending", "PENDING", "PROCESSING"} for status in statuses),
            "attention": sum(status in {"FAILED", "CANCELED", "recovery_required"} for status in statuses),
        },
    }


def browser_package(manifest: dict) -> dict:
    """Build the exact payload consumed by the Cloud Web Browser flow."""
    posts = []
    for clip in sorted(manifest["clips"], key=lambda item: item["schedule"]["youtube_publish_at"]):
        posts.append(
            {
                "index": clip["index"],
                "batch_id": clip["batch_id"],
                "batch_index": clip["batch_index"],
                "drive_folder_id": clip["drive_folder_id"],
                "drive_id": clip["drive_id"],
                "file_name": clip["name"],
                "youtube": {
                    "publish_at": clip["schedule"]["youtube_publish_at"],
                    "title": clip["copy"]["youtube_title"],
                    "description": clip["copy"]["youtube_description"],
                    "tags": clip["copy"]["youtube_tags"],
                },
                "tiktok": {
                    "publish_at": clip["schedule"]["tiktok_publish_at"],
                    "caption": clip["copy"]["tiktok_caption"],
                },
            }
        )
    return {"version": 1, "source_manifest_version": manifest["version"], "timezone": manifest["timezone"], "posts": posts}


def main() -> int:
    parser = argparse.ArgumentParser(description="Corte Fino Publisher")
    parser.add_argument("command", choices=["prepare", "browser-package", "report", "youtube", "tiktok", "verify-tiktok", "verify-google", "preflight"])
    parser.add_argument("--folder-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", FOLDER_ID))
    parser.add_argument("--folder-2-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_2_ID", ""))
    parser.add_argument("--manifest", default="publisher/state/current.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--due-only", action="store_true", help="publica no máximo um TikTok já vencido")
    parser.add_argument("--allow-immediate", action="store_true", help="confirma publicação imediata dos dez TikToks")
    parser.add_argument("--target-date", default="", help="compatibilidade: data do primeiro lote")
    parser.add_argument("--date-1", default="", help="data local do lote A (AAAA-MM-DD)")
    parser.add_argument("--date-2", default="", help="data local do lote B (AAAA-MM-DD)")
    parser.add_argument("--period-1", default="day", help="day/morning/first ou night/evening/second")
    parser.add_argument("--period-2", default="night", help="day/morning/first ou night/evening/second")
    parser.add_argument("--source-name", default=os.environ.get("PUBLISHER_SOURCE_NAME", ""), help="fonte do lote A")
    parser.add_argument("--source-episode", default=os.environ.get("PUBLISHER_SOURCE_EPISODE", ""), help="episódio do lote A")
    parser.add_argument("--source-name-2", default=os.environ.get("PUBLISHER_SOURCE_NAME_2", ""), help="fonte do lote B")
    parser.add_argument("--source-episode-2", default=os.environ.get("PUBLISHER_SOURCE_EPISODE_2", ""), help="episódio do lote B")
    parser.add_argument("--confirm-rights", action="store_true", help="confirma autorização das duas fontes")
    parser.add_argument("--remote", action="store_true", help="inclui estados persistidos no Drive no relatório")
    args = parser.parse_args()
    path = Path(args.manifest)

    if args.command == "verify-tiktok":
        print(json.dumps(verify_tiktok_account(), ensure_ascii=False, indent=2))
        return 0
    if args.command in {"verify-google", "preflight"}:
        folder_ids = [item for item in (args.folder_id, args.folder_2_id) if item]
        if not folder_ids:
            raise SystemExit("Informe as duas pastas do Publisher.")
        google = [verify_google_accounts(folder_id) for folder_id in folder_ids]
        if args.command == "verify-google":
            print(json.dumps(google, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"google": google, "tiktok": verify_tiktok_account()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare":
        date_1 = args.date_1 or args.target_date
        date_2 = args.date_2 or date_1
        if not args.folder_id or not args.folder_2_id:
            raise SystemExit("O preparo exige --folder-id e --folder-2-id.")
        if not date_1 or not date_2:
            raise SystemExit("O preparo exige --date-1 e --date-2, ou --target-date para ambos.")
        rights = args.confirm_rights or os.environ.get("PUBLISHER_RIGHTS_AUTHORIZED", "").casefold() in {"1", "true", "yes", "sim", "on"}
        data = prepare_batches(
            [
                {"folder_id": args.folder_id, "date": date_1, "period": args.period_1, "source_name": args.source_name, "source_episode": args.source_episode, "rights_authorized": rights},
                {"folder_id": args.folder_2_id, "date": date_2, "period": args.period_2, "source_name": args.source_name_2 or args.source_name, "source_episode": args.source_episode_2 or args.source_episode, "rights_authorized": rights},
            ],
            path,
            rights_status=os.environ.get("PUBLISHER_RIGHTS_STATUS", "revisão manual necessária"),
        )
        print(json.dumps({"status": "prepared", "batches": 2, "clips": len(data["clips"])}, ensure_ascii=False))
        return 0

    data = load(path)
    if args.command == "browser-package":
        print(json.dumps(browser_package(data), ensure_ascii=False, indent=2))
        return 0
    if args.command == "youtube":
        from publisher.google_io import publish_youtube
        print(json.dumps(publish_youtube(data, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    elif args.command == "tiktok":
        print(json.dumps(publish_tiktok(data, dry_run=args.dry_run, due_only=args.due_only, allow_immediate=args.allow_immediate), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report(data, drive=drive_service() if args.remote else None), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

