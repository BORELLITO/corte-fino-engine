"""Rebuild nonpublishable E01v2 picture roughcut from SHA-verified Library assets.

Requires the two real private Library files supplied to Work/desktop by its
authorized file surface. GitHub Actions does not automatically possess them.
No download links, model weights, paid APIs, channel access or publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path

from agents.content_production import ProductionError,check
from agents.e01_visual_roughcut_gate import (
    manifest,package,sha256,EXACT_WAV_SHA,EXACT_ASR_ASS_SHA,
)

FPS=30
SIZE="720x1280"
EXPECTED_DURATION=70.425
OUTPUT_NAME="E01_V2_VISUAL_ROUGHCUT_NOT_FOR_PUBLICATION.mp4"


def ensure_sources(root:Path,bundle:Path,wav:Path,ass:Path) -> dict:
    proof=package(root,bundle)
    check(wav.is_file() and sha256(wav)==EXACT_WAV_SHA,
          "visual_render:wrong_immutable_voice")
    check(ass.is_file() and sha256(ass)==EXACT_ASR_ASS_SHA,
          "visual_render:wrong_immutable_captions")
    with wave.open(str(wav),"rb") as f:
        check((f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,24000)
              and abs(f.getnframes()/24000-EXPECTED_DURATION)<.001,
              "visual_render:physical_audio_shape_changed")
    return proof


def ffmpeg_command(ffmpeg:str,image:Path,dest:Path,frames:int) -> list[str]:
    check(1<=frames<=250 and image.name.startswith("E01V2_SCENE_")
          and dest.name.startswith("seg_"),"visual_render:invalid_clip_params")
    zoom="min(max(zoom,1.0)+0.00023,1.085)"
    x="(iw-iw/zoom)/2+6*sin(on/65)"
    y="(ih-ih/zoom)/2+4*cos(on/80)"
    vf=(f"zoompan=z='{zoom}':x='{x}':y='{y}'"
        ":d=1:s=720x1280:fps=30,format=yuv420p")
    return [ffmpeg,"-hide_banner","-nostdin","-loglevel","error","-y",
            "-loop","1","-framerate","30","-i",str(image),
            "-frames:v",str(frames),"-vf",vf,"-an",
            "-c:v","libx264","-preset","ultrafast","-crf","28",
            "-pix_fmt","yuv420p","-r","30",str(dest)]


def run(root:Path,bundle:Path,wav:Path,ass:Path,out:Path) -> dict:
    root=root.resolve();bundle=bundle.resolve()
    wav=wav.resolve();ass=ass.resolve();out=out.resolve()
    check(not out.is_relative_to(root/"contracts")
          and not out.is_relative_to(root/"agents")
          and not out.is_relative_to(root/"docs"),
          "visual_render:protected_output")
    proof=ensure_sources(root,bundle,wav,ass)
    e=manifest(root)
    from imageio_ffmpeg import get_ffmpeg_exe
    ffmpeg=get_ffmpeg_exe()
    out.mkdir(parents=True,exist_ok=True)
    dest=out/OUTPUT_NAME
    dest.unlink(missing_ok=True)
    report={
        "project":"verbo-no-chao","episode_id":"VNC-W01-E1",
        "candidate_version":2,
        "status":"BLOCKED_NEW_RENDER_UNVERIFIED",
        "input_package_sha256":e["source_package_sha256"],
        "source_wav_sha256":EXACT_WAV_SHA,
        "source_ass_sha256":EXACT_ASR_ASS_SHA,
        "publication_authorized":False,
        "full_1080x1920_master_approved":False,
        "commercial_licenses_cleared":False,
        "soundtrack_with_license_present":False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="vnc_e01_v2_clip_") as d:
            tmp=Path(d);clips=[]
            with zipfile.ZipFile(bundle,"r") as z:
                for shot in e["shots"]:
                    name=shot["derived_output"]
                    raw=z.read(name)
                    target=tmp/Path(name).name
                    target.write_bytes(raw)
                    check(sha256(target)==shot["sha256"],
                          "visual_render:scene_extract_sha_mismatch")
                    idx=len(clips)+1
                    count=round(shot["end_seconds"]*FPS)-round(shot["start_seconds"]*FPS)
                    clip=tmp/f"seg_{idx:02}.mp4"
                    subprocess.run(ffmpeg_command(ffmpeg,target,clip,count),
                                   check=True,capture_output=True,timeout=100)
                    clips.append(clip)
            concat=tmp/"clips.txt"
            concat.write_text("".join("file '"+str(f)+"'\n" for f in clips),encoding="utf-8")
            joined=tmp/"joined.mp4"
            subprocess.run([ffmpeg,"-hide_banner","-nostdin","-loglevel","error","-y",
                            "-f","concat","-safe","0","-i",str(concat),
                            "-c","copy",str(joined)],
                           check=True,capture_output=True,timeout=90)
            subprocess.run([ffmpeg,"-hide_banner","-nostdin","-loglevel","error","-y",
                            "-i",str(joined),"-i",str(wav),
                            "-vf",f"ass={ass}:original_size=1080x1920",
                            "-map","0:v:0","-map","1:a:0",
                            "-t",str(EXPECTED_DURATION),"-c:v","libx264",
                            "-preset","ultrafast","-crf","24",
                            "-pix_fmt","yuv420p","-r","30",
                            "-c:a","aac","-b:a","128k",
                            "-movflags","+faststart",str(dest)],
                           check=True,capture_output=True,timeout=130)
        check(dest.is_file() and dest.stat().st_size>=250000,
              "visual_render:mp4_not_created")
        # Full-stream physical decode; the output is still a temporary roughcut.
        completed=subprocess.run([ffmpeg,"-hide_banner","-nostdin","-v","error",
                                 "-i",str(dest),"-f","null","-"],
                                 check=False,capture_output=True,timeout=90)
        check(completed.returncode==0,
              "visual_render:physical_video_audio_decode_failed")
        report.update({
            "status":"LOCAL_12_SCENE_ROUGHCUT_REBUILT_DECODED_NOT_MASTER",
            "new_video_file":OUTPUT_NAME,"new_video_sha256":sha256(dest),
            "new_video_bytes":dest.stat().st_size,
            "real_physical_ffmpeg_decode_completed":True,
            "source_images_verified":proof["scene_bytes_sha_verified"],
            "visual_resolution":"720x1280",
            "camera_motion":"SYNTHETIC_PAN_ZOOM_NOT_GENERATED_VIDEO_CLIPS",
            "original_storyboard_tiles_low_resolution":True,
        })
    except Exception as exc:
        dest.unlink(missing_ok=True)
        report["status"]="BLOCKED_VISUAL_REBUILD_FAILED"
        report["error_code"]=str(exc) if isinstance(exc,ProductionError) else type(exc).__name__
    (out/"visual-roughcut-qa.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--assets-zip",type=Path,required=True)
    ap.add_argument("--wav",type=Path,required=True)
    ap.add_argument("--ass",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    result=run(args.root,args.assets_zip,args.wav,args.ass,args.output_dir)
    print(json.dumps({k:result.get(k) for k in (
        "status","new_video_sha256","real_physical_ffmpeg_decode_completed",
        "publication_authorized","error_code"
    )},ensure_ascii=False))
    return 0 if result["status"]=="LOCAL_12_SCENE_ROUGHCUT_REBUILT_DECODED_NOT_MASTER" else 2


if __name__=="__main__":
    raise SystemExit(main())
