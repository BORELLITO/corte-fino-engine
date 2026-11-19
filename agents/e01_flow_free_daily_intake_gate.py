"""VERBO NO CHÃO — offline local QA for Google Flow 12-shot zero-cash acquisition.

No Google Flow browser automation, no unofficial APIs, no billing or account
access, no auto-download, no uploading private media into public GitHub.
Run locally on already obtained MP4s. The output is technical QA only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

from agents.e01_stock_candidates import ROOT

CONTRACT = Path("contracts/e01_flow_free_daily_50_video_production_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
SCENE_IDS = tuple(f"VNC-E01V2-S{i:02d}" for i in range(1, 13))
VALID_VIDEO_SECONDS = (4, 6, 8)
VALID_DAYS = (1, 2, 3)


class IntakeRejected(ValueError):
    """Fail-closed source contract violation."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise IntakeRejected("not_an_object")
    return value


def verified_manifest(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    plan = _load(root / CONTRACT)
    source = _load(root / STORY)
    if not (
        plan.get("schema_version") == "1.0.0"
        and plan.get("project") == "VERBO_NO_CHAO_EXCLUSIVO"
        and plan.get("episode_id") == "VNC-W01-E1"
        and plan.get("source_storyboard") == str(STORY)
        and plan.get("source_script_sha256") == source.get("script_sha256")
        and plan.get("source_audio_sha256") == source.get("audio_sha256")
        and plan.get("source_28_captions_locked") is True
        and plan.get("target_duration_seconds") == source.get("duration_seconds")
        and plan.get("strategy") == "FLOW_FREE_DAILY_BATCH_WITH_HUMAN_AUTH_AND_PRIVATE_DRIVE_INTAKE"
        and plan.get("status") == "READY_FOR_USER_ACCOUNT_PREFLIGHT_NO_CLIP_CREATED"
        and plan.get("regular_user_free_daily_credits_officially_advertised") == 50
        and plan.get("per_scene_credits_officially_advertised") == 10
        and plan.get("total_scenes") == 12
        and plan.get("total_credits_nominal") == 120
        and plan.get("minimum_daily_cycles_if_no_rejections") == 3
        and plan.get("room_a_reference_frames_generated") is False
        and plan.get("room_a_free_image_entitlement_verified") is False
        and isinstance(plan.get("room_a_consistency_strategy"), str)
        and "S01" in plan["room_a_consistency_strategy"]
        and plan.get("direct_flow_api_connection_available") is False
        and plan.get("live_user_account_entitlement_verified") is False
        and plan.get("automated_browser_credentials_or_unofficial_api_permitted") is False
        and plan.get("publication_authorized") is False
        and plan.get("master_allowed") is False
        and plan.get("rights_cleared") is False
        and source.get("publication_authorized") is False
        and source.get("master_rendered") is False
    ):
        raise IntakeRejected("source_or_fiscal_or_safety_contract_modified")
    scenes = plan.get("scenes")
    source_scenes = source.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 12 or not isinstance(source_scenes, list) or len(source_scenes) != 12:
        raise IntakeRejected("scene_count_invalid")
    by_day = {day: 0 for day in VALID_DAYS}
    names = set()
    for i, (clip, original) in enumerate(zip(scenes, source_scenes)):
        start, end = original.get("start_seconds"), original.get("end_seconds")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            raise IntakeRejected("source_timeline_invalid")
        length = round(end - start, 3)
        expected_filename = f"VNC-E01-S{i+1:02d}-FLOW-CANDIDATE.mp4"
        if not (
            clip.get("scene_id") == original.get("id") == SCENE_IDS[i]
            and clip.get("title") == original.get("title")
            and clip.get("start_seconds") == start
            and clip.get("end_seconds") == end
            and clip.get("source_duration_seconds") == length
            and clip.get("requested_video_seconds") in VALID_VIDEO_SECONDS
            and clip["requested_video_seconds"] >= length
            and clip.get("requested_resolution") == "720p"
            and clip.get("requested_aspect_ratio") == "9:16"
            and clip.get("flow_model") == "Veo 3.1 Lite"
            and clip.get("generate_n") == 1
            and clip.get("credits_estimate") == 10
            and clip.get("suggested_day") in VALID_DAYS
            and clip.get("output_filename") == expected_filename
            and clip.get("flow_mode") == ("first_frame_to_video" if clip.get("world") == "ROOM_A" and i != 0 else "text_to_video")
            and clip.get("reference_media_verified") is False
            and clip.get("first_frame_status") == (
                "S01_IS_ROOT_VIDEO_ANCHOR_PENDING" if i == 0 else
                "PENDING_APPROVED_S01_FRAME_AND_SHOT_SPECIFIC_KEYFRAME"
                if clip.get("world") == "ROOM_A" else "NOT_REQUIRED")
            and clip.get("final_use_allowed") is False
            and clip.get("technical_verified") is False
            and clip.get("editorial_approved") is False
            and clip.get("rights_cleared") is False
            and isinstance(clip.get("flow_prompt"), str)
            and len(clip["flow_prompt"]) >= 500
        ):
            raise IntakeRejected(f"scene_or_flow_approval_invalid_{i+1:02d}")
        name = clip["output_filename"]
        if name in names or not re.fullmatch(r"VNC-E01-S\d{2}-FLOW-CANDIDATE\.mp4", name):
            raise IntakeRejected("duplicate_or_unsafe_filename")
        names.add(name)
        by_day[clip["suggested_day"]] += 10
    if (len(names) != 12 or sorted(by_day.values()) != [20, 50, 50]
            or sum(by_day.values()) != 120):
        raise IntakeRejected("free_daily_budget_overspent")
    if "rain" not in scenes[0]["flow_prompt"].lower() or "closed" not in scenes[0]["flow_prompt"].lower():
        raise IntakeRejected("s01_signature_lost")
    if "notebook" not in scenes[-1]["flow_prompt"].lower():
        raise IntakeRejected("s12_loop_signature_lost")
    return plan


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            sha.update(block)
    return sha.hexdigest()


def _run(cmd: list[str], timeout: int, *, capture: bool = True):
    return subprocess.run(
        cmd, timeout=timeout, capture_output=capture, text=True, check=False
    )


def inspect_file(video: Path, required_seconds: float, *,
                 ffprobe: str = "ffprobe", ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    """Only physical media facts. Rights, images, actor and authenticity remain unapproved."""
    if not video.is_file() or video.is_symlink():
        raise IntakeRejected("not_a_regular_file")
    size = video.stat().st_size
    if not 100_000 <= size <= 200_000_000:
        raise IntakeRejected("video_size_outside_safe_bounds")
    result = _run([
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate:format=duration",
        "-of", "json", str(video)], timeout=35)
    if result.returncode:
        raise IntakeRejected("ffprobe_failed")
    try:
        payload = json.loads(result.stdout)
        tracks = payload["streams"]
        if len(tracks) != 1:
            raise ValueError()
        stream = tracks[0]
        duration = float(payload["format"]["duration"])
        width, height = int(stream["width"]), int(stream["height"])
        parts = stream["avg_frame_rate"].split("/")
        fps = int(parts[0]) / int(parts[1])
        codec = stream["codec_name"]
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError):
        raise IntakeRejected("probe_metadata_malformed") from None
    if not (
        math.isfinite(duration) and duration + 0.015 >= required_seconds
        and duration <= 16
        and width >= 600 and height >= 1000
        and abs(width / height - (9 / 16)) < .04
        and 23 <= fps <= 61
        and codec in ("h264", "hevc", "av1", "vp9")
    ):
        raise IntakeRejected("length_geometry_fps_or_codec_not_compatible")
    decoded = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-xerror",
         "-i", str(video), "-map", "0:v:0", "-an",
         "-f", "null", "-"],
        capture_output=True, text=False, timeout=120, check=False
    )
    if decoded.returncode:
        raise IntakeRejected("full_mp4_decode_failed")
    # Sampling is a diagnostic, NOT proof of semantic camera/body motion.
    motion = subprocess.run([
        ffmpeg, "-nostdin", "-v", "error", "-i", str(video),
        "-map", "0:v:0", "-an",
        "-vf", "fps=3,scale=48:84:flags=fast_bilinear,format=gray",
        "-f", "rawvideo", "-"],
        capture_output=True, text=False, timeout=55, check=False)
    step = 48 * 84
    if motion.returncode or len(motion.stdout) < step * 9 or len(motion.stdout) % step:
        raise IntakeRejected("temporal_sample_unreadable")
    frames = [memoryview(motion.stdout)[j:j+step] for j in range(0, len(motion.stdout), step)]
    diffs = [
        sum(abs(x-y) for x,y in zip(a,b)) / step
        for a,b in zip(frames, frames[1:])
    ]
    avg_diff = sum(diffs) / len(diffs)
    return {
        "status": "PHYSICAL_BYTES_VALID_PENDING_EDITORIAL_AND_RIGHTS",
        "sha256": _sha256(video), "bytes": size,
        "width": width, "height": height,
        "duration_seconds": round(duration, 3), "fps": round(fps, 4),
        "codec": codec, "full_mp4_decode": True,
        "sampled_temporal_frames": len(frames),
        "mean_temporal_luma_difference": round(avg_diff, 4),
        "low_motion_warning": avg_diff < 0.55,
        "human_and_object_temporal_motion_verified": False,
        "continuous_scene_verified": False,
        "watermark_checked": False,
        "actor_room_notebook_rain_verified": False,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False
    }


