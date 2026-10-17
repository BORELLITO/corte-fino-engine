from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from publisher.core import validate_manifest
from publisher.google_io import (
    FOLDER_ID,
    prepare_batches,
    scheduled_publish_at,
)
from publisher.tiktok_io import publish_tiktok


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
                    "visibility": "PUBLIC_TO_EVERYONE",
                    "caption": clip["copy"]["tiktok_caption"],
                },
            }
        )
    return {
        "version": 2,
        "source_manifest_version": manifest["version"],
        "timezone": manifest["timezone"],
        "rights_authorized": True,
        "posts": posts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Corte Fino Publisher")
    parser.add_argument("command", choices=["prepare", "browser-package", "report", "youtube", "tiktok", "verify-tiktok", "preflight"])
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
        date_2 = args.date_2 or date_1
        if not args.folder_id or not args.folder_2_id:
            raise SystemExit("O preparo exige --folder-id e --folder-2-id.")
        if not date_1 or not date_2:
            raise SystemExit("O preparo exige --date-1 e --date-2, ou --target-date para ambos.")
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
        print(json.dumps(report(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

