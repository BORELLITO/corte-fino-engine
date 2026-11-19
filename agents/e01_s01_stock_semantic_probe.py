"""VERBO NO CHÃO E01 S01 — targeted physical stock semantic QA, never a release.

Downloads only three named Pexels free-video public sources, no auth/API key,
temporarily. Publishes only small derived contact sheet + measurement JSON.
No source MP4 is uploaded, no master, no credentials, no paid endpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from agents.e01_stock_candidates import ROOT

CANDIDATES = (
    {"video_id": 16835716, "source": "https://www.pexels.com/video/a-man-sitting-in-a-dark-room-with-a-lamp-16835716/", "name": "Night reader", "creator": "khanhhoangminh", "page_seconds": 13, "page_width": 1920, "page_height": 1080, "risk": "Person reads, likely OPEN book; rain, closed notebook and back-only must be inspected"},
    {"video_id": 32788087, "source": "https://www.pexels.com/video/silhouette-of-man-working-in-a-dimly-lit-study-32788087/", "name": "Dim study", "creator": "Salih Sezgen", "page_seconds": 16, "page_width": 3840, "page_height": 2160, "risk": "Potentially stylized/AI source and desk mismatch; verify reality and actor from frames"},
    {"video_id": 6944291, "source": "https://www.pexels.com/video/a-man-having-problems-6944291/", "name": "Contemplative man", "creator": "cottonbro studio", "page_seconds": 27, "page_width": 4096, "page_height": 2160, "risk": "Face and actor inconsistent, no verified notebook or rain; third-party depiction risk"},
)
OUTPUT = Path("artifacts/vnc_e01_s01_stock_semantic")
MAX_BYTES = 160 * 1024 * 1024
FRAME_FRACTIONS = (0.15, 0.50, 0.85)
TARGET_SECONDS = 5.74
CANONICAL_SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
CANONICAL_AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"


class StockSemanticError(ValueError):
    pass


class PexelsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, video_id: int):
        self.video_id = video_id
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if (parsed.scheme != "https"
            or parsed.hostname != "videos.pexels.com"
            or parsed.port is not None
            or parsed.username or parsed.password
            or not re.fullmatch(r"/video-files/" + str(self.video_id) + r"/[A-Za-z0-9_.-]+\.mp4", parsed.path)):
            raise StockSemanticError("blocked_untrusted_download_redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_storyboard(root=ROOT):
    obj = json.loads((Path(root) / "contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf8"))
    first = obj["scenes"][0]
    if not (obj.get("project") == "verbo-no-chao" and
            obj.get("script_sha256") == CANONICAL_SCRIPT and
            obj.get("audio_sha256") == CANONICAL_AUDIO and
            obj.get("publication_authorized") is False and
            first.get("id") == "VNC-E01V2-S01" and
            first.get("end_seconds") == TARGET_SECONDS and
            first.get("asset_sha256") is None and
            first.get("approved_for_export") is False):
        raise StockSemanticError("source_storyboard_lock_failed")
    return True


def validate_candidates():
    if len(CANDIDATES) != 3 or len({c["video_id"] for c in CANDIDATES}) != 3:
        raise StockSemanticError("candidate_count_or_duplicates")
    for c in CANDIDATES:
        if (not isinstance(c["video_id"], int)
            or not c["source"].startswith("https://www.pexels.com/video/")
            or not c["source"].endswith(f"-{c['video_id']}/")
            or c["page_seconds"] < TARGET_SECONDS
            or c["page_width"] < 1920
            or c["page_height"] < 1080
            or len(c["risk"]) < 15):
            raise StockSemanticError("invalid_candidate_provenance")
    return True


def download(video_id: int, destination: Path):
    req = urllib.request.Request(
        f"https://www.pexels.com/download/video/{video_id}/",
        headers={"User-Agent": "Mozilla/5.0 VNC-Editorial-Research/1.0",
                 "Accept": "video/mp4,application/octet-stream,*/*"})
    opener = urllib.request.build_opener(PexelsOnlyRedirect(video_id))
    count = 0
    sha = hashlib.sha256()
    with opener.open(req, timeout=40) as response:
        host = urllib.parse.urlsplit(response.url).hostname
        if response.status != 200 or host != "videos.pexels.com":
            raise StockSemanticError("not_official_pexels_video")
        total = response.headers.get("Content-Length")
        if total and int(total) > MAX_BYTES:
            raise StockSemanticError("oversized_source")
        content_type = response.headers.get("Content-Type", "").lower()
        if not ("video/" in content_type or "octet-stream" in content_type):
            raise StockSemanticError("unexpected_media_type")
        with destination.open("wb") as out:
            while True:
                buf = response.read(1024 * 1024)
                if not buf:
                    break
                count += len(buf)
                if count > MAX_BYTES:
                    raise StockSemanticError("source_exceeds_bytes_limit")
                sha.update(buf)
                out.write(buf)
    if count < 100_000:
        raise StockSemanticError("too_short_to_be_real_video_bytes")
    return {"sha256": sha.hexdigest(), "source_size_bytes": count}


def media_probe(source: Path):
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name,avg_frame_rate:format=duration",
         "-of", "json", str(source)],
        capture_output=True, text=True, timeout=25)
    if proc.returncode:
        raise StockSemanticError("ffprobe_failed")
    obj = json.loads(proc.stdout)
    streams = obj.get("streams") or []
    if len(streams) != 1:
        raise StockSemanticError("video_stream_missing")
    s = streams[0]
    duration = float(obj["format"]["duration"])
    n, d = (int(x) for x in s.get("avg_frame_rate", "0/0").split("/"))
    fps = n / d if d else 0
    if (not TARGET_SECONDS <= duration <= 120 or
        int(s["width"]) < 1080 or int(s["height"]) < 720 or
        not 23 <= fps <= 120):
        raise StockSemanticError("duration_fps_geometry_unsupported")
    return {"duration_seconds": duration, "width": s["width"], "height": s["height"], "fps": round(fps, 3), "codec": s["codec_name"]}


def full_decode(source: Path):
    ret = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(source),
         "-map", "0:v:0", "-an", "-f", "null", "-"],
        capture_output=True, timeout=165)
    if ret.returncode:
        raise StockSemanticError("full_decode_failed")


def motion_metric(source: Path):
    w, h = 64, 36
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", "0",
         "-i", str(source), "-an",
         "-vf", f"fps=2,scale={w}:{h}:flags=fast_bilinear,format=gray",
         "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"],
        capture_output=True, timeout=60)
    if proc.returncode or len(proc.stdout) < 10 * w * h or len(proc.stdout) % (w*h):
        raise StockSemanticError("motion_sampling_failed")
    raw = proc.stdout
    samples = [memoryview(raw)[k:k+w*h] for k in range(0, len(raw), w*h)]
    diffs = [sum(abs(a-b) for a,b in zip(p,q))/(w*h) for p,q in zip(samples, samples[1:])]
    return {"sampled_frames": len(samples), "adjacent_gray_luma_difference": round(sum(diffs)/len(diffs),3),
            "has_measurable_motion_candidate": sum(diffs)/len(diffs) > .55,
            "semantic_human_motion_verified": False}


def frame(source: Path, t: float, crop_mode: str):
    # Reject untrusted framing before requiring optional imaging dependencies.
    if crop_mode not in ("wide", "left", "center", "right"):
        raise StockSemanticError("invalid_crop_mode")
    # Each frame is real footage; no face generation or added objects.
    from PIL import Image
    if crop_mode == "wide":
        w, h = 426, 240
        vf = f"scale={w}:{h}:flags=lanczos"
    elif crop_mode in ("left", "center", "right"):
        w, h = 135, 240
        x = {"left":"0", "center":"(in_w-out_w)/2", "right":"in_w-out_w"}[crop_mode]
        vf = f"scale=426:240:flags=lanczos,crop={w}:{h}:{x}:0"
    else:
        raise StockSemanticError("invalid_crop_mode")
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.3f}",
         "-i", str(source), "-an", "-frames:v", "1",
         "-vf", vf, "-pix_fmt", "rgb24",
         "-f", "rawvideo", "pipe:1"],
        capture_output=True, timeout=30)
    if proc.returncode or len(proc.stdout) != w * h * 3:
        raise StockSemanticError("image_frame_extract_failed")
    return Image.frombytes("RGB", (w,h), proc.stdout)


def contact_sheet(source: Path, seconds: float, candidate: dict, destination: Path):
    from PIL import Image, ImageDraw
    previews = [frame(source, seconds * f, "wide") for f in FRAME_FRACTIONS]
    crops = [frame(source, seconds*.50, mode) for mode in ("left", "center", "right")]
    w = 3*426 + 3*135
    h = 276
    sheet = Image.new("RGB", (w, h), (20, 20, 22))
    x=0
    for image, label in zip(previews+crops, ("15% full", "50% full", "85% full",
                                         "50% LEFT", "50% CENTER", "50% RIGHT")):
        sheet.paste(image, (x, 0))
        ImageDraw.Draw(sheet).text((x+4, 246), label, fill=(248,244,237))
        x += image.width
    ImageDraw.Draw(sheet).text(
        (7,263), f"Pexels {candidate['video_id']} | QA ONLY / NOT APPROVED / NO PUBLICATION",
        fill=(210,200,180))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, "JPEG", quality=83, optimize=True)
    return {"file": destination.name, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "width": w, "height": h}


def audit_one(candidate, directory: Path, output: Path):
    ident = candidate["video_id"]
    movie = directory / f"{ident}.mp4"
    try:
        item = download(ident, movie)
        meta = media_probe(movie)
        full_decode(movie)
        metric = motion_metric(movie)
        shot = contact_sheet(movie, meta["duration_seconds"], candidate,
                            output/f"pexels_{ident}_qa_only.jpg")
        return {"status": "PHYSICAL_VIDEO_VERIFIED_EDITORIAL_REVIEW_PENDING",
                "source": candidate["source"], "video_id": ident,
                "creator": candidate["creator"], "risk": candidate["risk"],
                "download_sha256": item["sha256"], "bytes": item["source_size_bytes"],
                "verified": meta, "motion": metric, "contact_sheet": shot,
                "physical_decode_complete": True,
                "studio_and_character_match_verified": False,
                "closed_notebook_verified": False, "visible_rain_verified": False,
                "rights_of_identifiable_people_cleared": False,
                "commercial_publication_authorized": False}
    except (OSError, ValueError, KeyError, TimeoutError, subprocess.TimeoutExpired,
            urllib.error.URLError) as ex:
        (output/f"pexels_{ident}_qa_only.jpg").unlink(missing_ok=True)
        return {"status": "BLOCKED_PHYSICAL_QA", "source": candidate["source"],
                "video_id": ident, "error_type": type(ex).__name__,
                "verified": False, "commercial_publication_authorized": False}
    finally:
        movie.unlink(missing_ok=True)


def run(root=ROOT, output=OUTPUT):
    validate_storyboard(root)
    validate_candidates()
    output.mkdir(parents=True, exist_ok=True)
    report = {"project": "VERBO_NO_CHAO_EXCLUSIVO", "episode": "VNC-W01-E1",
              "scene": "VNC-E01V2-S01", "status": "BLOCKED_NOT_EDITORIALLY_APPROVED",
              "target_seconds": TARGET_SECONDS, "source_license": "Pexels License",
              "source_license_url": "https://www.pexels.com/license/",
              "can_use_in_commercial_context_without_extra_rights": False,
              "master_rendered": False, "publication_authorized": False, "candidates": []}
    with tempfile.TemporaryDirectory(prefix="vnc_s01_stock_") as tmp:
        for c in CANDIDATES:
            report["candidates"].append(audit_one(c, Path(tmp), output))
    report["physically_verified_videos"] = sum(
        x["status"]=="PHYSICAL_VIDEO_VERIFIED_EDITORIAL_REVIEW_PENDING" for x in report["candidates"])
    report["status"] = ("PHYSICAL_SOURCE_QA_COMPLETE_EDITORIAL_BLOCKED"
                       if report["physically_verified_videos"] == len(CANDIDATES)
                       else "PARTIAL_OR_FAILED_PHYSICAL_SOURCE_QA_EDITORIAL_BLOCKED")
    (output/"technical_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps({"status": report["status"], "physically_verified_videos":
                      report["physically_verified_videos"], "total": len(CANDIDATES),
                      "publication_authorized": False},ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUTPUT))
    args = parser.parse_args()
    data = run(output=Path(args.out))
    raise SystemExit(0 if data["physically_verified_videos"] else 2)
