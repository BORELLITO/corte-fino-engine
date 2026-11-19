"""Real physical S01 single-take stock intake + low-res review sheets, NOT a master.

Reuses the existing Pexels strict redirect downloader; never exports original MP4s.
Only one exact-scope workflow may trigger this, with a fixed two-item shortlist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from agents.e01_s01_multi_stock_pilot_v1 import download_source, probe
from agents.e01_s01_stock_rejection_gate import load_registry
from agents.e01_stock_candidates import ROOT

CONTRACT = Path("contracts/e01_s01_single_take_stock_candidates_20261119_v2.json")
ALLOWED = (7026683,)
WINDOW = 5.74
WIDTH, HEIGHT = 216, 384
SAMPLE_TIMES = (0.5, 2.8, 5.4)


class SingleTakeProbeError(ValueError):
    pass


def validate_plan(root: Path = ROOT, obj: dict | None = None) -> list[dict]:
    if obj is None:
        obj = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise SingleTakeProbeError("bad_manifest")
    if (obj.get("project_id") != "VERBO_NO_CHAO_EXCLUSIVO"
            or obj.get("episode_id") != "VNC-W01-E1"
            or obj.get("scene_id") != "VNC-E01V2-S01"
            or obj.get("purpose") != "RESEARCH_SINGLE_TAKE_S01_ALTERNATIVE_V2_ONLY"
            or obj.get("mode") != "REAL_CAMERA_STOCK_NO_GENERATIVE_VIDEO"
            or obj.get("requested_s01_seconds") != WINDOW
            or obj.get("editorial_approval") is not False
            or obj.get("full_master_authorized") is not False
            or obj.get("publication_authorized") is not False
            or obj.get("no_cost_trial_only") is not True
            or obj.get("commercial_rights") != "PENDING_ITEM_REVIEW"):
        raise SingleTakeProbeError("manifest_release_or_identity_drift")
    cs = obj.get("candidates")
    if not isinstance(cs, list) or len(cs) != len(ALLOWED):
        raise SingleTakeProbeError("invalid_candidate_count")
    for item, expected_id in zip(cs, ALLOWED):
        if not isinstance(item, dict):
            raise SingleTakeProbeError("candidate_not_object")
        expected_page = {
            7026683: "https://www.pexels.com/video/a-woman-writing-on-the-notebook-7026683/",
        }[expected_id]
        if (type(item.get("video_id")) is not int
                or item["video_id"] != expected_id
                or item.get("page_url") != expected_page
                or item.get("page_license") != "Free / Pexels"
                or item.get("downloaded") is not False
                or item.get("editorial_status") != "PENDING_PHYSICAL_AND_FRAME_QA"
                or item.get("rights_cleared") is not False
                or not isinstance(item.get("known_conflict"), str)
                or len(item["known_conflict"]) < 20):
            raise SingleTakeProbeError("untrusted_candidate_or_false_rights")
    # Lock these names against historical rejected source pairs.
    load_registry(root / "contracts" / "e01_s01_stock_rejection_lock_20261119_v1.json")
    return cs


def crop_native(width: int, height: int) -> tuple[int, int]:
    if (type(width) is not int or type(height) is not int
            or width < 1080 or height < 1920):
        raise SingleTakeProbeError("insufficient_source_height_or_width")
    cropw = min(width, 2 * math.floor(height * 9 / 16 / 2))
    croph = min(height, 2 * math.floor(width * 16 / 9 / 2))
    if cropw < 1080 or croph < 1920:
        raise SingleTakeProbeError("insufficient_portrait_crop")
    return cropw, croph


def run_cmd(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    r = subprocess.run(args, timeout=timeout, capture_output=True)
    if r.returncode != 0:
        raise SingleTakeProbeError("ffmpeg_or_ffprobe_failed")
    return r


def frame_at(movie: Path, t: float, width: int, height: int):
    from PIL import Image
    cw, ch = crop_native(width, height)
    vf = f"crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})/2,scale={WIDTH}:{HEIGHT}:flags=lanczos"
    r = run_cmd(["ffmpeg", "-nostdin", "-v", "error",
                 "-ss", f"{t:.3f}", "-i", str(movie), "-an", "-frames:v", "1",
                 "-vf", vf, "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"], 55)
    if len(r.stdout) != WIDTH * HEIGHT * 3:
        raise SingleTakeProbeError("frame_decode_bad_size")
    return Image.frombytes("RGB", (WIDTH, HEIGHT), r.stdout)


def build_contact(rows, dest: Path) -> dict:
    from PIL import Image, ImageDraw, ImageStat, ImageChops
    if not 1 <= len(rows) <= len(ALLOWED):
        raise SingleTakeProbeError("candidate_rows_missing")
    sheet = Image.new("RGB", (WIDTH * 3, len(rows) * (HEIGHT + 46)), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    measurements = {}
    for rowno, (ident, frames) in enumerate(rows):
        if len(frames) != len(SAMPLE_TIMES):
            raise SingleTakeProbeError("frame_count_invalid")
        seq = []
        for col, im in enumerate(frames):
            sheet.paste(im, (col * WIDTH, rowno * (HEIGHT + 46)))
            luma = ImageStat.Stat(im.convert("L"))
            seq.append(round(luma.mean[0], 2))
            draw.rectangle((col*WIDTH+2, rowno*(HEIGHT+46)+2,
                            col*WIDTH+72, rowno*(HEIGHT+46)+24), fill=(10,10,10))
            draw.text((col*WIDTH+6, rowno*(HEIGHT+46)+7),
                      f"{SAMPLE_TIMES[col]:.1f}s", fill=(240,240,240))
        drift = []
        for a,b in zip(frames,frames[1:]):
            diff = ImageChops.difference(a,b).convert("L")
            drift.append(round(ImageStat.Stat(diff).mean[0],2))
        measurements[str(ident)]={"luma_means":seq,"frame_difference":drift,
                                  "frame_samples":3,"human_visual_review":False}
        draw.rectangle((0, (rowno+1)*(HEIGHT+46)-46,
                        3*WIDTH, (rowno+1)*(HEIGHT+46)), fill=(18,18,18))
        draw.text((8, (rowno+1)*(HEIGHT+46)-31),
                  f"Pexels {ident} | PREVIA EM QUARENTENA | NAO PUBLICAR",
                  fill=(245,245,245))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=78, format="JPEG")
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    return {"path":dest.name,"sha256":digest,"width":sheet.width,
            "height":sheet.height,"frames_per_candidate":3,
            "file_bytes":dest.stat().st_size,"measurements":measurements}


def run(root: Path, output: Path) -> tuple[int, dict]:
    output.mkdir(parents=True, exist_ok=True)
    report = {"project":"VERBO_NO_CHAO_EXCLUSIVO","scene":"VNC-E01V2-S01",
              "status":"BLOCKED_NO_NEW_MEDIA_QA","rights_cleared":False,
              "editorial_approved":False,"master_allowed":False,
              "publication_authorized":False,"preview_only":True,
              "new_master_created":False,"clips":[]}
    rows=[]
    current_video_id=None
    try:
        candidates=validate_plan(root)
        with tempfile.TemporaryDirectory(prefix="vnc_s01_single_take_") as folder:
            work = Path(folder)
            for item in candidates:
                current_video_id=item["video_id"]
                movie, meta = download_source({
                    "id":item["video_id"],"page":item["page_url"]
                }, work)
                p=probe(movie,min_seconds=WINDOW,min_width=1080,min_height=1920)
                cw,ch = crop_native(p["width"],p["height"])
                # Full physical decode. No generated movie, no synthetic motion.
                run_cmd(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(movie),
                         "-map","0:v:0","-an","-f","null","-"],180)
                frames=[frame_at(movie,t,p["width"],p["height"]) for t in SAMPLE_TIMES]
                rows.append((item["video_id"],frames))
                report["clips"].append({
                    **meta, **p,"native_portrait_crop_width":cw,
                    "native_portrait_crop_height":ch,
                    "physically_decoded_entire_mp4":True,
                    "source_license_claim":"Pexels Free page; third party pending",
                    "recognized_actor_or_brand_review":False,
                    "editorial_suitability_review":False,
                    "not_assumed_same_person_as_prior_sources":True,
                })
                movie.unlink(missing_ok=True)
            report["contact_sheet"]=build_contact(rows,output/"S01_SINGLE_TAKE_V2_QA.jpg")
            report["status"]="PHYSICAL_SINGLE_TAKE_CANDIDATES_READY_FOR_HUMAN_FRAME_REVIEW_ONLY"
    except Exception as exc:
        # Fail closed even if one source is unavailable; retain verified frames
        # for internal review without ever promoting a partial source set.
        report["error_type"]=type(exc).__name__
        if current_video_id is not None:
            report["failed_source_video_id"]=current_video_id
        detail=str(exc)
        report["error_code"]=(
            detail if detail and len(detail) <= 85 and all(
                c.isalnum() or c in "_- :." for c in detail
            ) else "provider_or_decode_error"
        )
        if rows:
            try:
                report["contact_sheet"]=build_contact(
                    rows,output/"S01_SINGLE_TAKE_V2_QA.jpg"
                )
                report["status"]="BLOCKED_PARTIAL_PHYSICAL_QA_EDITORIAL_RIGHTS_PENDING"
            except Exception:
                report["status"]="BLOCKED_NO_NEW_MEDIA_QA"
                (output/"S01_SINGLE_TAKE_V2_QA.jpg").unlink(missing_ok=True)
        else:
            report["status"]="BLOCKED_NO_NEW_MEDIA_QA"
            (output/"S01_SINGLE_TAKE_V2_QA.jpg").unlink(missing_ok=True)
    (output/"S01_SINGLE_TAKE_V2_REPORT.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"candidates_checked":len(report["clips"]),
                      "master_allowed":report["master_allowed"],
                      "rights_cleared":report["rights_cleared"],
                      "error_type":report.get("error_type")}))
    return (0 if report["status"].startswith("PHYSICAL_") else 2),report


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,default=Path("artifacts/vnc_s01_single_take"))
    args=ap.parse_args()
    return run(ROOT,args.out)[0]


if __name__=="__main__":
    raise SystemExit(main())
