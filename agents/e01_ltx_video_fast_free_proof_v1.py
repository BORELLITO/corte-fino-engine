"""VNC E01 S01: one anonymous zero-dollar Lightricks LTX 0.9.8 motion proof.

The video is a candidate only, never a master, licence or publication approval.
No personal media, token, billing, paid API, retry or account automation.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from agents.e01_stock_candidates import ROOT

BRANCH = "verbo-no-chao/e01-ltx-video-fast-free-proof-20261119-v1"
SPACE = "Lightricks/ltx-video-distilled"
SPACE_API = "https://huggingface.co/api/spaces/" + SPACE
PROVIDER_API = "/text_to_video"
LOCK = "operations/vnc_e01_s01_ltxfast_one_shot_20261119.json"
REPO = "BORELLITO/verbo-no-chao-engine"
OUTPUT = Path("artifacts/vnc_e01_s01_ltxfast")
REPORT = OUTPUT / "technical_report.json"
SECONDS = 6.0
WIDTH, HEIGHT = 512, 896
TARGET_SCENE = 5.74
PROMPT = (
    "Single uninterrupted photorealistic cinematic six-second shot, original fictional story. "
    "Night in a small modest apartment, one anonymous adult STRICTLY seen from behind wearing "
    "a charcoal wool jacket, seated near a window visibly streaked with streaming raindrops. "
    "One CLOSED dark notebook rests FLAT on the worn wooden table, cover fully shut, no pages "
    "visible. Soft dim amber lamp, slate black shadows, genuine natural breathing and subtle "
    "hand movement, restrained steady slow forward camera dolly. The face is never visible. "
    "Rain streaks visibly move. Subtle film grain, precise anatomy, no supernatural imagery, "
    "no extra people, no letters, no screens or logos. Keep bottom quarter dark and calm for "
    "later subtitle overlay. Serious grounded contemplative documentary-noir atmosphere."
)
NEGATIVE = ("open book, open notebook, visible pages, face, frontal view, daylight, dry window, "
            "extra people, missing limbs, text, logo, watermark, image slideshow, cartoons, "
            "video overlays, glitches, freeze-frame, camera shake")
CANONICAL_SHA = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
CANONICAL_AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"


def report(status: str, **data):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "project": "VERBO_NO_CHAO_EXCLUSIVO", "scene": "VNC-E01V2-S01",
        "source_space": SPACE, "source_model": "LTX-Video-0.9.8-13B-distilled",
        "status": status, "goal_seconds": TARGET_SCENE, "requested_seconds": SECONDS,
        "cost_usd": 0, "master_1080p": False, "rights_cleared": False,
        "editorial_approved": False, "publication_authorized": False,
        "no_private_user_media": True, "no_payment_or_account": True,
    }
    evidence.update(data)
    REPORT.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "scene": "S01", "media_verified": bool(data.get("full_decode_ok", False)),
                      "publication_authorized": False}), flush=True)


def fail(reason: str):
    report("BLOCKED_NO_SCENE_MEDIA", reason=reason)
    raise SystemExit(2)


def validate_source(root=ROOT):
    data = json.loads((root / "contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf8"))
    scene = data["scenes"][0]
    if not (data.get("script_sha256") == CANONICAL_SHA and
            data.get("audio_sha256") == CANONICAL_AUDIO and
            data.get("publication_authorized") is False and
            scene.get("id") == "VNC-E01V2-S01" and
            scene.get("end_seconds") == TARGET_SCENE and
            scene.get("approved_for_export") is False and
            not scene.get("asset_sha256")):
        raise ValueError("source_or_scene_guard_mismatch")
    return True


def check_space_running():
    request = urllib.request.Request(
        SPACE_API, headers={"User-Agent": "VNC-E01-LTX-fast-preflight/1.0"})
    with urllib.request.urlopen(request, timeout=18) as response:
        if response.status != 200:
            return False
        body = response.read(180001)
    if len(body) > 180000:
        return False
    obj = json.loads(body)
    return (obj.get("runtime") or {}).get("stage") == "RUNNING"


def consume_lock_before_request():
    token = os.environ.get("GITHUB_TOKEN", "")
    sha = os.environ.get("GITHUB_SHA", "")
    if len(token) < 16 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail("github_lock_access_missing")
    document = {"project": "VERBO_NO_CHAO_EXCLUSIVO", "scene_id": "VNC-E01V2-S01",
                "provider": SPACE, "requested_seconds": SECONDS,
                "status": "ONE_ATTEMPT_CONSUMED_BEFORE_EXTERNAL_CALL",
                "time_utc": datetime.now(timezone.utc).isoformat(),
                "source_sha": sha, "max_requests": 1, "cost_ceiling_usd": 0,
                "publication_authorized": False}
    url = f"https://api.github.com/repos/{REPO}/contents/{LOCK}"
    payload = {"message": "audit(vnc): lock single LTX Fast S01 proof before request",
               "content": base64.b64encode(json.dumps(document).encode()).decode(),
               "branch": BRANCH}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="PUT",
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "vnc-ltx-once/1.0",
                 "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 201:
                fail("durable_lock_not_created")
    except urllib.error.HTTPError as error:
        fail("durable_lock_rejected_or_already_exists")
    except Exception:
        fail("durable_lock_network_unknown_no_request")


def validate_request(args):
    if len(args) != 13:
        raise ValueError("expected_exact_gradio_13_inputs")
    if not (args[2] is None and args[3] is None and args[4:9] ==
            (HEIGHT, WIDTH, "text-to-video", SECONDS, 9)):
        raise ValueError("unexpected_media_or_request")
    if not (args[0] == PROMPT and args[1] == NEGATIVE and args[9:] ==
            (42251, False, 3.0, False)):
        raise ValueError("unexpected_seed_or_paid_setting")
    return True


def video_path_from_result(result):
    if not isinstance(result, (tuple, list)) or len(result) < 1:
        raise ValueError("no_provider_video_result")
    value = result[0]
    if isinstance(value, dict):
        value = value.get("video") or value.get("path")
    if isinstance(value, dict):
        value = value.get("path") or value.get("name")
    if not isinstance(value, str) or not Path(value).is_file():
        raise ValueError("no_physical_video_file")
    return Path(value)


def verify_mp4(source: Path):
    if not source.is_file() or not (20000 <= source.stat().st_size <= 75_000_000):
        raise ValueError("invalid_video_byte_count")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,codec_name:format=duration",
         "-of", "json", str(source)], capture_output=True, text=True, timeout=25)
    if probe.returncode:
        raise ValueError("ffprobe_failed")
    info = json.loads(probe.stdout)
    stream = (info.get("streams") or [{}])[0]
    duration = float(info.get("format", {}).get("duration") or 0)
    n, d = [int(x) for x in stream.get("avg_frame_rate", "0/0").split("/")]
    fps = n / d if d else 0
    if (stream.get("width") != WIDTH or stream.get("height") != HEIGHT or
        duration < TARGET_SCENE or duration > 8.5 or
        not 23.8 <= fps <= 30.2 or stream.get("codec_name") not in {"h264", "hevc"}):
        raise ValueError("wrong_duration_geometry_fps_or_codec")
    decoded = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(source),
         "-map", "0:v:0", "-an", "-f", "null", "-"],
        capture_output=True, timeout=75)
    if decoded.returncode:
        raise ValueError("incomplete_full_video_decode")
    return {"duration_seconds": duration, "width": WIDTH, "height": HEIGHT,
            "fps": fps, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "bytes": source.stat().st_size, "codec": stream["codec_name"],
            "full_decode_ok": True, "covers_scene_duration": True}


def main():
    report("STARTED_NOT_MEDIA")
    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        fail("not_an_authorized_one_shot_push")
    if os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH:
        fail("wrong_branch")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        fail("replay_prohibited")
    try:
        validate_source()
    except Exception:
        fail("immutable_scene_source_mismatch")
    try:
        running = check_space_running()
    except Exception:
        fail("provider_read_only_preflight_unavailable")
    if not running:
        fail("provider_is_not_running")
    args = (PROMPT, NEGATIVE, None, None, HEIGHT, WIDTH, "text-to-video",
            SECONDS, 9, 42251, False, 3.0, False)
    validate_request(args)
    consume_lock_before_request()
    report("LOCK_CONSUMED_PROVIDER_REQUEST_PENDING")
    from gradio_client import Client
    try:
        client = Client(SPACE, verbose=False)
        output = client.predict(*args, api_name=PROVIDER_API)
        incoming = video_path_from_result(output)
        info = verify_mp4(incoming)
        destination = OUTPUT / "VNC-E01-S01-LTXFAST-MOTION-CANDIDATE-NOT-MASTER.mp4"
        shutil.copy2(incoming, destination)
        info["artifact_mp4_name"] = destination.name
        report("ACTUAL_GENERATED_MOTION_PHYSICALLY_VERIFIED_EDITORIAL_PENDING", **info)
    except Exception as err:
        # Keep public logs free of arbitrary untrusted provider error contents.
        fail("provider_or_media_validation_failed_" + type(err).__name__)


if __name__ == "__main__":
    main()
