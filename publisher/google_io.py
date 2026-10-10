from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from publisher.core import TIMEZONE, YOUTUBE_HOURS, TIKTOK_HOURS, assign_slots, copy_dict, local_publish_at, make_copy, natural_index, truncate, truncate_utf8


FOLDER_ID = os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", "").strip()
YOUTUBE_PROCESSING_ATTEMPTS = 12
YOUTUBE_PROCESSING_INTERVAL = 5
PUBLISHER_MIN_CLIP_SECONDS = 45.0
PUBLISHER_MAX_CLIP_SECONDS = 90.0
PUBLISHER_MIN_FILE_BYTES = 50_000
_WHISPER_MODEL = None


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
    q = f"'{folder_id}' in parents and trashed = false and mimeType = 'video/mp4'"
    files: list[dict] = []
    page_token = None
    while True:
        kwargs = {
            "q": q,
            "pageSize": 100,
            "orderBy": "name",
            "fields": "nextPageToken,files(id,name,size,mimeType,md5Checksum,appProperties,modifiedTime,parents)",
        }
        if page_token:
            kwargs["pageToken"] = page_token
        response = drive.files().list(**kwargs).execute(num_retries=4)
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    files.sort(key=lambda f: (natural_index(f.get("name", "")), f.get("name", "")))
    return files


def _is_complete_batch(files: list[dict]) -> bool:
    return len(files) == 5 and [natural_index(item.get("name", "")) for item in files] == [1, 2, 3, 4, 5]


def resolve_publication_folder(drive, folder_id: str) -> str:
    """Resolve only the exact folder supplied by the user.

    The link is a hard content boundary: no child folder, neighboring batch or
    fallback source may be searched.
    """
    requested = normalize_folder_id(folder_id)
    direct = list_videos(drive, requested)
    if _is_complete_batch(direct):
        return requested
    raise RuntimeError(
        f"A pasta indicada precisa conter diretamente exatamente os 5 vídeos 01..05; encontrados: {len(direct)}."
    )


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

    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = WhisperModel(
            env("PUBLISHER_WHISPER_MODEL", "small"),
            device="cpu",
            compute_type="int8",
            cpu_threads=max(1, int(env("PUBLISHER_WHISPER_CPU_THREADS", "4"))),
        )
    segments, _ = _WHISPER_MODEL.transcribe(
        str(path),
        language="pt",
        beam_size=max(1, int(env("PUBLISHER_WHISPER_BEAM_SIZE", "3"))),
        vad_filter=True,
        condition_on_previous_text=False,
    )
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
    frame_rate = 0.0
    if video:
        numerator, _, denominator = str(video.get("r_frame_rate") or "0/1").partition("/")
        try:
            frame_rate = float(numerator) / max(float(denominator or 1), 1.0)
        except ValueError:
            frame_rate = 0.0
    if duration <= 0:
        errors.append("duração inválida")
    elif not PUBLISHER_MIN_CLIP_SECONDS <= duration <= PUBLISHER_MAX_CLIP_SECONDS:
        errors.append(
            f"duração {duration:.2f}s (esperado entre {PUBLISHER_MIN_CLIP_SECONDS:.0f}s e {PUBLISHER_MAX_CLIP_SECONDS:.0f}s)"
        )
    if video and video.get("pix_fmt") != "yuv420p":
        errors.append(f"pixel format {video.get('pix_fmt')} (esperado yuv420p)")
    if video and abs(frame_rate - 30.0) >= 0.1:
        errors.append(f"frame rate {frame_rate:.3f} (esperado 30)")
    if audio and str(audio.get("sample_rate") or "") != "48000":
        errors.append(f"sample rate {audio.get('sample_rate')} (esperado 48000)")
    if not path.is_file() or path.stat().st_size <= PUBLISHER_MIN_FILE_BYTES:
        errors.append("arquivo vazio ou pequeno demais")
    try:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        errors.append("arquivo não decodifica integralmente")
    if errors:
        raise RuntimeError(f"{path.name}: " + "; ".join(errors))
    return {
        "width": video["width"],
        "height": video["height"],
        "video_codec": video["codec_name"],
        "audio_codec": audio["codec_name"],
        "pixel_format": video.get("pix_fmt"),
        "frame_rate": round(frame_rate, 3),
        "audio_sample_rate": audio.get("sample_rate"),
        "duration": duration,
    }


def publication_day(now: datetime | None = None, target_date: date | str | None = None) -> date:
    if target_date:
        return date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    current = now or datetime.now(TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TIMEZONE)
    return current.date() + (timedelta(days=1) if current.hour >= 9 else timedelta())


def prepare(folder_id: str, output: Path, target_date: date | str | None = None) -> dict:
    drive = drive_service()
    folder_id = resolve_publication_folder(drive, folder_id)
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
                    "md5_checksum": item.get("md5Checksum", ""),
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
        "version": 3,
        "run_id": uuid.uuid4().hex,
        "created_at_utc": _utc_now().isoformat().replace("+00:00", "Z"),
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
    drive = drive_service()
    folder_id = resolve_publication_folder(drive, folder_id)
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
        "drive_folder_id": folder_id,
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


def youtube_processing_status(youtube, video_id: str) -> str:
    response = youtube.videos().list(
        part="processingDetails,status",
        id=video_id,
    ).execute(num_retries=4)
    items = response.get("items", [])
    if not items:
        return "unknown"
    details = items[0].get("processingDetails", {})
    return str(details.get("processingStatus", "unknown")).lower()


