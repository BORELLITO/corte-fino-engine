"""Temporary E01 stock frame QA, not a rights gate or final video approval.

Four source MP4s are downloaded, physically verified, sampled, and deleted.
Only numerical metrics and a low-resolution four-row QA contact sheet persist
for a short-lived GitHub Actions artifact. No original movie is uploaded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path
try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
except ImportError:  # Primary engine gates do not install imaging packages.
    Image = ImageChops = ImageDraw = ImageFont = ImageStat = None
from agents.e01_stock_candidates import ROOT, CONTRACT, StockIntakeError, require, probe_item, validate
from agents.e01_stock_probe_evidence import EXPECTED_HASHES, verify

THUMB_W, THUMB_H = 216, 384
FRACTIONS = (0.15, 0.50, 0.85)
TEXT_BAR = 40

def sample_frame(file: Path, second: float, ffmpeg: str) -> Image.Image:
    require(file.is_file() and math.isfinite(second) and second >= 0,
            "frame_qa:invalid_source_or_time")
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
           "-ss", f"{second:.3f}", "-i", str(file), "-an",
           "-frames:v", "1", "-vf", f"scale={THUMB_W}:{THUMB_H}:flags=lanczos",
           "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    result = subprocess.run(cmd, capture_output=True, timeout=45, check=False)
    require(result.returncode == 0 and len(result.stdout) == THUMB_W*THUMB_H*3,
            "frame_qa:no_decodable_preview_frame")
    return Image.frombytes("RGB", (THUMB_W, THUMB_H), result.stdout)

def image_metrics(images: list[Image.Image]) -> dict:
    require(len(images) == 3 and all(im.mode == "RGB" and
            im.size == (THUMB_W, THUMB_H) for im in images),
            "frame_qa:invalid_sample_set")
    metrics = []
    for im in images:
        gray = im.convert("L")
        stat = ImageStat.Stat(gray)
        hist = gray.histogram()
        n = THUMB_W * THUMB_H
        metrics.append({
            "luma_mean": round(stat.mean[0], 2),
            "luma_stddev": round(stat.stddev[0], 2),
            "near_black_share": round(sum(hist[:16])/n, 5),
            "near_white_share": round(sum(hist[240:])/n, 5),
        })
    diffs = []
    for first, second in zip(images, images[1:]):
        delta = ImageChops.difference(first, second).convert("L")
        diffs.append(round(ImageStat.Stat(delta).mean[0], 2))
    return {
        "sample_frames": 3,
        "frame_position_fractions": list(FRACTIONS),
        "frames": metrics,
        "sequential_sample_luma_difference": diffs,
        "potential_very_dark_frame": any(m["luma_mean"] < 27 for m in metrics),
        "potential_static_footage": all(d <= 1.2 for d in diffs),
        "logo_face_text_and_narrative_review_complete": False,
        "human_frame_review_complete": False,
    }

def contact_sheet(rows: list[tuple[str, list[Image.Image]]], target: Path) -> dict:
    require(len(rows) == 4 and all(len(frames) == 3 for _, frames in rows),
            "frame_qa:contact_sheet_requires_four_rows")
    canvas = Image.new("RGB", (3*THUMB_W, 4*(THUMB_H+TEXT_BAR)), (22, 22, 24))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for index, (label, frames) in enumerate(rows):
        y0 = index*(THUMB_H+TEXT_BAR)
        for col, frame in enumerate(frames):
            require(frame.mode == "RGB" and frame.size == (THUMB_W, THUMB_H),
                    "frame_qa:bad_frame_geometry")
            canvas.paste(frame, (col*THUMB_W, y0))
            d.rectangle((col*THUMB_W+2, y0+4, col*THUMB_W+95, y0+30),
                        fill=(22, 22, 24))
            d.text((col*THUMB_W+7, y0+7), f"{int(FRACTIONS[col]*100)}%", font=font,
                   fill=(245, 240, 230))
        d.rectangle((0, y0+THUMB_H, 3*THUMB_W, y0+THUMB_H+TEXT_BAR),
                    fill=(19, 19, 20))
        d.text((8, y0+THUMB_H+7), f"{label} | QA INTERNO - NAO PUBLICAR",
               font=font, fill=(244, 241, 235))
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "JPEG", quality=77, optimize=True, subsampling=1)
    raw = target.read_bytes()
    require(15000 <= len(raw) <= 1200000,
            "frame_qa:preview_image_implausible")
    return {"name": target.name, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "width": canvas.width, "height": canvas.height,
            "type": "derived_contact_sheet_low_resolution_qa_only"}

def run(root: Path, out: Path, ffmpeg: str, ffprobe: str) -> dict:
    require(Image is not None, "frame_qa:pillow_required")
    validate(root)
    verify(root)
    contract = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "project": "verbo-no-chao", "episode_id": "VNC-W01-E1",
        "status": "BLOCKED_FRAME_QA_INCOMPLETE", "candidates_expected": 4,
        "probed_candidates": [], "rights_cleared": False,
        "visual_editorial_approval": False, "master_1080x1920_completed": False,
        "publication_authorized": False, "raw_mp4_exported": False,
    }
    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix="vnc_frame_qa_") as folder:
            temp = Path(folder)
            for item in contract["candidates"]:
                observation = probe_item(item, temp, ffprobe, ffmpeg)
                require(observation["sha256"] == EXPECTED_HASHES[item["id"]],
                        "frame_qa:cdn_file_changed")
                movie = temp/(item["id"]+".mp4")
                frames = [sample_frame(movie, observation["duration_seconds"]*f, ffmpeg)
                          for f in FRACTIONS]
                probe = image_metrics(frames)
                report["probed_candidates"].append({**observation, "qa": probe})
                rows.append((item["scene_id"].split("-")[-1], frames))
                movie.unlink(missing_ok=True)
            require(len(report["probed_candidates"]) == 4,
                    "frame_qa:incomplete_observations")
            sheet = contact_sheet(rows, out/"e01-stock-contact-sheet-qa-only.jpg")
            report["derived_preview"] = sheet
            report["status"] = "PHYSICAL_AND_FRAME_SAMPLING_COMPLETE_EDITORIAL_RIGHTS_PENDING"
    except (StockIntakeError, OSError, ValueError, KeyError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        (out/"e01-stock-contact-sheet-qa-only.jpg").unlink(missing_ok=True)
        report["error_type"] = type(error).__name__
        report["status"] = "BLOCKED_FRAME_QA_INCOMPLETE"
    (out/"e01-stock-frame-qa.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args=parser.parse_args()
    report=run(args.root,args.out_dir,args.ffmpeg,args.ffprobe)
    print(json.dumps({k:report.get(k) for k in (
        "status","candidates_expected","derived_preview","rights_cleared",
        "publication_authorized","error_type")},ensure_ascii=False))
    return 0 if report["status"].startswith("PHYSICAL_AND_FRAME") else 2

if __name__ == "__main__":
    raise SystemExit(main())
