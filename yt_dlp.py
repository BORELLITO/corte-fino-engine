from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


class YoutubeDL:
    """Small yt-dlp-compatible adapter for public Piped streams."""

    def __init__(self, opts=None):
        self.opts = opts or {}
        self.info = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def _apis(self):
        configured = os.environ.get("PIPED_API_URL", "").strip()
        values = [configured] if configured else []
        values += [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.leptons.xyz",
            "https://pipedapi.nosebs.ru",
        ]
        return list(dict.fromkeys(x.rstrip("/") for x in values if x))

    def _json(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)

    def _video_id(self, url):
        match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{6,})", url)
        if not match:
            raise ValueError("Não consegui identificar o ID do vídeo YouTube.")
        return match.group(1)

    def _search(self, query):
        query = re.sub(r"^ytsearch(?:date)?\d*:", "", query)
        for api in self._apis():
            try:
                data = self._json(api + "/search?" + urllib.parse.urlencode({"q": query, "filter": "videos"}))
                entries = []
                for item in data.get("items", [])[:8]:
                    video_id = item.get("url", "").split("v=")[-1]
                    if video_id:
                        entries.append({
                            "id": video_id,
                            "title": item.get("title"),
                            "webpage_url": "https://www.youtube.com/watch?v=" + video_id,
                            "duration": item.get("duration"),
                            "view_count": item.get("views"),
                        })
                if entries:
                    return {"entries": entries}
            except Exception as exc:
                print(f"Busca Piped falhou em {api}: {exc}")
        return {"entries": []}

    def extract_info(self, url, download=False):
        if url.startswith("ytsearch"):
            return self._search(url)
        video_id = self._video_id(url)
        data = None
        last_error = None
        for api in self._apis():
            try:
                data = self._json(f"{api}/streams/{video_id}")
                if data and (data.get("videoStreams") or data.get("dash")):
                    break
            except Exception as exc:
                last_error = exc
        if not data or not (data.get("videoStreams") or data.get("dash")):
            raise RuntimeError(f"Piped não retornou os streams ({last_error}).")
        info = {
            "id": video_id,
            "title": data.get("title") or video_id,
            "uploader": data.get("uploader"),
            "channel": data.get("uploader"),
            "duration": data.get("duration"),
            "view_count": data.get("views"),
            "webpage_url": url,
            "_piped": data,
        }
        self.info = info
        if download:
            self._download(info)
        return info

    def prepare_filename(self, info):
        template = self.opts.get("outtmpl", "source.%(ext)s")
        return template.replace("%(ext)s", "mp4").replace("%(id)s", info.get("id", "source"))

    def _save(self, url, path):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)

    def _download(self, info):
        data = info["_piped"]
        target = Path(self.prepare_filename(info)).with_suffix(".mp4")
        target.parent.mkdir(parents=True, exist_ok=True)
        videos = [s for s in data.get("videoStreams", []) if s.get("url") and not s.get("videoOnly")]
        videos = [s for s in videos if not s.get("height") or s.get("height") <= 720] or videos
        if videos:
            stream = max(videos, key=lambda s: s.get("height") or 0)
            temporary = target.with_suffix(".download")
            self._save(stream["url"], temporary)
            subprocess.run(["ffmpeg", "-y", "-i", str(temporary), "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(target)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            temporary.unlink(missing_ok=True)
            return
        video = [s for s in data.get("videoStreams", []) if s.get("url")]
        audio = [s for s in data.get("audioStreams", []) if s.get("url")]
        if not video or not audio:
            raise RuntimeError("Piped não forneceu stream de vídeo e áudio utilizáveis.")
        work = target.with_suffix(".parts")
        work.mkdir(exist_ok=True)
        video_path, audio_path = work / "video", work / "audio"
        self._save(max(video, key=lambda s: s.get("height") or 0)["url"], video_path)
        self._save(max(audio, key=lambda s: s.get("bitrate") or 0)["url"], audio_path)
        subprocess.run(["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path), "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(target)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        shutil.rmtree(work, ignore_errors=True)
