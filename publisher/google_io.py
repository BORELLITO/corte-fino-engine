from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from publisher.core import TIMEZONE, YOUTUBE_HOURS, TIKTOK_HOURS, assign_slots, copy_dict, local_publish_at, make_copy, natural_index, truncate, truncate_utf8


FOLDER_ID = "15UJh2z5hBRKB8q_JpNpH1rcZZUANO6Da"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def normalize_folder_id(value: str) -> str:
    """Accept a Drive folder ID or a standard Drive folder URL."""
    raw = (value or "").strip()
    if not raw:
        raise RuntimeError("Informe o ID ou o link da pasta do Google Drive.")

    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        marker = "/folders/"
        if marker in parsed.path:
            candidate = parsed.path.split(marker, 1)[1].split("/", 1)[0]
        else:
            candidate = parse_qs(parsed.query).get("id", [""])[0]
        if not candidate:
            raise RuntimeError("Link do Drive inválido: use o link de uma pasta (/folders/ID).")
    else:
        candidate = raw

    candidate = candidate.strip().strip("/")
    if not candidate or "/" in candidate or any(char.isspace() for char in candidate):
        raise RuntimeError("ID da pasta do Drive inválido.")
    return candidate


def credentials(refresh_name: str, scopes: list[str]):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    refresh = env(refresh_name)
    missing = [
        n
        for n in ("PUBLISHER_GOOGLE_CLIENT_ID", "PUBLISHER_GOOGLE_CLIENT_SECRET")
        if not env(n)
    ]
    if not refresh:
        missing.append(refresh_name)
    if missing:
        raise RuntimeError("Credenciais ausentes: " + ", ".join(missing))

    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=env("PUBLISHER_GOOGLE_CLIENT_ID"),
        client_secret=env("PUBLISHER_GOOGLE_CLIENT_SECRET"),
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
        credentials=credentials("PUBLISHER_GOOGLE_REFRESH_TOKEN", ["https://www.googleapis.com/auth/drive"]),
        cache_discovery=False,
    )


def list_videos(drive, folder_id: str) -> list[dict]:
    folder_id = normalize_folder_id(folder_id)
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


