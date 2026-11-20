"""Footage stage: licensed sources only, each clip used at most once per video."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .common import ProducerError, decodes_cleanly, duration_sec, sha256_file
from media.probe import probe_media


@dataclass(frozen=True)
class Clip:
    asset_id: str
    path: Path
    source_url: str
    license_url: str
    license_name: str


class FootageProvider(Protocol):
    def fetch(self, query: str, min_seconds: float, exclude: set[str], dst_dir: Path) -> Clip: ...


def validate_clip(clip: Clip, min_seconds: float) -> None:
    if not clip.path.is_file() or not decodes_cleanly(clip.path):
        raise ProducerError(f"producer:footage:not_decodable:{clip.asset_id}")
    video = next((s for s in probe_media(clip.path).get("streams", [])
                  if s.get("codec_type") == "video"), None)
    if video is None:
        raise ProducerError(f"producer:footage:no_video_stream:{clip.asset_id}")
    if duration_sec(clip.path) + 0.03 < min_seconds:
        raise ProducerError(f"producer:footage:too_short_no_loops:{clip.asset_id}")


class LocalCatalogFootage:
    """Pre-curated clips described by catalog.json: [{asset_id,file,source_url,license_url,license_name,tags}]."""

    def __init__(self, catalog_dir: Path) -> None:
        self.dir = catalog_dir
        try:
            self.items = json.loads((catalog_dir / "catalog.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProducerError("producer:footage:catalog_unreadable") from exc

    def fetch(self, query, min_seconds, exclude, dst_dir):
        words = set(query.casefold().split())
        ranked = sorted(self.items, key=lambda i: -len(words & {t.casefold() for t in i.get("tags", [])}))
        for item in ranked:
            hash_id = sha256_file(self.dir / item["file"])
            if item["asset_id"] in exclude or item["source_url"] in exclude or hash_id in exclude:
                continue
            clip = Clip(item["asset_id"], self.dir / item["file"], item["source_url"],
                        item["license_url"], item["license_name"])
            try:
                validate_clip(clip, min_seconds)
            except ProducerError:
                continue
            return clip
        raise ProducerError(f"producer:footage:no_unused_clip_for:{query}")


class PexelsFootage:
    """Pexels Videos API (free license). Needs PEXELS_API_KEY; without it the run stays BLOCKED."""

    API = "https://api.pexels.com/videos/search"
    LICENSE_URL = "https://www.pexels.com/license/"

    def __init__(self, api_key: str | None = None) -> None:
        self.key = api_key or os.environ.get("PEXELS_API_KEY", "")
        if not self.key:
            raise ProducerError("producer:footage:pexels_api_key_missing")

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"Authorization": self.key,
                                                   "User-Agent": "verbo-no-chao-producer"})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https hosts)
            return resp.read()

    def fetch(self, query, min_seconds, exclude, dst_dir):
        qs = urllib.parse.urlencode({"query": query, "orientation": "portrait", "per_page": 15})
        try:
            videos = json.loads(self._get(f"{self.API}?{qs}")).get("videos", [])
        except Exception as exc:
            raise ProducerError(f"producer:footage:pexels_search_failed:{type(exc).__name__}") from exc
        for video in videos:
            asset_id = f"pexels-{video['id']}"
            if asset_id in exclude or video["url"] in exclude or video.get("duration", 0) < min_seconds + 0.5:
                continue
            files = [f for f in video.get("video_files", [])
                     if (f.get("width") or 0) >= 1080 and (f.get("height") or 0) >= 1920
                     and str(f.get("link", "")).startswith("https://")]
            if not files:
                continue
            pick = min(files, key=lambda f: f["width"] * f["height"])
            dst = dst_dir / f"{asset_id}.mp4"
            try:
                dst.write_bytes(self._get(pick["link"]))
            except Exception as exc:
                raise ProducerError(f"producer:footage:download_failed:{asset_id}") from exc
            if sha256_file(dst) in exclude:
                dst.unlink()
                continue
            clip = Clip(asset_id, dst, video["url"], self.LICENSE_URL, "Pexels License")
            try:
                validate_clip(clip, min_seconds)
            except ProducerError:
                dst.unlink(missing_ok=True)
                continue
            return clip
        raise ProducerError(f"producer:footage:no_unused_clip_for:{query}")


class PixabayFootage:
    """Pixabay Videos API (Pixabay Content License). Needs PIXABAY_API_KEY; without it the run stays BLOCKED.

    Pixabay has no portrait filter, so only native 1080x1920+ files are accepted (no upscaled crops).
    """

    API = "https://pixabay.com/api/videos/"
    LICENSE_URL = "https://pixabay.com/service/license-summary/"

    def __init__(self, api_key: str | None = None) -> None:
        self.key = api_key or os.environ.get("PIXABAY_API_KEY", "")
        if not self.key:
            raise ProducerError("producer:footage:pixabay_api_key_missing")

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "verbo-no-chao-producer"})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https hosts)
            return resp.read()

    def fetch(self, query, min_seconds, exclude, dst_dir):
        hits: list = []
        for page in (1, 2, 3):  # portrait-native files are rare: look deeper before giving up
            qs = urllib.parse.urlencode({"key": self.key, "q": query, "per_page": 50,
                                         "safesearch": "true", "page": page})
            try:
                batch = json.loads(self._get(f"{self.API}?{qs}")).get("hits", [])
            except Exception as exc:
                raise ProducerError(f"producer:footage:pixabay_search_failed:{type(exc).__name__}") from exc
            hits.extend(batch)
            if len(batch) < 50:
                break
        for hit in hits:
            asset_id = f"pixabay-{hit['id']}"
            if asset_id in exclude or hit.get("pageURL") in exclude or hit.get("duration", 0) < min_seconds + 0.5:
                continue
            files = [f for f in (hit.get("videos") or {}).values()
                     if (f.get("width") or 0) >= 1080 and (f.get("height") or 0) >= 1920
                     and str(f.get("url", "")).startswith("https://")]
            if not files:
                continue
            pick = min(files, key=lambda f: f["width"] * f["height"])
            dst = dst_dir / f"{asset_id}.mp4"
            try:
                dst.write_bytes(self._get(pick["url"]))
            except Exception as exc:
                raise ProducerError(f"producer:footage:download_failed:{asset_id}") from exc
            if sha256_file(dst) in exclude:
                dst.unlink()
                continue
            clip = Clip(asset_id, dst, hit["pageURL"], self.LICENSE_URL, "Pixabay Content License")
            try:
                validate_clip(clip, min_seconds)
            except ProducerError:
                dst.unlink(missing_ok=True)
                continue
            return clip
        raise ProducerError(f"producer:footage:no_unused_clip_for:{query}")


class ChainFootage:
    """Try several providers in order; each scene may offer several queries (broad -> narrow fallbacks)."""

    def __init__(self, providers: list) -> None:
        if not providers:
            raise ProducerError("producer:footage:empty_chain")
        self.providers = providers

    def fetch(self, query, min_seconds, exclude, dst_dir):
        queries = [query] if isinstance(query, str) else list(query)
        last: ProducerError | None = None
        for provider in self.providers:
            for q in queries:
                try:
                    return provider.fetch(q, min_seconds, exclude, dst_dir)
                except ProducerError as exc:
                    if "no_unused_clip_for" not in str(exc):
                        raise  # real failures (auth, network, corrupt) must not be hidden by fallbacks
                    last = exc
        raise ProducerError(f"producer:footage:no_unused_clip_for_any_query:{queries}") from last
