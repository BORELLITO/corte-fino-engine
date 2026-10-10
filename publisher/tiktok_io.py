from __future__ import annotations

import json
import math
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time
from pathlib import Path

from publisher.core import TIMEZONE, local_publish_at, truncate_utf8
from publisher.google_io import download, drive_service, env, marker, verify_manifest_clip


API_ROOT = "https://open.tiktokapis.com/v2"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
CHUNK_SIZE = 10 * 1024 * 1024
POLL_SECONDS = 5
POLL_ATTEMPTS = 24
UPLOAD_ATTEMPTS = 3
TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "FAILED", "CANCELED"}


class TikTokError(RuntimeError):
    pass


def _json_request(url: str, *, method: str = "POST", token: str = "", body: dict | None = None) -> dict:
    payload = json.dumps(body or {}).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise TikTokError(f"TikTok HTTP {exc.code}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise TikTokError(f"Falha de rede no TikTok: {exc.reason}") from exc
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TikTokError("TikTok devolveu uma resposta inválida.") from exc
    error = result.get("error", {})
    if error and error.get("code") not in (None, "ok"):
        raise TikTokError(f"TikTok {error.get('code')}: {error.get('message', 'erro sem mensagem')}")
    return result


def _refresh_access_token() -> str:
    required = ("PUBLISHER_TIKTOK_CLIENT_KEY", "PUBLISHER_TIKTOK_CLIENT_SECRET", "PUBLISHER_TIKTOK_REFRESH_TOKEN")
    missing = [name for name in required if not env(name)]
    if missing:
        raise TikTokError("Credenciais ausentes: " + ", ".join(missing))
    form = urllib.parse.urlencode(
        {
            "client_key": env("PUBLISHER_TIKTOK_CLIENT_KEY"),
            "client_secret": env("PUBLISHER_TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": env("PUBLISHER_TIKTOK_REFRESH_TOKEN"),
        }
    ).encode("utf-8")
    request = urllib.request.Request(TOKEN_URL, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise TikTokError(f"TikTok token HTTP {exc.code}: {detail[:500]}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise TikTokError("Não foi possível renovar o token do TikTok.") from exc
    if result.get("error"):
        raise TikTokError(f"TikTok token {result.get('error')}: {result.get('error_description', '')}".strip())
    token = result.get("access_token", "")
    if not token:
        raise TikTokError("TikTok não retornou access_token.")
    rotated_refresh = result.get("refresh_token")
    if rotated_refresh and rotated_refresh != env("PUBLISHER_TIKTOK_REFRESH_TOKEN"):
        raise TikTokError(
            "TikTok rotacionou o refresh token; atualize PUBLISHER_TIKTOK_REFRESH_TOKEN "
            "antes de publicar novamente."
        )
    return token


def _creator_info(token: str) -> dict:
    result = _json_request(f"{API_ROOT}/post/publish/creator_info/query/", token=token)
    data = result.get("data", {})
    if not data.get("privacy_level_options"):
        raise TikTokError("A conta TikTok não retornou opções de privacidade para publicação.")
    return data


def verify_tiktok_account() -> dict:
    """Validate TikTok OAuth and return non-secret account metadata.

    This is intentionally read-only: it refreshes the access token and calls
    creator_info, but it never initializes a post or uploads a video.
    """
    token = _refresh_access_token()
    creator = _creator_info(token)
    username = str(creator.get("creator_username", "")).strip()
    expected = env("PUBLISHER_TIKTOK_EXPECTED_USERNAME")
    if expected and username and username.casefold() != expected.lstrip("@").casefold():
        raise TikTokError(
            f"Conta TikTok incorreta: token pertence a @{username}, "
            f"mas o Publisher espera @{expected.lstrip('@')}."
        )
    return {
        "status": "ok",
        "creator_username": username or None,
        "creator_nickname": creator.get("creator_nickname") or None,
        "privacy_levels": creator.get("privacy_level_options", []),
        "selected_privacy_level": choose_privacy_level(creator),
        "comment_disabled": bool(creator.get("comment_disabled", False)),
        "duet_disabled": bool(creator.get("duet_disabled", False)),
        "stitch_disabled": bool(creator.get("stitch_disabled", False)),
        "expected_username_check": bool(expected),
    }


def choose_privacy_level(creator: dict, desired: str | None = None) -> str:
    options = [str(option) for option in creator.get("privacy_level_options", [])]
    desired = desired or env("PUBLISHER_TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")
    if desired not in options:
        raise TikTokError(
            f"Privacidade TikTok indisponível: {desired}. Opções retornadas: {', '.join(options) or 'nenhuma'}"
        )
    return desired


def _upload_file(upload_url: str, path: Path) -> None:
    size = path.stat().st_size
    with path.open("rb") as source:
        start = 0
        while start < size:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            end = start + len(chunk) - 1
            request = urllib.request.Request(
                upload_url,
                data=chunk,
                headers={"Content-Type": "video/mp4", "Content-Length": str(len(chunk)), "Content-Range": f"bytes {start}-{end}/{size}"},
                method="PUT",
            )
            last_error: Exception | None = None
            for attempt in range(UPLOAD_ATTEMPTS):
                try:
                    with urllib.request.urlopen(request, timeout=120) as response:
                        if response.status not in (200, 201, 204):
                            raise TikTokError(f"Upload TikTok HTTP {response.status}.")
                    last_error = None
                    break
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", errors="replace")
                    last_error = TikTokError(f"Upload TikTok HTTP {exc.code}: {detail[:500]}")
                except urllib.error.URLError as exc:
                    last_error = TikTokError(f"Falha de rede no upload TikTok: {exc.reason}")
                if attempt < UPLOAD_ATTEMPTS - 1:
                    time.sleep(2**attempt)
            if last_error:
                raise last_error
            start = end + 1


def _status(token: str, publish_id: str) -> dict:
    result = _json_request(f"{API_ROOT}/post/publish/status/fetch/", token=token, body={"publish_id": publish_id})
    return result.get("data", {})


def _wait_for_publish(token: str, publish_id: str) -> tuple[str, dict]:
    latest: dict = {}
    for attempt in range(POLL_ATTEMPTS):
        latest = _status(token, publish_id)
        state = str(latest.get("status", "PROCESSING")).upper()
        if state in TERMINAL_STATUSES:
            return state, latest
        if attempt < POLL_ATTEMPTS - 1:
            time.sleep(POLL_SECONDS)
    return str(latest.get("status", "PROCESSING")).upper(), latest


def _post_clip(token: str, creator: dict, clip: dict, source: Path, on_initialized=None) -> dict:
    size = source.stat().st_size
    post_info = {
        "title": truncate_utf8(clip["copy"]["tiktok_caption"], 2200),
        "privacy_level": choose_privacy_level(creator),
        "disable_comment": bool(creator.get("comment_disabled", False)),
        "disable_duet": bool(creator.get("duet_disabled", False)),
        "disable_stitch": bool(creator.get("stitch_disabled", False)),
        "video_cover_timestamp_ms": 0,
        "is_aigc": False,
    }
    init = _json_request(
        f"{API_ROOT}/post/publish/video/init/",
        token=token,
        body={
            "post_info": post_info,
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": min(CHUNK_SIZE, size), "total_chunk_count": max(1, math.ceil(size / CHUNK_SIZE))},
        },
    )
    data = init.get("data", {})
    publish_id, upload_url = data.get("publish_id", ""), data.get("upload_url", "")
    if not publish_id or not upload_url:
        raise TikTokError("TikTok não retornou publish_id e upload_url.")
    if on_initialized:
        on_initialized(publish_id)
    _upload_file(upload_url, source)
    state, status_data = _wait_for_publish(token, publish_id)
    return {"publish_id": publish_id, "status": state, "status_data": status_data}


def _due_clips(manifest: dict, now: datetime | None = None) -> list[dict]:
    current = now or datetime.now(TIMEZONE)
    day = date.fromisoformat(manifest["date"])
    if current.date() != day:
        return []
    eligible = [
        clip
        for clip in manifest["clips"]
        if current >= datetime.combine(
            day,
            time(hour=int(clip["schedule"]["tiktok_hour"])),
            tzinfo=TIMEZONE,
        )
    ]
    return sorted(eligible, key=lambda item: (int(item["schedule"]["tiktok_hour"]), item["index"]))


def publish_tiktok(
    manifest: dict,
    dry_run: bool = False,
    due_only: bool = False,
    now: datetime | None = None,
    allow_immediate: bool = False,
) -> list[dict]:
    if not dry_run and not due_only and not allow_immediate and env("PUBLISHER_ALLOW_IMMEDIATE_TIKTOK") != "1":
        raise TikTokError(
            "Publicação imediata dos cinco TikToks está bloqueada. Use --due-only ou confirme explicitamente a execução imediata."
        )
    day = date.fromisoformat(manifest["date"])
    clips = _due_clips(manifest, now) if due_only else sorted(manifest["clips"], key=lambda item: item["index"])
    if dry_run:
        if due_only:
            clips = clips[:1]
        return [{"index": clip["index"], "status": "dry_run", "publish_at": local_publish_at(day, int(clip["schedule"]["tiktok_hour"])), "caption": truncate_utf8(clip["copy"]["tiktok_caption"], 2200)} for clip in clips]
    if due_only and not clips:
        return [{"status": "nothing_due"}]
    token, creator, drive = _refresh_access_token(), None, None
    creator = _creator_info(token)
    drive = drive_service()
    results: list[dict] = []
    for clip in clips:
        item = verify_manifest_clip(drive, manifest, clip)
        properties = item.get("appProperties", {})
        existing_id = properties.get("cf_tiktok_publish_id", "").strip()
        if existing_id:
            state, status_data = _wait_for_publish(token, existing_id)
            if state == "PUBLISH_COMPLETE":
                marker(drive, clip["drive_id"], {"cf_tiktok_status": state, "cf_tiktok_date": manifest["date"]})
                results.append({"index": clip["index"], "status": "already_published", "publish_id": existing_id})
                continue
            if state not in {"FAILED", "CANCELED"}:
                marker(drive, clip["drive_id"], {"cf_tiktok_status": state, "cf_tiktok_date": manifest["date"]})
                results.append({"index": clip["index"], "status": state, "publish_id": existing_id})
                continue
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_tiktok_last_publish_id": existing_id,
                    "cf_tiktok_publish_id": "",
                    "cf_tiktok_status": state,
                    "cf_tiktok_date": manifest["date"],
                },
            )
            raise TikTokError(f"TikTok falhou no publish_id {existing_id}: {status_data}")
        with tempfile.TemporaryDirectory(prefix="corte-fino-tiktok-") as temp_dir:
            source = Path(temp_dir) / f"{clip['index']:02d}.mp4"
            download(drive, clip["drive_id"], source)
            outcome = _post_clip(
                token,
                creator,
                clip,
                source,
                on_initialized=lambda publish_id: marker(
                    drive,
                    clip["drive_id"],
                    {
                        "cf_tiktok_publish_id": publish_id,
                        "cf_tiktok_status": "PENDING",
                        "cf_tiktok_date": manifest["date"],
                    },
                ),
            )
        if outcome["status"] in {"FAILED", "CANCELED"}:
            marker(
                drive,
                clip["drive_id"],
                {
                    "cf_tiktok_last_publish_id": outcome["publish_id"],
                    "cf_tiktok_publish_id": "",
                    "cf_tiktok_status": outcome["status"],
                    "cf_tiktok_date": manifest["date"],
                },
            )
            raise TikTokError(f"TikTok falhou no publish_id {outcome['publish_id']}: {outcome.get('status_data', {})}")
        marker(
            drive,
            clip["drive_id"],
            {
                "cf_tiktok_publish_id": outcome["publish_id"],
                "cf_tiktok_status": outcome["status"],
                "cf_tiktok_date": manifest["date"],
            },
        )
        results.append({"index": clip["index"], **outcome})
        if due_only:
            break
    return results
