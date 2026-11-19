"""Read-only 4K Pexels source inspection for S04, never a master or release.

This is a separate public-stock candidate, not an alternative LTX/Wan GPU request.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path
from agents.e01_s04_pexels_7977614_physical_qa import digest, execute

VIDEO_ID = 11137423
SOURCE = "https://www.pexels.com/video/close-up-on-writing-with-ink-pen-11137423/"
DOWNLOAD = "https://videos.pexels.com/video-files/11137423/11137423-hd_3840_2160_25fps.mp4"
SCENE = "VNC-E01V2-S04"
SECONDS = 5.82

def inspect(source: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "scene":SCENE,"episode":"VNC-W01-E1","project":"VERBO_NO_CHAO_EXCLUSIVO",
        "source_id": VIDEO_ID, "source_page":SOURCE,"source_download":DOWNLOAD,
        "source_author":"emirkhan bal (Pexels)",
        "required_seconds":SECONDS,
        "source_description":"Close-up of hand writing with ink pen by candlelight.",
        "risk":"Written marks and modern metal pen may violate blank parchment/reed pen.",
        "technical_status":"BLOCKED_NOT_VALIDATED",
        "rights_cleared":False,"editorial_approved":False,
        "allowed_in_master":False,"publication_authorized":False,
        "whole_video_decoded":False,"generation_requests":0,
    }
    try:
        if not source.is_file() or not 100000 < source.stat().st_size < 250000000:
            raise ValueError("missing_or_oversized_source")
        report["source_sha256"]=digest(source)
        report["source_bytes"]=source.stat().st_size
        from portable_ffmpeg import get_ffmpeg
        ffmpeg,ffprobe=get_ffmpeg()
        probe=execute([str(ffprobe),"-v","error","-show_entries",
                       "format=duration:stream=codec_type,width,height,avg_frame_rate",
                       "-of","json",str(source)],timeout=40)
        if probe.returncode:
            raise ValueError("invalid_source_probe")
        meta=json.loads(probe.stdout)
        v=next((s for s in meta.get("streams",[]) if s.get("codec_type")=="video"),None)
        if not v:
            raise ValueError("no_video_stream")
        w,h=v.get("width"),v.get("height")
        total=float(meta["format"]["duration"])
        num,den=(float(x) for x in v.get("avg_frame_rate","0/1").split("/"))
        fps=num/den if den else 0.
        if type(w) is not int or type(h) is not int or w < 3840 or h < 2160:
            raise ValueError("expected_4k_unmodified_source")
        if total < 2*SECONDS or not math.isfinite(total) or fps < 24:
            raise ValueError("insufficient_video_duration_or_fps")
        report["physical"]={"duration":total,"width":w,"height":h,"fps":fps}
        crop_w=int((h*9/16)//2*2)
        if crop_w < 1080: raise ValueError("vertical_crop_below_native_master")
        report["portrait_crop"]={"native_width":crop_w,"native_height":h,
                                 "center_x":(w-crop_w)//2,"sufficient_native_resolution":True}
        dec=execute([str(ffmpeg),"-nostdin","-v","error","-xerror","-i",str(source),
                     "-map","0:v:0","-f","null","-"],timeout=160)
        if dec.returncode: raise ValueError("full_video_decode_failed")
        report["whole_video_decoded"]=True
        for window,start in enumerate((0.,SECONDS),start=1):
            name=f"S04_11137423_CENTER_CROP_WINDOW_{window}.jpg"
            path=out/name
            vf=f"crop={crop_w}:{h}:(iw-{crop_w})/2:0,fps=1,scale=270:480:flags=lanczos,tile=3x2"
            c=execute([str(ffmpeg),"-nostdin","-y","-v","error",
                       "-ss",str(start),"-i",str(source),"-t",str(SECONDS),
                       "-vf",vf,"-frames:v","1",str(path)],timeout=90)
            if c.returncode or not path.is_file() or path.stat().st_size < 1000:
                raise ValueError("portrait_contact_sheet_failed")
            report[f"portrait_grid_{window}_sha256"]=digest(path)
        # Look at original landscape composition before deciding alternative crop.
        wide=out/"S04_11137423_ORIGINAL_WIDE_CONTEXT.jpg"
        c=execute([str(ffmpeg),"-nostdin","-y","-v","error","-i",str(source),
                   "-t","8","-vf","fps=1,scale=480:270:flags=lanczos,tile=4x2",
                   "-frames:v","1",str(wide)],timeout=90)
        if c.returncode or not wide.is_file():
            raise ValueError("wide_context_sheet_failed")
        report["wide_context_grid_sha256"]=digest(wide)
        report["technical_status"]="PASS_PHYSICAL_4K_WAIT_EDITORIAL_AND_RIGHTS"
    except (ValueError,OSError,TypeError,KeyError,ImportError,subprocess.TimeoutExpired) as e:
        report["technical_status"]="BLOCKED_SOURCE_OR_DECODE"
        report["error"]={"kind":type(e).__name__,"description":str(e)[:200]}
    (out/"S04_11137423_QA_REPORT.json").write_text(
         json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path);ap.add_argument("out",type=Path)
    opts=ap.parse_args()
    r=inspect(opts.source,opts.out)
    print(json.dumps({"status":r["technical_status"],"source_sha256":r.get("source_sha256"),"rights_cleared":False,"master":False}))
    raise SystemExit(0 if r["technical_status"].startswith("PASS_PHYSICAL") else 2)
