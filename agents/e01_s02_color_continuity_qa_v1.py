"""Reproducible VNC E01 S02 low-light grade from immutable preview MP4s.

THIS TOOL NEVER GENERATES A MASTER OR RELEASE PERMISSION.
No stock download. Real moving footage is preserved; only S02 exposure/color
is adjusted. S01 original reference is read only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/e01_s02_color_continuity_qa_20261119_v1.json"
GRADE = (
    "eq=contrast=0.88:brightness=-0.035:saturation=0.65:gamma=0.64,"
    "colorbalance=bs=0.10:gs=0.04:rs=-0.01,vignette=PI/7"
)
FRAME_COUNTS = (173, 147)
WIDTH, HEIGHT, FPS = 720, 1280, 30
TOTAL_FRAMES = 319


class S02ColorContinuityError(ValueError):
    pass


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_contract(path: Path = CONTRACT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise S02ColorContinuityError("contract_not_object")
    expected = {
        "schema_version": "1.0.0",
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "scene_id": "VNC-E01V2-S02",
        "approval_state": "S01_APPROVED_S02_CANDIDATE_NOT_APPROVED",
        "filter_for_s02_only": GRADE,
    }
    for key, value in expected.items():
        if type(data.get(key)) is not type(value) or data.get(key) != value:
            raise S02ColorContinuityError("invalid_contract_" + key)
    orig = data.get("input_preview_source", {})
    required_inputs = {
        "s01_expected_sha256": "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961",
        "s02_expected_sha256": "31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786",
        "s01_trim_frames": 172, "s02_trim_frames": 147,
        "s01_art_approved": True, "s02_art_approved": False,
    }
    for key, value in required_inputs.items():
        if type(orig.get(key)) is not type(value) or orig.get(key) != value:
            raise S02ColorContinuityError("input_contract_mismatch_" + key)
    req = data.get("render_requirements", {})
    expected_req = {
        "fps": FPS, "frame_width": WIDTH, "frame_height": HEIGHT,
        "s02_frames": 147, "s01_s02_total_frames": TOTAL_FRAMES,
        "audio_included": False, "captions_included": False,
        "watermark_remaining": True, "master_allowed": False,
        "publication_authorized": False, "source_rights_cleared": False,
        "s01_video_edited_other_than_composite_reencode": False,
        "no_new_source_download": True,
    }
    for key, value in expected_req.items():
        if type(req.get(key)) is not type(value) or req.get(key) != value:
            raise S02ColorContinuityError("render_contract_mismatch_" + key)
    return data


def run_command(cmd: list[str], timeout: int = 90) -> bytes:
    completed = subprocess.run(cmd, capture_output=True, timeout=timeout,
                               check=False)
    if completed.returncode:
        raise S02ColorContinuityError("media_processor_failed")
    return completed.stdout


def probe_video(path: Path, expected_frames: int) -> dict:
    raw = run_command([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,codec_type,width,height,nb_frames,avg_frame_rate:format=duration",
        "-of", "json", str(path)
    ])
    obj = json.loads(raw.decode("utf-8"))
    streams = obj.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    if len(video) != 1 or len(streams) != 1:
        raise S02ColorContinuityError("unexpected_audio_or_streams")
    item = video[0]
    if (int(item.get("width", 0)) != WIDTH or
            int(item.get("height", 0)) != HEIGHT or
            item.get("avg_frame_rate") != "30/1" or
            int(item.get("nb_frames", 0)) != expected_frames or
            abs(float(obj["format"]["duration"]) -
                expected_frames / FPS) > 0.035):
        raise S02ColorContinuityError("frame_or_geometry_mismatch")
    return {"frames": expected_frames, "fps": FPS,
            "width": WIDTH, "height": HEIGHT,
            "duration_seconds": float(obj["format"]["duration"]),
            "audio": False, "stream_count": 1}


def full_decode(path: Path) -> None:
    run_command([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror",
        "-i", str(path), "-map", "0:v:0", "-an", "-f", "null", "-"
    ], timeout=80)


def render(s01: Path, s02: Path, out: Path, contract: Path = CONTRACT) -> tuple[int, dict]:
    out.mkdir(parents=True, exist_ok=True)
    grade = out / "S02_CLOCK_GRADE_A_QA.mp4"
    combined = out / "S01_APPROVED_S02_GRADED_A_TRANSITION_QA.mp4"
    result = {
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "scene_id": "VNC-E01V2-S02",
        "status": "BLOCKED_COLOR_QA_INCOMPLETE",
        "s01_visual_approved": True,
        "s02_visual_approved": False,
        "rights_cleared": False, "master_allowed": False,
        "publication_authorized": False, "contains_audio": False,
        "input_s01_original_untouched": True,
        "s01_composite_reencoded": True, "grade_s02_only": True,
    }
    try:
        spec = load_contract(contract)
        s01 = s01.resolve(strict=True)
        s02 = s02.resolve(strict=True)
        if s01 == s02 or any(inp == output.resolve() for inp in (s01, s02)
                            for output in (grade, combined)):
            raise S02ColorContinuityError("input_output_aliasing")
        for f in (s01, s02):
            if not f.is_file() or f.suffix.lower() != ".mp4":
                raise S02ColorContinuityError("source_not_video")
        required = spec["input_preview_source"]
        if digest(s01) != required["s01_expected_sha256"]:
            raise S02ColorContinuityError("s01_approved_video_sha_mismatch")
        if digest(s02) != required["s02_expected_sha256"]:
            raise S02ColorContinuityError("s02_input_video_sha_mismatch")
        probe_video(s01, FRAME_COUNTS[0])
        probe_video(s02, FRAME_COUNTS[1])
        run_command([
            "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(s02), "-vf", GRADE,
            "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "19", "-pix_fmt", "yuv420p", "-frames:v",
            str(FRAME_COUNTS[1]), str(grade),
        ], timeout=120)
        g = probe_video(grade, FRAME_COUNTS[1])
        full_decode(grade)
        filters = (
            "[0:v]trim=start_frame=0:end_frame=172,setpts=PTS-STARTPTS,"
            "format=yuv420p[v0];"
            "[1:v]trim=start_frame=0:end_frame=147,setpts=PTS-STARTPTS,"
            "format=yuv420p[v1];"
            "[v0][v1]concat=n=2:v=1:a=0,format=yuv420p[v]"
        )
        run_command([
            "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(s01), "-i", str(grade),
            "-filter_complex", filters, "-map", "[v]", "-an",
            "-frames:v", str(TOTAL_FRAMES), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-movflags", "+faststart", str(combined),
        ], timeout=135)
        c = probe_video(combined, TOTAL_FRAMES)
        full_decode(combined)
        result.update(
            status="PHYSICALLY_VERIFIED_S02_COLOR_QA_EDITORIAL_PENDING",
            original_s01_sha256=digest(s01),
            original_s02_sha256=digest(s02),
            graded_s02={**g, "sha256": digest(grade), "bytes": grade.stat().st_size},
            combined_preview={**c, "sha256": digest(combined),
                              "bytes": combined.stat().st_size}
        )
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired,
            json.JSONDecodeError) as exc:
        grade.unlink(missing_ok=True)
        combined.unlink(missing_ok=True)
        result["error_type"] = type(exc).__name__
        result["status"] = "BLOCKED_COLOR_QA_INCOMPLETE"
    (out / "S02_COLOR_MATCH_RENDER_REPORT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": result["status"], "master_allowed": False,
                      "publication_authorized": False}))
    return (0 if result["status"].startswith("PHYSICALLY_VERIFIED") else 2), result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--s01", type=Path, required=True)
    p.add_argument("--s02", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    return render(args.s01, args.s02, args.out)[0]


if __name__ == "__main__":
    raise SystemExit(main())