def probe_video(path: Path) -> dict:
    """Fail early when a Drive file is not the contract's 9:16 MP4."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffprobe não está disponível no runner; não foi possível validar o vídeo.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Vídeo inválido para o Publisher: {path.name}.") from exc

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe devolveu metadados inválidos para {path.name}.") from exc
    streams = metadata.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    errors: list[str] = []
    if not video:
        errors.append("sem stream de vídeo")
    else:
        if (video.get("width"), video.get("height")) != (1080, 1920):
            errors.append(f"resolução {video.get('width')}x{video.get('height')} (esperado 1080x1920)")
        if video.get("codec_name") != "h264":
            errors.append(f"codec de vídeo {video.get('codec_name')} (esperado h264)")
    if not audio:
        errors.append("sem stream de áudio")
    elif audio.get("codec_name") != "aac":
        errors.append(f"codec de áudio {audio.get('codec_name')} (esperado aac)")
    duration = float((metadata.get("format") or {}).get("duration") or 0)
    if duration <= 0:
        errors.append("duração inválida")
    if errors:
        raise RuntimeError(f"{path.name}: " + "; ".join(errors))
    return {"width": video["width"], "height": video["height"], "video_codec": video["codec_name"], "audio_codec": audio["codec_name"], "duration": duration}


def publication_day(now: datetime | None = None, target_date: date | str | None = None) -> date:
    if target_date:
        return date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    current = now or datetime.now(TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TIMEZONE)
    return current.date() + (timedelta(days=1) if current.hour >= 9 else timedelta())


def prepare(folder_id: str, output: Path, target_date: date | str | None = None) -> dict:
    folder_id = normalize_folder_id(folder_id)
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
            profile = probe_video(source)
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
                    "video_profile": profile,
                    "transcript": transcript,
                    "copy": copy_dict(make_copy(transcript)),
                    "schedule": {},
                }
            )

    assign_slots(clips)
    manifest = {
        "version": 1,
        "date": publication_day(target_date=target_date).isoformat(),
        "timezone": "America/Sao_Paulo",
        "drive_folder_id": folder_id,
        "youtube_hours": list(YOUTUBE_HOURS),
        "tiktok_hours": list(TIKTOK_HOURS),
        "clips": clips,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def verify_google_accounts(folder_id: str) -> dict:
    """Read-only preflight for Drive and the OAuth credentials used by Publisher."""
    folder_id = normalize_folder_id(folder_id)
    drive = drive_service()
    files = list_videos(drive, folder_id)
    indexed = [natural_index(item.get("name", "")) for item in files]
    if len(files) != 5 or indexed != [1, 2, 3, 4, 5]:
        raise RuntimeError(f"Preflight Drive falhou: esperados 5 vídeos 01..05, encontrados {indexed}.")
    invalid = [
        item.get("name", "")
        for item in files
        if item.get("mimeType") != "video/mp4" or int(item.get("size", 0) or 0) <= 0
    ]
    if invalid:
        raise RuntimeError("Preflight Drive encontrou arquivos inválidos: " + ", ".join(invalid))
    # Apenas renova o token: consultar canais exigiria um escopo adicional e
    # não deve invalidar um refresh token emitido originalmente para upload.
    credentials("PUBLISHER_YOUTUBE_REFRESH_TOKEN", ["https://www.googleapis.com/auth/youtube.upload"])
    return {
        "status": "ok",
        "drive_videos": [{"index": index, "name": item.get("name", "")} for index, item in zip(indexed, files)],
        "youtube_credentials": "ok",
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def reconcile_youtube_upload(youtube, title: str, intent_at: str) -> str | None:
    """Find a just-created upload when the Drive marker was not finalized."""
    intent = _parse_utc(intent_at)
    if not intent:
        return None
    try:
        response = youtube.search().list(
            part="id,snippet",
            forMine=True,
            type="video",
            q=title,
            order="date",
            maxResults=25,
        ).execute(num_retries=4)
    except Exception:
        # A token scoped only for upload may not be allowed to search the
        # channel. In that case, block a duplicate and request reconciliation.
        return None
    lower_bound = intent - timedelta(minutes=10)
    # O upload pode ser reconciliado até 24h depois da intenção; depois disso
    # a confirmação automática fica ambígua demais e exige revisão manual.
    upper_bound = intent + timedelta(hours=24)
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        if snippet.get("title", "").strip() != title.strip():
            continue
        published_at = _parse_utc(snippet.get("publishedAt", ""))
        video_id = (item.get("id") or {}).get("videoId")
        if video_id and published_at and lower_bound <= published_at <= upper_bound:
            return video_id
    return None


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
            credentials=credentials("PUBLISHER_YOUTUBE_REFRESH_TOKEN", ["https://www.googleapis.com/auth/youtube.upload"]),
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

        if properties.get("cf_youtube_upload_status") == "PENDING":
            if dry_run:
                results.append({"index": clip["index"], "status": "recovery_required", "title": title})
                continue
            recovered_id = reconcile_youtube_upload(
                youtube,
                title,
                properties.get("cf_youtube_intent_at", ""),
            )
            if not recovered_id:
                raise RuntimeError(
                    f"Upload YouTube do corte {clip['index']:02d} ficou pendente sem reconciliação segura; "
                    "o envio foi bloqueado para evitar duplicidade."
                )
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_youtube_video_id": recovered_id,
                    "cf_youtube_upload_status": "SCHEDULED",
                    "cf_youtube_publish_at": publish_at,
                    "cf_youtube_date": manifest["date"],
                },
            )
            results.append({"index": clip["index"], "status": "reconciled", "video_id": recovered_id, "publish_at": publish_at})
            continue

        if dry_run:
            results.append({"index": clip["index"], "status": "dry_run", "publish_at": publish_at, "title": title, "tags": tags})
            continue

        publish_dt = _parse_utc(publish_at)
        if publish_dt and publish_dt <= _utc_now():
            raise RuntimeError(
                f"Horário do YouTube para o corte {clip['index']:02d} já passou ({publish_at}); "
                "gere um manifesto com --target-date futuro para recuperar."
            )

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
            intent_at = _utc_now().isoformat().replace("+00:00", "Z")
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_youtube_upload_status": "PENDING",
                    "cf_youtube_intent_at": intent_at,
                    "cf_youtube_title": title,
                    "cf_youtube_publish_at": publish_at,
                    "cf_youtube_date": manifest["date"],
                },
            )
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
                "cf_youtube_upload_status": "SCHEDULED",
                "cf_youtube_publish_at": publish_at,
                "cf_youtube_date": manifest["date"],
            },
        )
        results.append({"index": clip["index"], "status": "published", "video_id": video_id, "publish_at": publish_at})

    return results
