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
from publisher.google_io import download, drive_service, env, marker


API_ROOT = "https://open.tiktokapis.com/v2"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
CHUNK_SIZE = 10 * 1024 * 1024
POLL_SECONDS = 5
POLL_ATTEMPTS = 24


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
    return token


def _creator_info(token: str) -> dict:
    result = _json_request(f"{API_ROOT}/post/publish/creator_info/query/", token=token)
    data = result.get("data", {})
    if not data.get("privacy_level_options"):
        raise TikTokError("A conta TikTok não retornou opções de privacidade para publicação.")
    return data


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
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    if response.status not in (200, 201, 204):
                        raise TikTokError(f"Upload TikTok HTTP {response.status}.")
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise TikTokError(f"Upload TikTok HTTP {exc.code}: {detail[:500]}") from exc
            start = end + 1


def _status(token: str, publish_id: str) -> dict:
    result = _json_request(f"{API_ROOT}/post/publish/status/fetch/", token=token, body={"publish_id": publish_id})
    return result.get("data", {})


def _post_clip(token: str, creator: dict, clip: dict, source: Path) -> dict:
    size = source.stat().st_size
    post_info = {
        "title": truncate_utf8(clip["copy"]["tiktok_caption"], 2200),
        "privacy_level": creator["privacy_level_options"][0],
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
    _upload_file(upload_url, source)
    final_status = {}
    for _ in range(POLL_ATTEMPTS):
        final_status = _status(token, publish_id)
        state = final_status.get("status", "").upper()
        if state in {"PUBLISH_COMPLETE", "FAILED", "CANCELED"}:
            break
        time.sleep(POLL_SECONDS)
    state = final_status.get("status", "PROCESSING")
    if state.upper() in {"FAILED", "CANCELED"}:
        raise TikTokError(f"TikTok falhou no publish_id {publish_id}: {final_status}")
    return {"publish_id": publish_id, "status": state}


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


def publish_tiktok(manifest: dict, dry_run: bool = False, due_only: bool = False, now: datetime | None = None) -> list[dict]:
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
        item = drive.files().get(fileId=clip["drive_id"], fields="id,name,appProperties").execute(num_retries=4)
        properties = item.get("appProperties", {})
        if properties.get("cf_tiktok_publish_id"):
            results.append({"index": clip["index"], "status": "already_published", "publish_id": properties["cf_tiktok_publish_id"]})
            continue
        with tempfile.TemporaryDirectory(prefix="corte-fino-tiktok-") as temp_dir:
            source = Path(temp_dir) / f"{clip['index']:02d}.mp4"
            download(drive, clip["drive_id"], source)
            outcome = _post_clip(token, creator, clip, source)
        marker(drive, clip["drive_id"], {"cf_tiktok_publish_id": outcome["publish_id"], "cf_tiktok_status": outcome["status"], "cf_tiktok_date": manifest["date"]})
        results.append({"index": clip["index"], **outcome})
        if due_only:
            break
    return results
