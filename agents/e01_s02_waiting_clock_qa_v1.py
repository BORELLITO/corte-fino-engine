"""S02: physical stock clock review, single-source motion video. NEVER a master.

Reuses proven Pexels safe downloader, native portrait cropping, FFmpeg full
decode and QA watermark. The S01 artistic approval does not approve S02.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path


from agents.e01_s01_multi_stock_pilot_v1 import download_source, probe
from agents.e01_s01_single_take_stock_qa import crop_native, frame_at, run_cmd
from agents.e01_s01_night_rain_motif_probe_v1 import watermark
from agents.e01_stock_candidates import ROOT

CONTRACT = Path("contracts/e01_s02_waiting_clock_stock_preflight_20261119_v1.json")
APPROVAL = Path("contracts/e01_s01_owner_visual_approval_20261119_v1.json")
SOURCE_ID = 7034348
PAGE = "https://www.pexels.com/video/clock-is-ticking-7034348/"
FRAMES = 147
FPS = 30
W, H = 720, 1280
SAMPLES = (0.5, 2.4, 4.5)
ACCEPTED_S01_SHA = "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961"

class S02StockGateError(ValueError):
    pass


def validate(root=ROOT, data=None):
    root = Path(root)
    if data is None:
        data = json.loads((root / CONTRACT).read_text(encoding="utf8"))
    if not isinstance(data, dict):
        raise S02StockGateError("manifest_not_object")
    checks = {
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id":"VNC-W01-E1",
        "scene_id":"VNC-E01V2-S02",
        "purpose":"S02_REAL_STOCK_CLOCK_REVIEW_ONLY",
        "editorial_approved":False,
        "owner_approved_for_s02":False,
        "rights_cleared":False,
        "s01_reference_modified":False,
        "master_allowed":False,
        "publication_authorized":False,
        "spending_authorized":False,
        "source_original_persisted":False,
        "result_state":"RESEARCH_AWAITING_PHYSICAL_FRAMES"
    }
    for k,v in checks.items():
        if type(data.get(k)) is not type(v) or data[k] != v:
            raise S02StockGateError("release_or_identity_invariant_"+k)
    source = data.get("source")
    if (not isinstance(source, dict) or source.get("video_id") != SOURCE_ID
        or type(source.get("video_id")) is not int
        or source.get("page_url") != PAGE
        or source.get("license_label") != "Free"
        or source.get("physical_source_acquired") is not False
        or source.get("source_sha256") is not None
        or source.get("third_party_rights_clearance") is not False
        or source.get("scene_specific_release_cleared") is not False):
        raise S02StockGateError("untrusted_source_or_rights")
    preview = data.get("output_preview")
    if not isinstance(preview,dict) or any(
        type(preview.get(k)) is not type(v) or preview[k] != v for k,v in {
            "width":W,"height":H,"fps":FPS,"frames":FRAMES,
            "watermark":"PREVIA DE QA - NAO PUBLICAR","audio":False,
            "captions":False
        }.items()):
        raise S02StockGateError("preview_falsified")
    timeline = data.get("cut_frame_plan_30fps") or {}
    if timeline != {
        "s01_last_exclusive":172, "s02_last_exclusive":319,
        "s02_frames":147, "s02_preview_duration_seconds":4.9
    }:
        raise S02StockGateError("timeline_30fps_mismatch")
    first = data.get("previous_scene") or {}
    owner = json.loads((root / APPROVAL).read_text(encoding="utf8"))
    if (first.get("approved_preview_sha256") != ACCEPTED_S01_SHA
        or first.get("s01_visual_approved") is not True
        or owner.get("approval_scope",{}).get("preview_sha256") != ACCEPTED_S01_SHA
        or owner.get("approval_status") != "APPROVED_S01_VISUAL_DIRECTION_ONLY"
        or owner.get("approval_scope",{}).get("extend_to_other_scenes_automatically") is not False):
        raise S02StockGateError("s01_owner_approval_not_scoped")
    return source


def contact_sheet(frames, path):
    from PIL import Image, ImageDraw, ImageStat, ImageChops
    if len(frames) != 3 or any(im.size != (216,384) for im in frames):
        raise S02StockGateError("invalid_sample_geometry")
    sheet=Image.new("RGB",(648,426),(20,20,22))
    draw=ImageDraw.Draw(sheet)
    vals,drifts=[],[]
    for i,im in enumerate(frames):
        sheet.paste(im,(i*216,0))
        vals.append(round(ImageStat.Stat(im.convert("L")).mean[0],2))
        draw.rectangle((i*216+2,4,i*216+87,24),fill=(10,10,10))
        draw.text((i*216+7,8),f"{SAMPLES[i]:.1f}s",fill=(255,255,255))
    for a,b in zip(frames,frames[1:]):
        drifts.append(round(ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0],2))
    draw.text((8,397),"S02 CLOCK - QA PREVIA - NAO PUBLICAR",fill=(250,250,250))
    sheet.save(path,format="JPEG",quality=80)
    return {"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "filename":path.name,"samples_s":list(SAMPLES),
            "luma_means":vals,"frame_differences":drifts,
            "human_editorial_approval":False}


def render(src:Path,overlay:Path,dst:Path,width:int,height:int):
    cw,ch=crop_native(width,height)
    filt=(
        f"[0:v]fps={FPS},crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})/2,"
        f"scale={W}:{H}:flags=lanczos,setsar=1[scene];"
        "[scene][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,"
        "format=yuv420p[v]"
    )
    run_cmd(["ffmpeg","-nostdin","-v","error","-y","-i",str(src),
             "-loop","1","-i",str(overlay),"-filter_complex",filt,
             "-map","[v]","-an","-frames:v",str(FRAMES),"-r",str(FPS),
             "-c:v","libx264","-preset","veryfast","-crf","24",
             "-movflags","+faststart",str(dst)],160)
    p=probe(dst,min_seconds=4.85,min_width=W,min_height=H)
    if p["width"]!=W or p["height"]!=H or abs(p["duration_seconds"]-FRAMES/FPS)>0.04:
        raise S02StockGateError("preview_duration_or_geometry_invalid")
    run_cmd(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(dst),
             "-map","0:v:0","-an","-f","null","-"],80)
    return p


def run(out:Path,root=ROOT):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    result={
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO","scene_id":"VNC-E01V2-S02",
        "status":"BLOCKED_NO_S02_PREVIEW","source_id":SOURCE_ID,
        "s01_approved_visual_preserved":True,
        "s02_visual_approved":False,"rights_cleared":False,
        "master_allowed":False,"publication_authorized":False,
        "source_mp4_stored":False,"voice_added":False,"captions_added":False
    }
    movie_out=out/"S02_WAITING_CLOCK_QA_NOT_MASTER.mp4"
    still_out=out/"S02_CLOCK_REAL_FRAMES_QA.jpg"
    try:
        validate(root)
        with tempfile.TemporaryDirectory(prefix="vnc_s02_clock_") as folder:
            temp=Path(folder)
            clip,metadata=download_source({"id":SOURCE_ID,"page":PAGE},temp)
            p=probe(clip,min_seconds=4.88,min_width=1080,min_height=1920)
            crop_native(p["width"],p["height"])
            run_cmd(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(clip),
                     "-map","0:v:0","-an","-f","null","-"],210)
            frames=[frame_at(clip,t,p["width"],p["height"]) for t in SAMPLES]
            frames_meta=contact_sheet(frames,still_out)
            watermark(temp/"overlay.png")
            preview_meta=render(clip,temp/"overlay.png",movie_out,p["width"],p["height"])
            result.update(status="S02_REAL_STOCK_PREVIEW_PHYSICALLY_VERIFIED_ART_RIGHTS_PENDING",
                 source={**metadata,**p,"complete_source_decode":True},
                 contact_sheet=frames_meta,
                 output={**preview_meta,"filename":movie_out.name,
                        "sha256":hashlib.sha256(movie_out.read_bytes()).hexdigest(),
                        "bytes":movie_out.stat().st_size,"frames":FRAMES,
                        "fps":FPS,"full_decode_pass":True,"audio":False,
                        "watermarked":True})
            clip.unlink(missing_ok=True)
    except Exception as exc:
        movie_out.unlink(missing_ok=True)
        still_out.unlink(missing_ok=True)
        result["status"]="BLOCKED_NO_S02_PREVIEW"
        result["error_type"]=type(exc).__name__
        result["error_code"]=str(exc) if isinstance(exc,S02StockGateError) else "provider_or_decode_error"
    (out/"S02_CLOCK_PHYSICAL_QA_REPORT.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8"
    )
    print(json.dumps({"status":result["status"],"master_allowed":False,
                      "source_id":SOURCE_ID,"error":result.get("error_type")}))
    return 0 if result["status"].startswith("S02_REAL_STOCK_PREVIEW") else 2


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    raise SystemExit(run(parser.parse_args().out))
