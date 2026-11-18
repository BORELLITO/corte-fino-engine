"""One candidate, one real-public-footage physical QA; never mark release approval.
Only FFmpeg from a pinned pip wheel. No ffprobe, apt, model API or credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

SOURCE_ID = 19381590
SOURCE_URL = "https://www.pexels.com/video/carousel-19381590/"
SOURCE_FILE_URL = "https://videos.pexels.com/video-files/19381590/19381590-uhd_3840_2160_25fps.mp4"
SCENE_ID = "VNC-E01V2-S03"
SCENE_DURATION = 6.14
MAX_BYTES = 125_000_000


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_binary(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def probe_with_ffmpeg(binary: str, path: Path) -> dict:
    """A single bundled FFmpeg executable can inspect headers and decode frames."""
    result = run_binary([binary, "-nostdin", "-hide_banner", "-i", str(path)], timeout=20)
    output = result.stderr
    dur = re.search(r"Duration:\s*(\d\d):(\d\d):(\d\d(?:\.\d+)?)", output)
    line = next((x for x in output.splitlines() if "Video:" in x and "Stream #" in x), "")
    dim = re.search(r"(\d{3,5})x(\d{3,5})", line)
    fps = re.search(r"(\d+(?:\.\d+)?)\s+fps", line)
    if not (dur and dim and fps):
        raise ValueError("missing_or_unreadable_video_stream_headers")
    duration = 3600 * int(dur[1]) + 60 * int(dur[2]) + float(dur[3])
    width, height, framerate = int(dim[1]), int(dim[2]), float(fps[1])
    if not all(math.isfinite(x) for x in (duration, framerate)):
        raise ValueError("nonfinite_video_duration_or_fps")
    return {"duration_seconds": duration, "width": width, "height": height, "source_fps": framerate}


def source_to_vertical_crop(width: int, height: int) -> dict:
    """A center crop to 9:16, with no upscaling of inadequate source pixels."""
    proposed = int((height * 9 / 16) // 2 * 2)
    if proposed < 1080 or height < 1920 or proposed > width:
        raise ValueError("source_cannot_native_crop_9x16_at_1080x1920")
    return {
        "crop_width": proposed,
        "crop_height": height,
        "crop_left": (width - proposed) // 2,
        "crop_top": 0,
        "vertical_source_resolution_ok": True,
    }


def run(source: Path, out_dir: Path, ffmpeg_bin: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "project": "verbo-no-chao",
        "episode": "VNC-W01-E1",
        "scene": SCENE_ID,
        "required_scene_seconds": SCENE_DURATION,
        "source_provider": "Pexels",
        "source_video_id": SOURCE_ID,
        "source_page_url": SOURCE_URL,
        "source_original_url": SOURCE_FILE_URL,
        "source_description_at_research": "Deserted playground seesaw on a rainy night, evoking nostalgia",
        "physical_status": "BLOCKED",
        "editorial_visual_review": "PENDING_ACTUAL_FRAME_INSPECTION",
        "rights_review": "PENDING_PER_ASSET_AND_CONTEXT",
        "is_real_footage": None,
        "source_copyright_license_cleared": False,
        "editorial_approved": False,
        "commercial_use_approved": False,
        "allowed_in_master": False,
        "publication_authorized": False,
        "master_created": False,
        "ai_generation_requests": 0,
        "notes": "Video hash and technical decode do not establish historical truth, actor rights or biblical scene fitness.",
    }
    try:
        if not source.is_file():
            raise ValueError("source_file_missing_after_one_download")
        length = source.stat().st_size
        if length < 100000 or length > MAX_BYTES:
            raise ValueError("unexpected_source_size")
        report["source_bytes"] = length
        report["sha256"] = hash_file(source)
        meta = probe_with_ffmpeg(ffmpeg_bin, source)
        report["source_physical"] = meta
        if meta["duration_seconds"] < SCENE_DURATION:
            raise ValueError("source_video_shorter_than_scene")
        if meta["source_fps"] < 24:
            raise ValueError("source_fps_below_24")
        crop = source_to_vertical_crop(meta["width"], meta["height"])
        report["vertical_crop"] = crop
        # Full real-source video decode: exit-code only, not proof of semantic meaning.
        decoded = run_binary(
            [ffmpeg_bin, "-nostdin", "-hide_banner", "-v", "error", "-xerror",
             "-i", str(source), "-map", "0:v:0", "-f", "null", "-"], timeout=200,
        )
        if decoded.returncode:
            raise ValueError("whole_source_video_decode_failed:" + decoded.stderr[-120:])
        report["full_source_decoded"] = True

        vf = ("crop={crop_width}:{crop_height}:{crop_left}:{crop_top},"
              "fps=1,scale=270:480:flags=lanczos,tile=3x2").format(**crop)
        contact = out_dir / "S03_6_REAL_SOURCE_FRAMES_CONTACT.jpg"
        sampled = run_binary(
            [ffmpeg_bin, "-nostdin", "-y", "-hide_banner", "-v", "error",
             "-ss", "0", "-i", str(source), "-t", str(SCENE_DURATION),
             "-vf", vf, "-frames:v", "1", str(contact)], timeout=75,
        )
        if sampled.returncode or not contact.is_file():
            raise ValueError("contact_sheet_assembly_failed:" + sampled.stderr[-120:])
        preview = out_dir / "S03_VERTICAL_540x960_30FPS_QA_ONLY.mp4"
        proxy_vf = ("crop={crop_width}:{crop_height}:{crop_left}:{crop_top},"
                    "fps=30,scale=540:960:flags=lanczos").format(**crop)
        proxy = run_binary(
            [ffmpeg_bin, "-nostdin", "-y", "-hide_banner", "-v", "error",
             "-i", str(source), "-t", str(SCENE_DURATION), "-an",
             "-vf", proxy_vf, "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
             str(preview)], timeout=160,
        )
        if proxy.returncode or not preview.is_file():
            raise ValueError("technical_review_proxy_failed:" + proxy.stderr[-120:])
        report["review_assets"] = {
            "contact_sheet": {"name": contact.name, "sha256": hash_file(contact)},
            "proxy": {"name": preview.name, "sha256": hash_file(preview),
                      "is_master": False, "native_source_not_claimed_for_output": True},
        }
        report["physical_status"] = "PASS_PHYSICAL_SOURCE_NEEDS_DIRECTOR_FRAME_REVIEW"
        report["is_real_footage"] = True
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        report["physical_status"] = "BLOCKED"
        report["error"] = {"type": type(exc).__name__, "description": str(exc)[:300]}
    (out_dir / "S03_QA_PHYSICAL_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    import imageio_ffmpeg
    result = run(args.source, args.out, imageio_ffmpeg.get_ffmpeg_exe())
    print(json.dumps({"status": result["physical_status"],
                      "rights": result["source_copyright_license_cleared"],
                      "master": result["master_created"]}))
    return 0 if result["physical_status"].startswith("PASS_PHYSICAL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
