"""VERBO NO CHÃO S01: camera-footage night-rain visual proposal, not approved.

Single Pexels stock source, original MP4 downloaded only to runner temporary dir.
Exports a reduced visibly marked test movie (without sound), 3 sampled frames,
SHA256/ffprobe/full decode report. Never publishes or changes the storyboard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from agents.e01_s01_multi_stock_pilot_v1 import download_source, probe
from agents.e01_s01_single_take_stock_qa import (
    crop_native, frame_at, build_contact, run_cmd
)
from agents.e01_stock_candidates import ROOT
from agents.e01_s01_stock_rejection_gate import load_registry

CONTRACT = ROOT / "contracts/e01_s01_night_rain_motif_probe_20261119_v1.json"
ASSET = 31069867
PAGE = "https://www.pexels.com/video/raindrop-reflections-on-nighttime-metro-glass-31069867/"
FPS = 30
FRAMES = 173
WIDTH, HEIGHT = 720, 1280


class NightRainProbeError(ValueError):
    pass


def validate_contract(obj=None, root=ROOT):
    if obj is None:
        obj = json.loads((Path(root) / "contracts/e01_s01_night_rain_motif_probe_20261119_v1.json").read_text(encoding="utf8"))
    if not isinstance(obj, dict):
        raise NightRainProbeError("non_object")
    required = {
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "scene_id": "VNC-E01V2-S01",
        "concept": "NIGHT_RAIN_WINDOW_SINGLE_TAKE_SYMBOLIC_VISUAL_ALTERNATIVE",
        "approval_status": "CONCEPT_RESEARCH_ONLY_NOT_USER_APPROVED",
        "source_class": "PEXELS_REAL_FOOTAGE_REVIEW_ONLY",
        "source_id": ASSET,
        "page_url": PAGE,
        "page_license": "Free / Pexels",
        "free_cost_only": True,
        "raw_movie_to_repo": False,
        "editorial_approved": False,
        "third_party_rights_cleared": False,
        "voice_license_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
        "release_state": "BLOCKED_RESEARCH",
        "scene_window_seconds": 5.74,
    }
    for key, value in required.items():
        if type(obj.get(key)) is not type(value) or obj[key] != value:
            raise NightRainProbeError("contract_mismatch_" + key)
    preview = obj.get("experimental_preview")
    if not isinstance(preview, dict) or any(
        type(preview.get(k)) is not type(v) or preview.get(k) != v
        for k, v in {
            "width": WIDTH, "height": HEIGHT, "fps": FPS, "frames": FRAMES,
            "source_audio_removed": True, "voice_added": False,
            "subtitles_added": False,
            "watermark": "PREVIA DE QA - NAO PUBLICAR"
        }.items()
    ):
        raise NightRainProbeError("preview_contract_invalid")
    if not isinstance(obj.get("known_storyboard_deviation"), list) or len(obj["known_storyboard_deviation"]) < 3:
        raise NightRainProbeError("storyboard_deviations_unacknowledged")
    if not isinstance(obj.get("rejected_source_ids"), list) or any(
        x == ASSET for x in obj["rejected_source_ids"]
    ):
        raise NightRainProbeError("wrong_rejected_media_class")
    load_registry(Path(root) / "contracts/e01_s01_stock_rejection_lock_20261119_v1.json")
    return obj


def watermark(path):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((50, 26, WIDTH - 50, 82), radius=12, fill=(12, 12, 12, 185))
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 22)
    except OSError:
        font = ImageFont.load_default()
    txt = "PREVIA DE QA - NAO PUBLICAR"
    bounds = dr.textbbox((0, 0), txt, font=font)
    dr.text(((WIDTH - (bounds[2] - bounds[0])) // 2, 44), txt, fill=(255, 255, 255, 255), font=font)
    img.save(path)


def build_visual_preview(src, output, mask, native_width, native_height):
    cw, ch = crop_native(native_width, native_height)
    filters = (
        f"[0:v]fps={FPS},crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})/2,"
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1[scene];"
        "[scene][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,"
        "format=yuv420p[v]"
    )
    run_cmd([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src),
        "-loop", "1", "-i", str(mask), "-filter_complex", filters,
        "-map", "[v]", "-an", "-frames:v", str(FRAMES), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-movflags", "+faststart", str(output)
    ], 160)
    meta = probe(output, min_seconds=5.7, min_width=WIDTH, min_height=HEIGHT)
    if meta["width"] != WIDTH or meta["height"] != HEIGHT or not 5.70 <= meta["duration_seconds"] <= 5.82:
        raise NightRainProbeError("preview_geometry_or_timing")
    run_cmd([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output),
        "-map", "0:v:0", "-an", "-f", "null", "-"
    ], 80)
    return meta


def run(output_dir: Path, root=ROOT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "project": "VERBO_NO_CHAO_EXCLUSIVO", "scene_id": "VNC-E01V2-S01",
        "source_id": ASSET, "status": "BLOCKED_NO_PHYSICAL_PREVIEW",
        "editorial_approved": False, "rights_cleared": False,
        "master_allowed": False, "publication_authorized": False,
        "voice_added": False, "captions_added": False, "raw_source_persisted": False,
        "single_shoot_real_stock_provenance": "UNVERIFIED_CLAIM_NOT_MADE",
        "storyboard_room_a_equivalent": False, "output": None,
    }
    target = output_dir / "S01_NIGHT_RAIN_SYMBOLIC_PREVIEW_NOT_MASTER.mp4"
    contact = output_dir / "S01_NIGHT_RAIN_REAL_FRAMES_QA.jpg"
    try:
        validate_contract(root=root)
        with tempfile.TemporaryDirectory(prefix="vnc_s01_night_rain_") as td:
            tmp = Path(td)
            movie, evidence = download_source({"id": ASSET, "page": PAGE}, tmp)
            physical = probe(movie, min_seconds=6.0, min_width=1080, min_height=1920)
            crop_native(physical["width"], physical["height"])
            run_cmd(["ffmpeg", "-nostdin", "-v", "error", "-xerror",
                     "-i", str(movie), "-map", "0:v:0", "-an", "-f", "null", "-"], 240)
            frames = [frame_at(movie, sec, physical["width"], physical["height"])
                      for sec in (0.5, 2.8, 5.4)]
            sheet = build_contact([(ASSET, frames)], contact)
            watermark(tmp / "qa_overlay.png")
            preview_probe = build_visual_preview(
                movie, target, tmp / "qa_overlay.png", physical["width"], physical["height"]
            )
            preview_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            result.update({
                "status": "REAL_STOCK_QA_PREVIEW_PHYSICALLY_VERIFIED_ART_AND_RIGHTS_PENDING",
                "source": {**evidence, **physical, "full_source_video_decode_ok": True},
                "contact_sheet": sheet,
                "output": {
                    **preview_probe, "path": target.name,
                    "sha256": preview_sha, "size_bytes": target.stat().st_size,
                    "frames": FRAMES, "full_preview_video_decode_ok": True,
                    "watermarked": True, "contains_audio": False
                }
            })
            movie.unlink(missing_ok=True)
    except Exception as exc:
        target.unlink(missing_ok=True)
        contact.unlink(missing_ok=True)
        result.update(status="BLOCKED_NO_PHYSICAL_PREVIEW",
                      error_type=type(exc).__name__,
                      # Only a bounded static code, not provider response/URLs
                      error_reason=str(exc) if isinstance(exc, NightRainProbeError) else None)
    (output_dir / "S01_NIGHT_RAIN_PHYSICAL_QA_REPORT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )
    print(json.dumps({
        "status": result["status"], "output_sha256": (result.get("output") or {}).get("sha256"),
        "error_type": result.get("error_type"), "master_allowed": False, "publication_authorized": False
    }))
    return 0 if result["status"].startswith("REAL_STOCK_QA_PREVIEW") else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("artifacts/vnc_s01_night_rain_qa"))
    return run(parser.parse_args().out)


if __name__ == "__main__":
    raise SystemExit(main())
