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

from publisher.core import (
    BRANDING_CAPTION_MARGIN_V,
    BRANDING_FORMAT,
    BRANDING_VERSION,
    BRANDING_LOGO_POSITION,
    MANIFEST_VERSION,
    TIMEZONE,
    YOUTUBE_DESCRIPTION_LIMIT,
    YOUTUBE_HOURS,
    YOUTUBE_TITLE_LIMIT,
    TIKTOK_HOURS,
    as_bool,
    assign_slots,
    copy_dict,
    local_publish_at,
    make_copy,
    natural_index,
    normalize_period,
    period_hours,
    truncate,
    truncate_utf8,
    validate_credit_source,
    validate_manifest,
)


FOLDER_ID = os.environ.get("PUBLISHER_DRIVE_FOLDER_ID", "").strip()
YOUTUBE_PROCESSING_ATTEMPTS = 12
YOUTUBE_PROCESSING_INTERVAL = 5
PUBLISHER_MIN_CLIP_SECONDS = 60.01
PUBLISHER_MAX_CLIP_SECONDS = 90.0
PUBLISHER_MIN_FILE_BYTES = 50_000
PUBLISHER_MIN_AUDIO_BITRATE = 128_000
PUBLISHER_MIN_VIDEO_BITRATE = 6_000_000
_WHISPER_MODEL = None


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name, "1" if default else "0").casefold()
    return value in {"1", "true", "yes", "sim", "on"}


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


def list_children(drive, folder_id: str) -> list[dict]:
    folder_id = normalize_folder_id(folder_id)
    q = f"'{folder_id}' in parents and trashed = false"
    files: list[dict] = []
    page_token = None
    while True:
        kwargs = {
            "q": q,
            "pageSize": 100,
            "orderBy": "name",
            "fields": "nextPageToken,files(id,name,size,mimeType,md5Checksum,modifiedTime,parents)",
        }
        if page_token:
            kwargs["pageToken"] = page_token
        response = drive.files().list(**kwargs).execute(num_retries=4)
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return files


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
            "fields": "nextPageToken,files(id,name,size,mimeType,md5Checksum,modifiedTime,parents)",
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
    children = list_children(drive, requested)
    direct = [item for item in children if item.get("mimeType") == "video/mp4"]
    unexpected = [item.get("name", "") for item in children if item.get("mimeType") != "video/mp4"]
    if _is_complete_batch(direct) and not unexpected:
        return requested
    raise RuntimeError(
        "A pasta indicada precisa conter diretamente exatamente os 5 vídeos 01..05, "
        f"sem subpastas ou arquivos extras; vídeos={len(direct)}, extras={unexpected}."
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
        try:
            video_bitrate = int(video.get("bit_rate") or 0)
        except (TypeError, ValueError):
            video_bitrate = 0
        if not video_bitrate:
            errors.append("bitrate de vídeo ausente (não foi possível verificar o piso de qualidade)")
        elif video_bitrate < PUBLISHER_MIN_VIDEO_BITRATE:
            errors.append(
                f"bitrate de vídeo {video_bitrate} (mínimo {PUBLISHER_MIN_VIDEO_BITRATE})"
            )
        if video.get("codec_name") != "h264":
            errors.append(f"codec de vídeo {video.get('codec_name')} (esperado h264)")
        if str(video.get("profile") or "").lower() != "high":
            errors.append(f"perfil de vídeo {video.get('profile')} (esperado High)")
        if str(video.get("pix_fmt") or "") != "yuv420p":
            errors.append(f"pixel format {video.get('pix_fmt')} (esperado yuv420p)")
        if str(video.get("sample_aspect_ratio") or "") not in {"1:1", "1/1"}:
            errors.append(f"sample aspect ratio {video.get('sample_aspect_ratio')} (esperado 1:1)")
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
    if audio:
        try:
            audio_bitrate = int(audio.get("bit_rate") or 0)
        except (TypeError, ValueError):
            audio_bitrate = 0
        if not audio_bitrate:
            errors.append("bitrate de áudio ausente (não foi possível verificar o piso de qualidade)")
        elif audio_bitrate < PUBLISHER_MIN_AUDIO_BITRATE:
            errors.append(f"bitrate de áudio {audio_bitrate} (mínimo {PUBLISHER_MIN_AUDIO_BITRATE})")
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
        "video_bitrate": video_bitrate,
        "audio_codec": audio["codec_name"],
        "pixel_format": video.get("pix_fmt"),
        "video_profile": video.get("profile"),
        "sample_aspect_ratio": video.get("sample_aspect_ratio"),
        "frame_rate": round(frame_rate, 3),
        "audio_sample_rate": audio.get("sample_rate"),
        "audio_bitrate": audio.get("bit_rate"),
        "duration": duration,
    }


