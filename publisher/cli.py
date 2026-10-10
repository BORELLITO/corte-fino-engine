from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from publisher.google_io import FOLDER_ID, prepare, publish_youtube, verify_google_accounts
from publisher.tiktok_io import publish_tiktok, verify_tiktok_account


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(data.get("clips", [])) != 5:
        raise RuntimeError("Manifesto inválido: precisa conter 5 cortes.")
    return data


def report(manifest: dict) -> dict:
    return {
        "youtube": [{"index": c["index"], "hour": c["schedule"]["youtube_hour"], "title": c["copy"]["youtube_title"]} for c in sorted(manifest["clips"], key=lambda c: c["schedule"]["youtube_hour"])],
        "tiktok": [{"index": c["index"], "hour": c["schedule"]["tiktok_hour"], "caption": c["copy"]["tiktok_caption"]} for c in sorted(manifest["clips"], key=lambda c: c["schedule"]["tiktok_hour"])],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Corte Fino Publisher")
    parser.add_argument("command", choices=["prepare", "report", "youtube", "tiktok", "verify-tiktok", "verify-google"])
    parser.add_argument("--folder-id", default=os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", FOLDER_ID))
    parser.add_argument("--manifest", default="publisher/state/current.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--due-only", action="store_true", help="publica no máximo um TikTok já vencido no horário local")
    parser.add_argument("--target-date", default="", help="data ISO do manifesto; útil para recuperação manual (AAAA-MM-DD)")
    args = parser.parse_args()
    path = Path(args.manifest)
    if args.command == "verify-tiktok":
        print(json.dumps(verify_tiktok_account(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "verify-google":
        print(json.dumps(verify_google_accounts(args.folder_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare":
        data = prepare(args.folder_id, path, target_date=args.target_date or None)
        print(json.dumps({"status": "prepared", "date": data["date"], "clips": 5}, ensure_ascii=False))
        return 0
    data = load(path)
    if args.command == "youtube":
        print(json.dumps(publish_youtube(data, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    elif args.command == "tiktok":
        print(json.dumps(publish_tiktok(data, dry_run=args.dry_run, due_only=args.due_only), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
