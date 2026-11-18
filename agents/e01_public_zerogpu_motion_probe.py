"""Proof of concept only: test anonymous free Wan 2.2 ZeroGPU API from CI.

This is a short AI-generated motion test, NOT an E01 scene or authorized master.
No tokens, subscription, credentials, private source, or customer media are used.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

OUT=Path("artifacts/e01_zerogpu_smoke")
OUT.mkdir(parents=True,exist_ok=True)
REPORT=OUT/"technical_proof.json"
SPACE="OpenKing/wan2-video-generation"
PROMPT=(
  "One-second original moving video, portrait frame. A faceless anonymous adult "
  "seen only from behind, wearing charcoal jacket, seated quietly by a dark "
  "rain-streaked window beside a worn wooden desk with a closed notebook. "
  "Soft warm amber lamp, quiet contemplative realism, visible slow movement "
  "of raindrops and breathing, realistic hands, subtle camera move, 35mm film "
  "look, no text or logos, no religious symbols, no dialogue, no cuts."
)
BASE={
 "project":"verbo-no-chao","episode_id":"VNC-W01-E1",
 "scene_id":"VNC-E01V2-S01","mode":"EXPERIMENTAL_ANONYMOUS_FREE_ZEROGPU",
 "model":"Wan-AI/Wan2.2-TI2V-5B-Diffusers",
 "model_license":"Apache-2.0","space":SPACE,
 "original_scene_length_seconds":5.74,
 "experimental_target_seconds":1.04,
 "generation_source":"AI_GENERATED_VIDEO",
 "target_width":576,"target_height":1024,"target_frames":25,
 "account_login_required_by_us":False,
 "payment_authorized":False,"expenses_incurred_confirmed":False,
 "real_person_depicted_confirmed":False,
 "license_for_publication_cleared":False,
 "scene_complete":False,"master_rendered":False,
 "publication_authorized":False,"approved_for_master":False
}
def report(state,extra=None):
 p=dict(BASE,status=state)
 p.update(extra or {})
 REPORT.write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":state,"space":SPACE,"publication_authorized":False,
       "scene_complete":False,"output":str(REPORT)},ensure_ascii=False),flush=True)

def main():
 report("TEST_IN_PROGRESS")
 try:
  from gradio_client import Client
  client=Client(SPACE,verbose=False)
  # Space owner documents eight inputs in app.py; this is T2V, no uploaded image.
  payload=client.predict(PROMPT,None,576,1024,25,20,5.0,12345,
                         api_name="/generate_video")
  if isinstance(payload,(tuple,list)):
   candidate=payload[0]
   note=str(payload[1])[:200] if len(payload)>1 else ""
  else:
   candidate=payload
   note=""
  if isinstance(candidate,dict):
   candidate=candidate.get("video") or candidate.get("path") or candidate.get("name")
  if not isinstance(candidate,str):
   raise RuntimeError("no_video_file_returned")
  path=Path(candidate)
  if not path.is_file() or path.stat().st_size<10000:
   raise RuntimeError("no_valid_media_bytes")
  dest=OUT/"wan22_S01_motion_probe_AI_NOT_MASTER.mp4"
  shutil.copyfile(path,dest)
  digest=hashlib.sha256(dest.read_bytes()).hexdigest()
  cmd=["ffprobe","-v","error","-select_streams","v:0",
       "-show_entries","stream=codec_name,width,height,avg_frame_rate,duration:format=duration",
       "-of","json",str(dest)]
  res=subprocess.run(cmd,capture_output=True,text=True,timeout=20,check=False)
  if res.returncode!=0:
   raise RuntimeError("ffprobe_failed")
  probe=json.loads(res.stdout)
  streams=probe.get("streams") or []
  if not streams:
   raise RuntimeError("no_video_track")
  stream=streams[0]
  dec=subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
          "-i",str(dest),"-map","0:v:0","-an","-f","null","-"],
          capture_output=True,text=True,timeout=100,check=False)
  if dec.returncode!=0:
   raise RuntimeError("full_decode_failed")
  report("AI_VIDEO_BYTES_PROVEN_ONLY",{
   "note":note,"bytes":dest.stat().st_size,"sha256":digest,
   "dimensions":[stream.get("width"),stream.get("height")],
   "codec":stream.get("codec_name"),
   "duration_seconds":float(stream.get("duration") or probe.get("format",{}).get("duration") or "0"),
   "fps":stream.get("avg_frame_rate"),
   "fully_decoded":True,
   "video_name":dest.name,"native_1080x1920":False,
   "copyright_and_continuity_editorial_review_completed":False
  })
  return 0
 except Exception as error:
  # Keep source failure diagnostic, never persist secret tokens or URLs.
  report("BLOCKED_FREE_GPU_EXECUTION",{
     "error_type":type(error).__name__,
     "reason":"anonymous_public_space_quota_or_runtime_failure",
     "detail":str(error)[:240].replace("\n"," ")
  })
  return 2

if __name__=="__main__":
 raise SystemExit(main())