def publication_day(now: datetime | None = None, target_date: date | str | None = None) -> date:
    if target_date:
        return date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    current = now or datetime.now(TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TIMEZONE)
    return current.date() + (timedelta(days=1) if current.hour >= 9 else timedelta())


def _prepare_batch(
    drive,
    spec: dict,
    batch_id: str,
    start_index: int,
) -> tuple[dict, list[dict]]:
    folder_id = resolve_publication_folder(drive, str(spec.get("folder_id", "")))
    files = list_videos(drive, folder_id)
    if len(files) != 5:
        raise RuntimeError(f"Pasta {batch_id} precisa conter exatamente 5 vídeos; encontrados: {len(files)}")
    indexed = [natural_index(f.get("name", "")) for f in files]
    if indexed != [1, 2, 3, 4, 5]:
        raise RuntimeError(f"Pasta {batch_id}: os vídeos precisam estar numerados de 01 a 05.")
    try:
        batch_day = date.fromisoformat(str(spec.get("date", "")))
    except ValueError as exc:
        raise RuntimeError(f"Data inválida no lote {batch_id}; use AAAA-MM-DD.") from exc
    period = normalize_period(str(spec.get("period", "")))
    hours = period_hours(period)
    source_name = validate_credit_source(str(spec.get("source_name", "") or "").strip(), required=True)
    source_episode = str(spec.get("source_episode", "") or "").strip()
    rights_authorized = as_bool(spec.get("rights_authorized"))
    clips: list[dict] = []
    with tempfile.TemporaryDirectory(prefix=f"corte-fino-publisher-{batch_id.lower()}-") as temp_dir:
        for batch_index, item in zip(indexed, files):
            global_index = start_index + batch_index
            source = Path(temp_dir) / f"{global_index:02d}.mp4"
            download(drive, item["id"], source)
            profile = probe_video(source)
            transcript = transcribe(source)
            if len(transcript.split()) < 6:
                raise RuntimeError(f"Transcrição insuficiente para o corte {global_index:02d}.")
            clips.append(
                {
                    "index": global_index,
                    "batch_id": batch_id,
                    "batch_index": batch_index,
                    "drive_folder_id": folder_id,
                    "drive_id": item["id"],
                    "name": item.get("name", ""),
                    "size": int(item.get("size", 0) or 0),
                    "md5_checksum": item.get("md5Checksum", ""),
                    "mime_type": item.get("mimeType", "video/mp4"),
                    "modified_time": item.get("modifiedTime", ""),
                    "video_profile": profile,
                    "transcript": transcript,
                    "copy": copy_dict(make_copy(transcript, source_name, source_episode)),
                    "schedule": {},
                }
            )
    assign_slots(clips, hours)
    for clip in clips:
        hour = int(clip["schedule"]["youtube_hour"])
        publish_at = local_publish_at(batch_day, hour)
        clip["schedule"].update(
            {
                "youtube_publish_at": publish_at,
                "tiktok_publish_at": publish_at,
            }
        )
    return (
        {
            "batch_id": batch_id,
            "drive_folder_id": folder_id,
            "date": batch_day.isoformat(),
            "period": period,
            "hours": list(hours),
            "source": {"name": source_name, "episode": source_episode},
            "rights_authorized": rights_authorized,
        },
        clips,
    )


