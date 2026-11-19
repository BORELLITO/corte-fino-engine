"""E01 S10 — genuine public stock *research* only, not an editorial release.

Only a single public Pexels video is downloaded by the separate one-shot workflow.
This module physically decodes original bytes and produces small review frames.
No source media enters git, no external model, no publication, no rights promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

PROJECT = "VERBO_NO_CHAO_EXCLUSIVO"
EPISODE = "VNC-W01-E1"
SCENE = "VNC-E01V2-S10"
SOURCE_ID = 9490306
SOURCE_PAGE = "https://www.pexels.com/video/a-woman-talking-to-her-friend-while-sitting-at-a-table-9490306/"
DOWNLOAD = "https://videos.pexels.com/video-files/9490306/9490306-uhd_2160_3840_25fps.mp4"
CREATOR = "Yaroslav Shuraev"
REQUIRED_SECONDS = 6.6
WINDOW_STARTS = (0.0, 8.0)
MAX_SIZE = 230_000_000


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def binary(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=timeout, check=False)


def audit(source: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": "1.0.0", "project_id": PROJECT,
        "episode_id": EPISODE, "scene_id": SCENE,
        "scene_timeline_seconds": [55.56, 62.16],
        "required_real_seconds": REQUIRED_SECONDS,
        "original_url": SOURCE_PAGE, "download_url": DOWNLOAD,
        "source_id": SOURCE_ID, "creator": CREATOR,
        "prior_source_status": "RESEARCH_ONLY",
        "source_claimed_by_public_page": "2160x3840, 25fps, around 17s; two women discussing studies indoors",
        "visual_risks": [
            "Visible or recognizable faces suggest real testimony",
            "Educational setting, documents or books differ from mutual support",
            "Prominent logos or written material in image",
            "Mutual listening and hands at table not visible simultaneously",
            "Low-key amber/charcoal ambience may not match"
        ],
        "physical_status": "NOT_VERIFIED",
        "full_original_decode_pass": False,
        "actual_frame_sampling_complete": False,
        "editorial_approved": False, "people_context_rights_cleared": False,
        "source_license_reviewed_for_scene": False,
        "allowed_in_master": False, "publication_authorized": False,
        "paid_generation_calls": 0, "raw_video_uploaded_to_repo": False,
    }
    try:
        if not source.is_file() or not (100000 < source.stat().st_size <= MAX_SIZE):
            raise ValueError("source_bytes_missing_or_out_of_bounds")
        result["source_sha256"] = sha(source)
        result["source_bytes"] = source.stat().st_size
        from portable_ffmpeg import get_ffmpeg
        ffmpeg, ffprobe = map(str, get_ffmpeg())
        p = binary(ffprobe, "-v", "error", "-show_entries",
                   "format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate",
                   "-of", "json", str(source), timeout=30)
        if p.returncode:
            raise ValueError("ffprobe_rejected_source")
        info = json.loads(p.stdout)
        v = next((s for s in info.get("streams", [])
                  if s.get("codec_type") == "video"), None)
        if not isinstance(v, dict):
            raise ValueError("source_missing_video_stream")
        width, height = v.get("width"), v.get("height")
        duration = float(info["format"]["duration"])
        n, d = (float(k) for k in v.get("avg_frame_rate", "0/1").split("/"))
        fps = n / d if d else 0
        result["source_video"] = {
            "width": width, "height": height,
            "duration_sec": duration, "native_fps": fps,
            "codec": v.get("codec_name"),
        }
        if type(width) is not int or type(height) is not int or width < 1080 or height < 1920:
            raise ValueError("insufficient_original_portrait_dimensions")
        if not math.isfinite(duration) or duration < max(x + REQUIRED_SECONDS for x in WINDOW_STARTS):
            raise ValueError("not_enough_unlooped_video_for_both_review_windows")
        if not math.isfinite(fps) or fps < 24:
            raise ValueError("original_fps_below_24")
        decode = binary(ffmpeg, "-nostdin", "-hide_banner", "-v", "error",
                        "-xerror", "-i", str(source), "-map", "0:v:0",
                        "-f", "null", "-", timeout=180)
        if decode.returncode:
            raise ValueError("full_original_video_decode_failed")
        result["full_original_decode_pass"] = True

        sheets = []
        for index, start in enumerate(WINDOW_STARTS, 1):
            name = f"S10_REAL_SOURCE_FRAMES_WINDOW_{index}.jpg"
            image = out / name
            res = binary(
                ffmpeg, "-nostdin", "-y", "-v", "error", "-ss", str(start),
                "-i", str(source), "-t", str(REQUIRED_SECONDS),
                "-vf", "fps=1,scale=270:480:flags=lanczos,tile=3x3",
                "-frames:v", "1", str(image), timeout=90,
            )
            if res.returncode or not image.is_file() or image.stat().st_size < 1500:
                raise ValueError(f"source_contact_sheet_{index}_failed")
            sheets.append({"file": name, "sha256": sha(image),
                           "start": start, "end": start + REQUIRED_SECONDS,
                           "frames_transformed_for_contact_sheet": True})

        # Alternative lower-half framing: see hands and tabletop without implying
        # recognizable people endorsing the story. This is not a source replacement.
        crop_y = min(max(0, int(height * 0.40)), height - 1920)
        crop_x = (width - 1080) // 2
        alt = out / "S10_LOWER_BODY_NATIVE_CROP_REVIEW.jpg"
        vf = (f"crop=1080:1920:{crop_x}:{crop_y},fps=1,"
              "scale=270:480:flags=lanczos,tile=3x3")
        crop = binary(ffmpeg, "-nostdin", "-y", "-v", "error", "-i", str(source),
                      "-t", str(REQUIRED_SECONDS), "-vf", vf,
                      "-frames:v", "1", str(alt), timeout=90)
        if crop.returncode or not alt.is_file() or alt.stat().st_size < 1500:
            raise ValueError("native_vertical_lower_body_review_failed")
        result["portrait_no_upscale_crop"] = {
            "x": crop_x, "y": crop_y, "width": 1080, "height": 1920,
            "review_file": alt.name, "review_sha256": sha(alt),
            "do_not_assume_faces_absent_without_review": True,
        }
        result["contact_sheets"] = sheets
        result["actual_frame_sampling_complete"] = True
        result["physical_status"] = "PASS_REAL_STOCK_SOURCE_EDITS_AND_RIGHTS_NOT_APPROVED"
    except (OSError, ValueError, KeyError, TypeError, ImportError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        result["physical_status"] = "BLOCKED_REAL_SOURCE_OR_MEDIA"
        result["error_type"] = type(exc).__name__
        result["error_reason"] = str(exc)[:240]

    (out / "S10_9490306_PHYSICAL_QA.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    opt = parser.parse_args()
    report = audit(opt.source, opt.out)
    print(json.dumps({"status": report["physical_status"],
                      "source_sha256": report.get("source_sha256"),
                      "editorial_approved": False,
                      "allowed_in_master": False,
                      "publication_authorized": False}))
    return 0 if report["physical_status"].startswith("PASS_REAL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
