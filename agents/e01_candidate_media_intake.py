"""Fail-closed first-party E01 video-byte intake. Never releases assets."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from agents.e01_stock_candidates import ROOT, StockIntakeError, require
from agents.e01_visual_single_world_gate import validate as verify_world

POLICY=Path("contracts/e01_v2_media_intake_policy_v1.json")
STORY=Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
ORIGINS={"camera_original","ai_generated_video","stock_licensed_candidate"}
MAX_BYTES=314572800

def verify_policy(root=ROOT):
    policy=json.loads((root/POLICY).read_text(encoding="utf-8"))
    require(policy.get("schema_version")=="1.0.0"
      and policy.get("project")=="verbo-no-chao"
      and policy.get("episode_id")=="VNC-W01-E1"
      and policy.get("candidate_version")==2
      and policy.get("source_storyboard")==str(STORY)
      and policy.get("source_continuity_blueprint")==
         "contracts/e01_v2_visual_single_world_acquisition_v1.json"
      and policy.get("state")=="TECHNICAL_INPUT_ONLY_NOT_RELEASE"
      and set(policy.get("origins",[]))==ORIGINS
      and policy.get("max_bytes")==MAX_BYTES
      and policy.get("expected_vertical_ratio")=="9:16"
      and policy.get("target_native_resolution")==[1080,1920]
      and policy.get("rights_review_completed") is False
      and policy.get("continuity_review_completed") is False
      and policy.get("user_publication_approval") is False
      and policy.get("persist_video_in_public_github") is False
      and policy.get("reusable_license_assumed") is False,
      "media_intake:unsafe_policy")
    verify_world(root)
    return policy

def _ffprobe(path:Path,binary="ffprobe"):
    command=[binary,"-v","error","-select_streams","v:0",
      "-show_entries","stream=codec_name,codec_type,width,height,avg_frame_rate,duration:format=duration",
      "-of","json",str(path)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=45,check=False)
    require(result.returncode==0,"media_intake:ffprobe_error")
    payload=json.loads(result.stdout)
    streams=payload.get("streams",[])
    require(isinstance(streams,list) and len(streams)==1
            and streams[0].get("codec_type")=="video",
            "media_intake:no_video_track")
    s=streams[0]
    duration=float(s.get("duration") or payload.get("format",{}).get("duration") or "nan")
    w,h=int(s["width"]),int(s["height"])
    fps_string=s.get("avg_frame_rate","")
    require(re.fullmatch(r"[0-9]+/[1-9][0-9]*",fps_string) is not None,
            "media_intake:fps_format")
    num,den=map(int,fps_string.split("/"))
    fps=num/den
    require(s.get("codec_name") in {"h264","hevc","av1","vp9","prores"}
            and duration>0 and duration<=180 and 8<=fps<=120
            and w>=360 and h>=640 and abs(w/h-9/16)<0.02,
            "media_intake:unusable_geometry_codec_or_duration")
    return {"codec":s["codec_name"],"width":w,"height":h,
            "fps":round(fps,4),"duration_seconds":round(duration,4)}

def inspect(video:Path,scene_id:str,origin:str,root=ROOT,
            ffprobe="ffprobe",ffmpeg="ffmpeg"):
    verify_policy(root)
    story=json.loads((root/STORY).read_text(encoding="utf-8"))
    scenes=[x for x in story["scenes"] if x["id"]==scene_id]
    require(origin in ORIGINS and len(scenes)==1,
            "media_intake:bad_origin_or_scene")
    path=Path(video)
    require(path.is_file() and not path.is_symlink()
            and path.suffix.lower() in {".mp4",".mov"}
            and 10000<=path.stat().st_size<=MAX_BYTES,
            "media_intake:file_absent_or_invalid")
    before=path.stat()
    meta=_ffprobe(path,ffprobe)
    outcome=subprocess.run([ffmpeg,"-nostdin","-v","error","-xerror",
       "-i",str(path),"-map","0:v:0","-an","-f","null","-"],
       capture_output=True,text=True,timeout=240,check=False)
    require(outcome.returncode==0,"media_intake:video_decode_failed")
    assert_unchanged=lambda: require(
        path.stat().st_size==before.st_size and
        path.stat().st_mtime_ns==before.st_mtime_ns,
        "media_intake:file_modified_during_probe")
    assert_unchanged()
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1048576),b""):
            digest.update(chunk)
    assert_unchanged()
    sc=scenes[0]
    length=round(sc["end_seconds"]-sc["start_seconds"],4)
    duration_ok=meta["duration_seconds"]+0.025>=length
    enough_native=meta["width"]>=1080 and meta["height"]>=1920
    return {
     "status":"VIDEO_BYTES_VERIFIED_NO_RIGHTS_RELEASE",
     "episode_id":"VNC-W01-E1","scene_id":scene_id,
     "media_origin":origin,
     "origin_proven_by_codec":False,
     "sha256":digest.hexdigest(),"bytes":before.st_size,
     "full_video_decode_completed":True,
     "technical_metrics":meta,"scene_duration_seconds":length,
     "scene_length_covered":duration_ok,"native_resolution_sufficient":enough_native,
     "preview_only":not(duration_ok and enough_native),
     "filmed_in_real_world_claimed":origin=="camera_original",
     "ai_motion_video_claimed":origin=="ai_generated_video",
     "visual_continuity_verified":False,"third_party_rights_cleared":False,
     "license_verified":False,"caption_safe_zone_verified":False,
     "final_master_rendered":False,"approved_for_master":False,
     "publication_authorized":False,"raw_file_uploaded":False
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video",required=True,type=Path)
    parser.add_argument("--scene-id",required=True)
    parser.add_argument("--origin",required=True,choices=sorted(ORIGINS))
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--root",type=Path,default=ROOT)
    a=parser.parse_args()
    try:
        report=inspect(a.video,a.scene_id,a.origin,a.root)
        code=0
    except (StockIntakeError,OSError,ValueError,KeyError,TypeError,
            json.JSONDecodeError,subprocess.TimeoutExpired) as exc:
        report={"status":"BLOCKED_VIDEO_INTAKE",
                "error_type":type(exc).__name__,
                "approved_for_master":False,
                "publication_authorized":False}
        code=2
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                     encoding="utf-8")
    print(json.dumps({"status":report["status"],
                      "publication_authorized":False,
                      "evidence_json":str(a.out)}))
    return code

if __name__=="__main__":
    raise SystemExit(main())
