"""One-shot S03 public-footage QA. No browser/login/provider/production approvals.

Designed for a temporary GitHub Actions runner; never writes video into the repo.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

SCENE="VNC-E01V2-S03"
SOURCE_ID=40316686
SOURCE_URL="https://www.pexels.com/video/quiet-residential-street-at-dusk-40316686/"
SOURCE_FILE_URL="https://videos.pexels.com/video-files/40316686/17221948_1080_1920_60fps.mp4"
SCENE_DURATION=6.14
ALLOWED_BYTES=50_000_000


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def tool(*args: str, timeout: int=60) -> subprocess.CompletedProcess:
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False)


def run(video: Path, output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    report={
        "project":"verbo-no-chao",
        "episode_id":"VNC-W01-E1",
        "scene_id":SCENE,
        "scene_duration_seconds":SCENE_DURATION,
        "source_platform":"Pexels",
        "source_id":SOURCE_ID,
        "source_page":SOURCE_URL,
        "source_download_url":SOURCE_FILE_URL,
        "origin":"PUBLIC_THIRD_PARTY_STOCK_CANDIDATE",
        "editorial_brief":"Neglected residential public space after rain; no identifiable victims or allegations",
        "technical_status":"BLOCKED_NOT_TESTED",
        "visual_edit_review":"PENDING",
        "source_license_terms_review":"PENDING_PER_ASSET_AND_CONTEXT",
        "commercial_rights_cleared":False,
        "editorial_approved":False,
        "can_enter_master":False,
        "publication_authorized":False,
        "external_model_calls":0,
        "note":"Physical probe and source hash cannot establish story fidelity or third-party rights.",
    }
    try:
        if not video.is_file() or video.stat().st_size<100000 or video.stat().st_size>ALLOWED_BYTES:
            raise ValueError("missing_or_out_of_bounds_source_bytes")
        report["source_file_bytes"]=video.stat().st_size
        report["source_sha256"]=sha256(video)
        probe=tool("ffprobe","-v","error","-show_entries",
                   "format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate",
                   "-of","json",str(video),timeout=30)
        if probe.returncode:
            raise ValueError("ffprobe_failed:"+probe.stderr[-160:])
        media=json.loads(probe.stdout)
        stream=next((s for s in media.get("streams",[]) if s.get("codec_type")=="video"),None)
        if not stream: raise ValueError("no_video_stream")
        duration=float(media["format"]["duration"])
        fpsstring=stream.get("avg_frame_rate","0/1")
        num,den=(float(x) for x in fpsstring.split("/"))
        fps=num/den if den else 0
        report["physical"]={"duration_seconds":duration,"width":stream.get("width"),
            "height":stream.get("height"),"fps":fps,"codec":stream.get("codec_name"),
            "seconds_required":SCENE_DURATION,"full_stream_decode":False}
        if not math.isfinite(duration) or duration<SCENE_DURATION:
            raise ValueError("real_clip_too_short")
        if (stream.get("width"),stream.get("height"))!=(1080,1920):
            raise ValueError("wrong_native_resolution")
        if not math.isfinite(fps) or fps<29.9:
            raise ValueError("source_fps_too_low")
        decode=tool("ffmpeg","-nostdin","-v","error","-xerror",
                    "-i",str(video),"-map","0:v:0","-f","null","-",timeout=150)
        if decode.returncode:
            raise ValueError("full_video_decode_failed:"+decode.stderr[-160:])
        report["physical"]["full_stream_decode"]=True
        sheet=output/"S03_SIX_FRAME_CONTACT_SHEET.jpg"
        montage=tool("ffmpeg","-nostdin","-y","-v","error","-xerror","-i",str(video),
                     "-t","6.14","-vf","fps=1,scale=270:480:flags=lanczos,tile=3x2",
                     "-frames:v","1",str(sheet),timeout=70)
        if montage.returncode or not sheet.is_file(): raise ValueError("contact_sheet_failed")
        preview=output/"S03_540x960_30FPS_QA_ONLY.mp4"
        proxy=tool("ffmpeg","-nostdin","-y","-v","error","-xerror","-i",str(video),
                   "-t","6.14","-an","-vf","fps=30,scale=540:960:flags=lanczos",
                   "-c:v","libx264","-preset","veryfast","-crf","25",
                   "-pix_fmt","yuv420p","-movflags","+faststart",str(preview),timeout=150)
        if proxy.returncode or not preview.is_file(): raise ValueError("qa_proxy_failed")
        report["qa_assets"]={
            "contact_sheet":{"file":sheet.name,"sha256":sha256(sheet)},
            "low_res_technical_proxy":{"file":preview.name,"sha256":sha256(preview),
                                       "is_master":False}
        }
        report["technical_status"]="PHYSICAL_STOCK_SOURCE_VALID_FOR_EDITORIAL_VISUAL_REVIEW_ONLY"
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.TimeoutExpired) as exc:
        report["technical_status"]="BLOCKED_SOURCE_PHYSICAL_OR_DOWNLOAD"
        report["failure_type"]=type(exc).__name__
        report["failure_reason"]=str(exc)[:220]
    (output/"S03_PHYSICAL_SOURCE_QA_REPORT.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("video",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    report=run(a.video,a.output)
    print(json.dumps({k:report[k] for k in ("technical_status","editorial_approved",
          "commercial_rights_cleared","can_enter_master","publication_authorized")},
          ensure_ascii=False))
    return 0 if report["technical_status"].startswith("PHYSICAL_STOCK_SOURCE_VALID") else 2


if __name__=="__main__":
    raise SystemExit(main())
