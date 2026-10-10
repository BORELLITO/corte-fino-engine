from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from publisher.google_io import FOLDER_ID, drive_service, prepare, publish_youtube, verify_google_accounts
from publisher.tiktok_io import publish_tiktok, verify_tiktok_account


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("version", 0) or 0) < 3:
        raise RuntimeError("Manifesto antigo ou incompatível; execute prepare novamente antes de publicar.")
    if len(data.get("clips", [])) != 5:
        raise RuntimeError("Manifesto inválido: precisa conter 5 cortes.")
    return data


def report(manifest: dict, drive=None) -> dict:
    """Return planned slots and, when requested, remote publication states."""
    remote: dict[str, dict] = {}
    if drive:
        for clip in manifest["clips"]:
            item = drive.files().get(fileId=clip["drive_id"], fields="id,appProperties").execute(num_retries=4)
            remote[str(clip["index"])] = item.get("appProperties", {})

    youtube = []
    tiktok = []
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["youtube_hour"]):
        properties = remote.get(str(clip["index"]), {})
        youtube_status = properties.get("cf_youtube_upload_status", "pending")
        if youtube_status == "PENDING":
            youtube_status = "recovery_required"
        if properties.get("cf_youtube_video_id") and youtube_status == "SCHEDULED":
            youtube_status = "scheduled"
        youtube.append({
            "index": clip["index"],
            "hour": clip["schedule"]["youtube_hour"],
            "title": clip["copy"]["youtube_title"],
            "status": youtube_status,
            "video_id": properties.get("cf_youtube_video_id"),
        })
    for clip in sorted(manifest["clips"], key=lambda c: c["schedule"]["tiktok_hour"]):
        properties = remote.get(str(clip["index"]), {})
        tiktok.append({
            "index": clip["index"],
            "hour": clip["schedule"]["tiktok_hour"],
            "caption": clip["copy"]["tiktok_caption"],
            "status": properties.get("cf_tiktok_status", "pending"),
            "publish_id": properties.get("cf_tiktok_publish_id") or properties.get("cf_tiktok_last_publish_id"),
        })
    statuses = [item["status"] for item in youtube + tiktok]
    return {
        "date": manifest.get("date"),
        "timezone": manifest.get("timezone", "America/Sao_Paulo"),
        "youtube": youtube,
        "tiktok": tiktok,
        "summary": {
            "total": len(statuses),
            "scheduled_or_complete": sum(status in {"scheduled", "PUBLISH_COMPLETE", "published"} for status in statuses),
            "pending_or_processing": sum(status in {"pending", "PENDING", "PROCESSING"} for status in statuses),
            "attention": sum(status in {"FAILED", "CANCELED", "recovery_required"} for status in statuses),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Corte Fino Publisher")
    parser.add_argument("command", choices=["prepare", "report", "youtube", "tiktok", "verify-tiktok", "verify-google", "preflight"])
    parser.add_argument("--folder-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", FOLDER_ID))
    parser.add_argument("--manifest", default="publisher/state/current.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--due-only", action="store_true", help="publica no máximo um TikTok já vencido no horário local")
    parser.add_argument("--allow-immediate", action="store_true", help="confirma publicação imediata de todos os TikToks")
    parser.add_argument("--target-date", default="", help="data ISO do manifesto; útil para recuperação manual (AAAA-MM-DD)")
    parser.add_argument("--remote", action="store_true", help="inclui estados persistidos no Drive no relatório")
    args = parser.parse_args()
    path = Path(args.manifest)
    if args.command == "verify-tiktok":
        print(json.dumps(verify_tiktok_account(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "verify-google":
        print(json.dumps(verify_google_accounts(args.folder_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "preflight":
        print(json.dumps({"google": verify_google_accounts(args.folder_id), "tiktok": verify_tiktok_account()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare":
        data = prepare(args.folder_id, path, target_date=args.target_date or None)
        print(json.dumps({"status": "prepared", "date": data["date"], "clips": 5}, ensure_ascii=False))
        return 0
    data = load(path)
    if args.command == "youtube":
        print(json.dumps(publish_youtube(data, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    elif args.command == "tiktok":
        print(json.dumps(
            publish_tiktok(
                data,
                dry_run=args.dry_run,
                due_only=args.due_only,
                allow_immediate=args.allow_immediate,
            ),
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(json.dumps(report(data, drive=drive_service() if args.remote else None), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
