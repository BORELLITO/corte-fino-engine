"""Fail-closed Pexels stock intake for VNC E01 v2; never a publication gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path("contracts/e01_v2_stock_candidates_v1.json")
STORYBOARD = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
ALLOWED_STATES = {"PENDING_FRAME_REVIEW"}
MAX_BYTES = 140 * 1024 * 1024

class StockIntakeError(ValueError):
    pass

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise StockIntakeError(reason)

def _https_url(url: str, host: str) -> bool:
    try:
        parsed = urlparse(url)
        return (parsed.scheme == "https" and parsed.hostname == host
                and parsed.port is None and parsed.username is None
                and parsed.password is None and not parsed.params
                and not parsed.query and not parsed.fragment)
    except ValueError:
        return False

def validate(root: Path = ROOT, data: dict | None = None) -> dict:
    if data is None:
        data = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    require(isinstance(data, dict), "contract:not_object")
    require(data.get("schema_version") == "1.0.0"
            and data.get("project") == "verbo-no-chao"
            and data.get("episode_id") == "VNC-W01-E1"
            and data.get("candidate_version") == 2,
            "contract:wrong_project_or_version")
    require(data.get("source_storyboard") == str(STORYBOARD),
            "contract:wrong_storyboard")
    require(data.get("status") == "PAGE_METADATA_CURATED_FILES_NOT_ACQUIRED"
            and data.get("full_media_integrity_confirmed") is False
            and data.get("footage_approved_for_edit") is False
            and data.get("final_master_available") is False
            and data.get("publication_authorized") is False,
            "contract:fake_approval")
    storyboard = json.loads((root / STORYBOARD).read_text(encoding="utf-8"))
    require(data.get("source_voice_sha256") == storyboard["audio_sha256"]
            and data.get("source_caption_ass_sha256")
                == "0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a",
            "contract:source_audio_caption_mismatch")
    scenes = {s["id"]: s for s in storyboard["scenes"]}
    items = data.get("candidates")
    require(isinstance(items, list) and 1 <= len(items) <= 12,
            "contract:invalid_candidate_count")
    seen_assets, seen_videos, seen_scenes = set(), set(), set()
    for item in items:
        require(isinstance(item, dict), "candidate:not_object")
        ident = item.get("id")
        scene_id = item.get("scene_id")
        video_id = item.get("video_id")
        require(isinstance(ident, str) and re.fullmatch(r"E01V2-STOCK-S\d{2}-[A-Z]", ident),
                "candidate:invalid_asset_id")
        require(ident not in seen_assets and scene_id in scenes
                and scene_id not in seen_scenes,
                "candidate:duplicate_or_unknown_scene")
        require(isinstance(video_id, int) and video_id > 0
                and video_id not in seen_videos,
                "candidate:duplicate_or_invalid_video")
        seen_assets.add(ident)
        seen_scenes.add(scene_id)
        seen_videos.add(video_id)
        page = item.get("page_url")
        file_url = item.get("download_url")
        require(isinstance(page, str) and _https_url(page, "www.pexels.com")
                and re.fullmatch(r"/video/[a-z0-9-]+-" + str(video_id) + r"/",
                                 urlparse(page).path),
                "candidate:untrusted_page")
        require(isinstance(file_url, str)
                and _https_url(file_url, "videos.pexels.com")
                and re.fullmatch(r"/video-files/" + str(video_id)
                                 + r"/[0-9a-zA-Z_-]+\.mp4",
                                 urlparse(file_url).path),
                "candidate:untrusted_download_host_or_id")
        require(item.get("page_metadata_verified") is True
                and item.get("download_redirect_observed") is True
                and item.get("download_performed") is False
                and item.get("physical_sha256") is None
                and item.get("physical_probe") is None
                and item.get("editorial_status") in ALLOWED_STATES
                and item.get("third_party_rights") == "PENDING_REVIEW"
                and item.get("commercial_publication_cleared") is False,
                "candidate:unearned_media_or_rights_approval")
        require(item.get("source_license_name") == "Pexels License"
                and item.get("source_license_url") == "https://www.pexels.com/license/"
                and isinstance(item.get("creator"), str)
                and len(item["creator"]) >= 2
                and isinstance(item.get("risk"), str)
                and len(item["risk"]) > 10,
                "candidate:incomplete_provenance_or_risk")
        width, height = item.get("width"), item.get("height")
        dur, fps = item.get("page_duration_seconds"), item.get("fps")
        scene = scenes[scene_id]
        require(isinstance(width, int) and isinstance(height, int)
                and width >= 1080 and height >= 1920
                and width * 16 == height * 9
                and isinstance(dur, (int, float)) and dur >=
                scene["end_seconds"] - scene["start_seconds"]
                and isinstance(fps, (int, float)) and fps >= 23,
                "candidate:incompatible_geometry_duration_or_fps")
    return {"status": "METADATA_VALID_RIGHTS_PENDING",
            "candidate_count": len(items),
            "source_media_bytes_verified": 0,
            "ready_for_final_master": False,
            "publication_authorized": False}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise StockIntakeError("probe:unexpected_redirect")

def probe_item(item: dict, temp: Path, ffprobe: str, ffmpeg: str) -> dict:
    url = item["download_url"]
    require(_https_url(url, "videos.pexels.com"),
            "probe:untrusted_host")
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={
        "User-Agent": "VerboNoChao-Research-Intake/1.0"})
    dest = temp / (item["id"] + ".mp4")
    digest = hashlib.sha256()
    count = 0
    with opener.open(req, timeout=35) as response:
        require(response.status == 200, "probe:http_status")
        content_type = response.headers.get("Content-Type", "").lower()
        require("video/" in content_type or "octet-stream" in content_type,
                "probe:wrong_content_type")
        declared_size = response.headers.get("Content-Length")
        if declared_size is not None:
            require(int(declared_size) <= MAX_BYTES, "probe:file_too_large")
        with dest.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                require(count <= MAX_BYTES, "probe:file_too_large")
                digest.update(chunk)
                output.write(chunk)
    require(count >= 100000, "probe:not_real_media_bytes")
    process = subprocess.run([ffprobe, "-v", "error",
        "-select_streams", "v:0", "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate:format=duration",
        "-of", "json", str(dest)], capture_output=True, text=True,
        timeout=60, check=False)
    require(process.returncode == 0, "probe:ffprobe_failed")
    info = json.loads(process.stdout)
    streams = info.get("streams") or []
    require(len(streams) == 1, "probe:no_video_stream")
    stream = streams[0]
    duration = float(info.get("format", {}).get("duration", 0))
    needed = float(item["page_duration_seconds"])
    require(int(stream["width"]) >= 1080
            and int(stream["height"]) >= 1920
            and int(stream["width"]) * 16 == int(stream["height"]) * 9
            and duration >= needed - 1.5,
            "probe:physical_media_does_not_meet_page_metadata")
    decoded = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-xerror",
        "-i", str(dest), "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True, timeout=190, check=False)
    require(decoded.returncode == 0, "probe:full_video_decode_failed")
    # No raw MP4 or frames leave the temporary runner directory.
    return {"id": item["id"], "video_id": item["video_id"],
            "scene_id": item["scene_id"], "sha256": digest.hexdigest(),
            "size_bytes": count, "width": stream["width"],
            "height": stream["height"],
            "codec": stream.get("codec_name"), "duration_seconds": duration,
            "physical_full_video_decode": True,
            "visual_frame_review_complete": False,
            "third_party_rights_cleared": False}

def run_probe(root: Path, ffprobe: str, ffmpeg: str) -> dict:
    result = validate(root)
    data = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    result.update(status="PROBE_IN_PROGRESS_NOT_RELEASED", observations=[])
    with tempfile.TemporaryDirectory(prefix="vnc_stock_provisional_") as folder:
        for item in data["candidates"]:
            try:
                result["observations"].append(probe_item(item, Path(folder),
                                                        ffprobe, ffmpeg))
            except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired,
                    urllib.error.URLError) as error:
                result.update(status="BLOCKED_PROBE_INCOMPLETE",
                    failed_candidate=item["id"], failure_reason=type(error).__name__)
                break
    if len(result["observations"]) == result["candidate_count"]:
        result["status"] = "PHYSICAL_PROBE_COMPLETE_EDITORIAL_RIGHTS_PENDING"
        result["source_media_bytes_verified"] = len(result["observations"])
    result["files_persisted_for_master"] = False
    result["visual_frame_review_complete"] = False
    result["ready_for_final_master"] = False
    result["publication_authorized"] = False
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = (run_probe(args.root, args.ffprobe, args.ffmpeg)
                  if args.probe else validate(args.root))
        status = 0 if not report["status"].startswith("BLOCKED") else 2
    except (StockIntakeError, OSError, KeyError, TypeError,
            json.JSONDecodeError) as error:
        report = {"status": "BLOCKED_CONTRACT_INVALID",
                  "failure_reason": type(error).__name__,
                  "ready_for_final_master": False,
                  "publication_authorized": False}
        status = 2
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output)
    return status

if __name__ == "__main__":
    raise SystemExit(main())
