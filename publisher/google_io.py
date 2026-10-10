from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from publisher.core import TIMEZONE, YOUTUBE_HOURS, TIKTOK_HOURS, assign_slots, copy_dict, local_publish_at, make_copy, natural_index, truncate, truncate_utf8


FOLDER_ID = "15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def credentials(refresh_name: str, scopes: list[str]):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    refresh = env(refresh_name)
    if not refresh and refresh_name == "YOUTUBE_REFRESH_TOKEN":
        refresh = env("GOOGLE_REFRESH_TOKEN")
    missing = [n for n in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET") if not env(n)]
    if not refresh:
        missing.append(refresh_name)
    if missing:
        raise RuntimeError("Credenciais ausentes: " + ", ".join(missing))

    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=env("GOOGLE_CLIENT_ID"),
        client_secret=env("GOOGLE_CLIENT_SECRET"),
        scopes=scopes,
    )
    try:
        creds.refresh(Request())
    except RefreshError as exc:
        if "invalid_grant" in str(exc):
            raise RuntimeError(
                f"{refresh_name} expirado ou revogado; renove o OAuth e atualize o secret."
            ) from exc
        raise
    return creds


def drive_service():
    from googleapiclient.discovery import build

    return build(
        "drive",
        "v3",
        credentials=credentials("GOOGLE_REFRESH_TOKEN", ["https://www.googleapis.com/auth/drive"]),
        cache_discovery=False,
    )


def list_videos(drive, folder_id: str) -> list[dict]:
    q = f"'{folder_id}' in parents and trashed = false and mimeType contains 'video/'"
    files = (
        drive.files()
        .list(
            q=q,
            pageSize=100,
            orderBy="name",
            fields="files(id,name,size,mimeType,appProperties,modifiedTime)",
        )
        .execute(num_retries=4)
        .get("files", [])
    )
    files.sort(key=lambda f: (natural_index(f.get("name", "")), f.get("name", "")))
    return files


def download(drive, file_id: str, target: Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload

    request = drive.files().get_media(fileId=file_id)
    with target.open("wb") as fh:
        dl = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk(num_retries=4)


def transcribe(path: Path) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        env("PUBLISHER_WHISPER_MODEL", "small"),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
    )
    segments, _ = model.transcribe(str(path), language="pt", beam_size=3, vad_filter=True)
    return " ".join(s.text.strip() for s in segments if s.text.strip()).strip()


def publication_day(now: datetime | None = None) -> date:
    current = now or datetime.now(TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TIMEZONE)
    return current.date() + (timedelta(days=1) if current.hour >= 9 else timedelta())


def prepare(folder_id: str, output: Path) -> dict:
    drive = drive_service()
    files = list_videos(drive, folder_id)
    if len(files) != 5:
        raise RuntimeError(f"Pasta do Publisher precisa conter exatamente 5 vídeos; encontrados: {len(files)}")

    indexed = [natural_index(f.get("name", "")) for f in files]
    if indexed != [1, 2, 3, 4, 5]:
        raise RuntimeError("Os cinco vídeos precisam estar numerados de 01 a 05 no nome do arquivo.")

    clips: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="corte-fino-publisher-") as temp_dir:
        for index, item in zip(indexed, files):
            source = Path(temp_dir) / f"{index:02d}.mp4"
            download(drive, item["id"], source)
            transcript = transcribe(source)
            if len(transcript.split()) < 6:
                raise RuntimeError(f"Transcrição insuficiente para o corte {index:02d}.")
            clips.append(
                {
                    "index": index,
                    "drive_id": item["id"],
                    "name": item.get("name", ""),
                    "size": int(item.get("size", 0) or 0),
                    "mime_type": item.get("mimeType", "video/mp4"),
                    "modified_time": item.get("modifiedTime", ""),
                    "transcript": transcript,
                    "copy": copy_dict(make_copy(transcript)),
                    "schedule": {},
                }
            )

    assign_slots(clips)
    manifest = {
        "version": 1,
        "date": publication_day().isoformat(),
        "timezone": "America/Sao_Paulo",
        "drive_folder_id": folder_id,
        "youtube_hours": list(YOUTUBE_HOURS),
        "tiktok_hours": list(TIKTOK_HOURS),
        "clips": clips,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def marker(drive, file_id: str, values: dict[str, str]) -> None:
    current = drive.files().get(fileId=file_id, fields="appProperties").execute(num_retries=4)
    properties = dict(current.get("appProperties", {}))
    properties.update({key: str(value) for key, value in values.items()})
    drive.files().update(
        fileId=file_id,
        body={"appProperties": properties},
        fields="id,appProperties",
    ).execute(num_retries=4)


def publish_youtube(manifest: dict, dry_run: bool = False) -> list[dict]:
    day = date.fromisoformat(manifest["date"])
    drive = drive_service()
    youtube = None
    if not dry_run:
        from googleapiclient.discovery import build

        youtube = build(
            "youtube",
            "v3",
            credentials=credentials("YOUTUBE_REFRESH_TOKEN", ["https://www.googleapis.com/auth/youtube.upload"]),
            cache_discovery=False,
        )

    results: list[dict] = []
    for clip in sorted(manifest["clips"], key=lambda item: item["index"]):
        item = drive.files().get(fileId=clip["drive_id"], fields="id,name,appProperties").execute(num_retries=4)
        properties = item.get("appProperties", {})
        if properties.get("cf_youtube_video_id"):
            results.append({"index": clip["index"], "status": "already_published", "video_id": properties["cf_youtube_video_id"]})
            continue

        hour = int(clip["schedule"]["youtube_hour"])
        publish_at = local_publish_at(day, hour)
        title = truncate(clip["copy"]["youtube_title"], 100)
        description = truncate_utf8(clip["copy"]["youtube_description"], 5000)
        tags = clip["copy"].get("youtube_tags", [])

        if dry_run:
            results.append({"index": clip["index"], "status": "dry_run", "publish_at": publish_at, "title": title, "tags": tags})
            continue

        from googleapiclient.http import MediaFileUpload

        with tempfile.TemporaryDirectory(prefix="corte-fino-upload-") as temp_dir:
            source = Path(temp_dir) / f"{clip['index']:02d}.mp4"
            download(drive, clip["drive_id"], source)
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "24",
                    "defaultLanguage": "pt-BR",
                    "defaultAudioLanguage": "pt-BR",
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": publish_at,
                    "selfDeclaredMadeForKids": False,
                    "containsSyntheticMedia": False,
                },
            }
            response = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=MediaFileUpload(str(source), mimetype="video/mp4", resumable=True),
                notifySubscribers=False,
            ).execute(num_retries=4)

        video_id = response["id"]
        marker(
            drive,
            clip["drive_id"],
            {
                "cf_youtube_video_id": video_id,
                "cf_youtube_publish_at": publish_at,
                "cf_youtube_date": manifest["date"],
            },
        )
        results.append({"index": clip["index"], "status": "published", "video_id": video_id, "publish_at": publish_at})

    return results