def wait_youtube_processing(youtube, video_id: str) -> str:
    """Confirm processing without treating an in-flight upload as complete."""
    latest = "unknown"
    for attempt in range(YOUTUBE_PROCESSING_ATTEMPTS):
        try:
            latest = youtube_processing_status(youtube, video_id)
        except Exception:
            latest = "unknown"
        if latest in {"succeeded", "failed"}:
            return latest
        if attempt < YOUTUBE_PROCESSING_ATTEMPTS - 1:
            time.sleep(YOUTUBE_PROCESSING_INTERVAL)
    return latest


def marker(drive, file_id: str, values: dict[str, str]) -> None:
    current = drive.files().get(fileId=file_id, fields="appProperties").execute(num_retries=4)
    properties = dict(current.get("appProperties", {}))
    properties.update({key: str(value) for key, value in values.items()})
    drive.files().update(
        fileId=file_id,
        body={"appProperties": properties},
        fields="id,appProperties",
    ).execute(num_retries=4)


def verify_manifest_clip(drive, manifest: dict, clip: dict) -> dict:
    """Guarantee that publication still targets the exact prepared Drive file."""
    item = drive.files().get(
        fileId=clip["drive_id"],
        fields="id,name,size,mimeType,md5Checksum,parents,trashed,appProperties",
    ).execute(num_retries=4)
    expected_folder = normalize_folder_id(manifest["drive_folder_id"])
    parents = set(item.get("parents", []))
    if item.get("trashed") or expected_folder not in parents:
        raise RuntimeError(
            f"Conteúdo do corte {clip['index']:02d} mudou de pasta ou foi para a lixeira; publicação bloqueada."
        )
    if item.get("name") != clip.get("name") or item.get("mimeType") != "video/mp4":
        raise RuntimeError(f"Metadados do corte {clip['index']:02d} mudaram desde o preflight; publicação bloqueada.")
    expected_size = int(clip.get("size", 0) or 0)
    current_size = int(item.get("size", 0) or 0)
    if expected_size and current_size != expected_size:
        raise RuntimeError(f"Tamanho do corte {clip['index']:02d} mudou desde o preflight; publicação bloqueada.")
    expected_md5 = str(clip.get("md5_checksum", "") or "").strip()
    current_md5 = str(item.get("md5Checksum", "") or "").strip()
    if expected_md5 and current_md5 and expected_md5 != current_md5:
        raise RuntimeError(f"Checksum do corte {clip['index']:02d} mudou desde o preflight; publicação bloqueada.")
    return item


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
        item = verify_manifest_clip(drive, manifest, clip)
        properties = item.get("appProperties", {})
        existing_video_id = properties.get("cf_youtube_video_id", "").strip()
        if existing_video_id:
            existing_status = properties.get("cf_youtube_upload_status", "")
            if existing_status == "FAILED":
                raise RuntimeError(
                    f"YouTube registrou falha no corte {clip['index']:02d}; reconcilie o estado antes de reenviar."
                )
            if existing_status == "PROCESSING" and not dry_run:
                processing = wait_youtube_processing(youtube, existing_video_id)
                if processing == "succeeded":
                    marker(
                        drive,
                        clip["drive_id"],
                        {"cf_youtube_upload_status": "SCHEDULED"},
                    )
                    existing_status = "SCHEDULED"
                elif processing == "failed":
                    marker(
                        drive,
                        clip["drive_id"],
                        {"cf_youtube_upload_status": "FAILED"},
                    )
                    raise RuntimeError(f"Processamento YouTube falhou para o corte {clip['index']:02d}.")
            results.append({
                "index": clip["index"],
                "status": "already_published" if existing_status == "SCHEDULED" else "processing",
                "video_id": existing_video_id,
            })
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
            processing = wait_youtube_processing(youtube, recovered_id)
            if processing == "failed":
                marker(drive, clip["drive_id"], {"cf_youtube_upload_status": "FAILED"})
                raise RuntimeError(f"Processamento YouTube falhou para o corte {clip['index']:02d}.")
            recovered_status = "SCHEDULED" if processing == "succeeded" else "PROCESSING"
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_youtube_video_id": recovered_id,
                    "cf_youtube_upload_status": recovered_status,
                    "cf_youtube_publish_at": publish_at,
                    "cf_youtube_date": manifest["date"],
                },
            )
            results.append({"index": clip["index"], "status": recovered_status.lower(), "video_id": recovered_id, "publish_at": publish_at})
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
        processing = wait_youtube_processing(youtube, video_id)
        if processing == "failed":
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_youtube_video_id": video_id,
                    "cf_youtube_upload_status": "FAILED",
                    "cf_youtube_publish_at": publish_at,
                    "cf_youtube_date": manifest["date"],
                },
            )
            raise RuntimeError(f"Processamento YouTube falhou para o corte {clip['index']:02d}.")
        final_status = "SCHEDULED" if processing == "succeeded" else "PROCESSING"
        marker(
            drive,
            clip["drive_id"],
            {
                "cf_youtube_video_id": video_id,
                "cf_youtube_upload_status": final_status,
                "cf_youtube_publish_at": publish_at,
                "cf_youtube_date": manifest["date"],
            },
        )
        results.append({"index": clip["index"], "status": final_status.lower(), "video_id": video_id, "publish_at": publish_at})

    return results
