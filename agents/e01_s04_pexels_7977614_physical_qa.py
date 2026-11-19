"""S04 public film (Pexels 7977614) *physical* review, NOT final master.

Only known public Pexels source bytes are examined. No private assets, no GPU,
no authentication, no claims of biblical authenticity or cleared commercial rights.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

VIDEO_ID = 7977614
PAGE = "https://www.pexels.com/video/person-using-a-quill-7977614/"
DOWNLOAD = "https://videos.pexels.com/video-files/7977614/7977614-hd_1080_1920_30fps.mp4"
REQUIRED_SECONDS = 5.82
SCENE = "VNC-E01V2-S04"

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def execute(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True,
                          check=False, timeout=timeout)

def analyze(source: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "1.0.0", "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1", "scene_id": SCENE,
        "source_id": VIDEO_ID, "source_page": PAGE, "source_download_url": DOWNLOAD,
        "source_creator": "RDNE Stock project (Pexels)",
        "candidate_risk": "Source tagged witchcraft: reject if visible occult objects, spellbook, legible text or non-reed quill.",
        "canonical_seconds": REQUIRED_SECONDS,
        "technical_status": "BLOCKED_NOT_PHYSICALLY_VERIFIED",
        "full_source_video_decoded": False, "editorial_approved": False,
        "commercial_rights_cleared": False, "allowed_in_master": False,
        "publication_authorized": False, "provider_generation_requests": 0,
        "assessment_scope": "Technical inspection and two sets of real frames, NOT visual signoff.",
    }
    try:
        if not source.is_file() or not 100000 < source.stat().st_size <= 160000000:
            raise ValueError("missing_or_unexpected_source_size")
        report["source_bytes"] = source.stat().st_size
        report["source_sha256"] = digest(source)
        from portable_ffmpeg import get_ffmpeg
        ffmpeg, ffprobe = get_ffmpeg()
        probe = execute([str(ffprobe), "-v", "error", "-show_entries",
                         "format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate",
                         "-of", "json", str(source)], timeout=30)
        if probe.returncode: raise ValueError("ffprobe_failed")
        streams = json.loads(probe.stdout)
        video = next((v for v in streams.get("streams", [])
                      if v.get("codec_type") == "video"), None)
        if not video: raise ValueError("video_stream_missing")
        duration = float(streams["format"]["duration"])
        ratio = video.get("avg_frame_rate", "0/1")
        num, den = (float(k) for k in ratio.split("/"))
        fps = num / den if den else 0.
        width, height = video.get("width"), video.get("height")
        report["physical"] = {"duration_seconds": duration, "width": width, "height": height,
                              "fps": fps, "codec": video.get("codec_name")}
        if not math.isfinite(duration) or duration < 2 * REQUIRED_SECONDS:
            raise ValueError("cannot_inspect_two_nonlooped_windows")
        if type(width) is not int or type(height) is not int or width < 1080 or height < 1920:
            raise ValueError("native_source_below_portrait_resolution")
        if not math.isfinite(fps) or fps < 24:
            raise ValueError("source_fps_below_24")
        dec = execute([str(ffmpeg), "-nostdin", "-v", "error", "-xerror", "-i", str(source),
                       "-map", "0:v:0", "-f", "null", "-"], timeout=150)
        if dec.returncode: raise ValueError("entire_source_video_decode_failed")
        report["full_source_video_decoded"] = True
        sheets = []
        for i, start in enumerate((0, REQUIRED_SECONDS)):
            sheet = out / f"S04_REAL_FRAMES_WINDOW_{i+1}.jpg"
            frames = execute([str(ffmpeg), "-nostdin", "-y", "-v", "error",
                              "-ss", str(start), "-i", str(source), "-t", "5.82",
                              "-vf", "fps=1,scale=270:480:flags=lanczos,tile=3x2",
                              "-frames:v", "1", str(sheet)], timeout=75)
            if frames.returncode or not sheet.is_file() or sheet.stat().st_size < 2000:
                raise ValueError(f"frame_grid_window_{i+1}_failed")
            sheets.append({"file": sheet.name, "sha256": digest(sheet),
                           "start_seconds": start, "end_seconds": start + REQUIRED_SECONDS,
                           "is_original_unchanged": False})
        report["actual_frame_sampling"] = sheets
        report["technical_status"] = "PASS_SOURCE_PHYSICALLY_VALID_EDITORIAL_REVIEW_REQUIRED"
    except (OSError, ValueError, TypeError, KeyError, TimeoutError,
            subprocess.TimeoutExpired, ImportError) as e:
        report["technical_status"] = "BLOCKED_SOURCE_OR_DECODE"
        report["error_type"] = type(e).__name__
        report["error_message"] = str(e)[:220]
    (out / "S04_PHYSICAL_QA_ONLY.json").write_text(json.dumps(report, ensure_ascii=False,
                                         indent=2) + "\n", encoding="utf-8")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("out", type=Path)
    opts = parser.parse_args()
    r = analyze(opts.video, opts.out)
    print(json.dumps({"technical_status": r["technical_status"], "source_sha256": r.get("source_sha256"),
                      "editorial_approved": False, "can_enter_master": False}))
    raise SystemExit(0 if r["technical_status"].startswith("PASS_SOURCE") else 2)