def prepare_batches(
    batch_specs: list[dict],
    output: Path,
    *,
    rights_status: str | None = None,
) -> dict:
    if len(batch_specs) != 2:
        raise RuntimeError("O Publisher exige exatamente duas pastas por rodada.")
    drive = drive_service()
    batches: list[dict] = []
    clips: list[dict] = []
    for position, spec in enumerate(batch_specs):
        batch, batch_clips = _prepare_batch(drive, spec, chr(ord("A") + position), position * 5)
        batches.append(batch)
        clips.extend(batch_clips)
    if batches[0]["drive_folder_id"] == batches[1]["drive_folder_id"]:
        raise RuntimeError("As duas pastas da rodada precisam ser diferentes.")
    if batches[0]["date"] == batches[1]["date"]:
        raise RuntimeError(
            "O modo 5 por dia exige datas diferentes: lote A em um dia e lote B no dia seguinte."
        )
    all_slots = [(batch["date"], hour) for batch in batches for hour in batch["hours"]]
    if len(all_slots) != len(set(all_slots)):
        raise RuntimeError("Os períodos das duas pastas possuem horários conflitantes.")
    rights_authorized = all(as_bool(spec.get("rights_authorized")) for spec in batch_specs)
    manifest = {
        "version": MANIFEST_VERSION,
        "run_id": uuid.uuid4().hex,
        "created_at_utc": _utc_now().isoformat().replace("+00:00", "Z"),
        "date": batches[0]["date"],
        "timezone": "America/Sao_Paulo",
        "drive_folder_id": batches[0]["drive_folder_id"],
        "drive_folder_ids": [batch["drive_folder_id"] for batch in batches],
        "youtube_hours": list(YOUTUBE_HOURS),
        "tiktok_hours": list(TIKTOK_HOURS),
        "batches": batches,
        "rights": {
            "authorized": rights_authorized,
            "status": (rights_status or env("PUBLISHER_RIGHTS_STATUS", "revisão manual necessária")).strip(),
        },
        "source": batches[0]["source"],
        "sources": [batch["source"] for batch in batches],
        "branding": {
            "version": BRANDING_VERSION,
            "format": BRANDING_FORMAT,
            "logo_position": BRANDING_LOGO_POSITION,
            "caption_margin_v": BRANDING_CAPTION_MARGIN_V,
        },
        "clips": clips,
    }
    # Um manifesto sem direitos confirmados não chega ao pacote de postagem.
    # A confirmação é obrigatória antes de qualquer ação no Studio.
    validate_manifest(manifest, require_rights=True, require_transcripts=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def prepare(
    folder_id: str,
    output: Path,
    target_date: date | str | None = None,
    *,
    folder_2_id: str = "",
    period_1: str = "daily",
    period_2: str = "daily",
    date_2: date | str | None = None,
    rights_authorized: bool | None = None,
    rights_status: str | None = None,
    source_name: str = "",
    source_episode: str = "",
    source_name_2: str = "",
    source_episode_2: str = "",
) -> dict:
    """Compatibility wrapper; production always supplies two folders."""
    if not folder_2_id:
        raise RuntimeError("O novo Publisher exige duas pastas por rodada; informe folder_2_id.")
    day_1 = publication_day(target_date=target_date).isoformat() if target_date else publication_day().isoformat()
    day_2 = date_2.isoformat() if isinstance(date_2, date) else (str(date_2) if date_2 else day_1)
    authorized = env_bool("PUBLISHER_RIGHTS_AUTHORIZED") if rights_authorized is None else as_bool(rights_authorized)
    return prepare_batches(
        [
            {"folder_id": folder_id, "date": day_1, "period": period_1, "source_name": source_name or env("PUBLISHER_SOURCE_NAME"), "source_episode": source_episode or env("PUBLISHER_SOURCE_EPISODE"), "rights_authorized": authorized},
            {"folder_id": folder_2_id, "date": day_2, "period": period_2, "source_name": source_name_2 or source_name or env("PUBLISHER_SOURCE_NAME"), "source_episode": source_episode_2 or source_episode or env("PUBLISHER_SOURCE_EPISODE"), "rights_authorized": authorized},
        ],
        output,
        rights_status=rights_status,
    )


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def scheduled_publish_at(manifest: dict, clip: dict, platform: str = "youtube") -> str:
    """Return the immutable per-clip timestamp stored by the v6 manifest."""
    key = f"{platform}_publish_at"
    value = str((clip.get("schedule") or {}).get(key, "")).strip()
    if value:
        return value
    hour = int((clip.get("schedule") or {}).get(f"{platform}_hour"))
    return local_publish_at(date.fromisoformat(manifest["date"]), hour)


def scheduled_local_date(manifest: dict, clip: dict, platform: str = "youtube") -> str:
    parsed = _parse_utc(scheduled_publish_at(manifest, clip, platform))
    if not parsed:
        return str(manifest.get("date", ""))
    return parsed.astimezone(TIMEZONE).date().isoformat()


def publish_youtube(manifest: dict, dry_run: bool = False) -> list[dict]:
    """Return a local preview; real posting is performed in YouTube Studio."""
    if not dry_run:
        raise RuntimeError(
            "Publicação YouTube por API removida: o fluxo oficial usa o Cloud Web Browser no YouTube Studio."
        )
    results: list[dict] = []
    for clip in sorted(manifest["clips"], key=lambda item: item["index"]):
        copy = clip["copy"]
        results.append(
            {
                "index": clip["index"],
                "status": "dry_run",
                "publish_at": scheduled_publish_at(manifest, clip, "youtube"),
                "title": truncate(copy["youtube_title"], YOUTUBE_TITLE_LIMIT),
                "description": truncate_utf8(copy["youtube_description"], YOUTUBE_DESCRIPTION_LIMIT),
                "tags": list(copy.get("youtube_tags", [])),
            }
        )
    return results