def audit_files(directory: Path, root: Path = ROOT):
    manifest = verified_manifest(root)
    directory = Path(directory)
    if not directory.is_dir():
        raise IntakeRejected("intake_directory_missing")
    report = {
        "project": "VERBO_NO_CHAO_EXCLUSIVO", "episode_id": "VNC-W01-E1",
        "status": "CANDIDATE_MP4_AUDIT_NOT_A_MASTER",
        "source_audio_sha256": manifest["source_audio_sha256"],
        "source_script_sha256": manifest["source_script_sha256"],
        "expected": 12,
        "physical_candidates_verified": 0,
        "editorially_approved": 0,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
        "scenes": []
    }
    for scene in manifest["scenes"]:
        candidate = directory / scene["output_filename"]
        if not candidate.exists():
            report["scenes"].append({"scene_id": scene["scene_id"], "status": "MISSING"})
            continue
        try:
            details = inspect_file(candidate, scene["source_duration_seconds"])
            report["physical_candidates_verified"] += 1
        except (IntakeRejected, OSError, subprocess.TimeoutExpired) as exc:
            # Never echo source paths, untrusted provider errors or user data.
            details = {"status": "BLOCKED_TECHNICAL_QA",
                       "reason": type(exc).__name__ + (":" + str(exc) if isinstance(exc, IntakeRejected) else "")}
        report["scenes"].append({"scene_id": scene["scene_id"], **details})
    return report


def main():
    parser = argparse.ArgumentParser(description="Private local clip audit; NEVER PUBLICATION.")
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        report = audit_files(args.dir)
    except (IntakeRejected, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "BLOCKED_INTAKE_CONTRACT", "reason": type(error).__name__,
                          "master_allowed": False, "publication_authorized": False}))
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["physical_candidates_verified"] == 12 else 2


if __name__ == "__main__":
    raise SystemExit(main())
