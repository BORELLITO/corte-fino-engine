"""One bounded no-login LTX-2.3 E01 S01 full-duration **candidate**.

One generator call only. 5.8s input -> 145 frames, ~6.04s at 24fps.
Physical video verification must never grant publication rights.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

SPACE = "Lightricks/LTX-2-3"
SPACE_API = "https://huggingface.co/api/spaces/Lightricks/LTX-2-3"
OUT = Path("artifacts/e01_ltx23_s01_v2")
REPORT = OUT / "report.json"
REQUEST_SECONDS = 5.8
SCENE_SECONDS = 5.74
WIDTH, HEIGHT = 480, 848
SEED = 42251
FRAME_RATE = 24
EXPECTED_FRAMES = math.ceil(math.floor(REQUEST_SECONDS * FRAME_RATE) / 8) * 8 + 1
PROMPT = (
 "Single uninterrupted cinematic live-action-style moving shot, exactly six seconds, "
 "portrait 9:16, original fictional scene. Interior: a modest lived-in Brazilian "
 "apartment room at night, a rain-covered window occupying the upper left of the "
 "composition, warm low amber tungsten lamp; soft charcoal-blue shadows and a "
 "worn dark wooden desk. ONE anonymous adult in a plain, texture-rich dark charcoal "
 "jacket, their face NEVER visible, viewed strictly from behind and seated beside "
 "the window. Their natural hands rest thoughtfully on the table. ON THE TABLE is "
 "ONE SMALL CLOSED dark notebook, with cover visibly shut and no pages or writing "
 "visible, throughout the entire shot. The notebook NEVER OPENS. No other books. "
 "Make many distinct large raindrops clearly slide down the window glass at "
 "different speeds, illuminated by weak city light outside, unmistakably rainy "
 "but without lightning. A tiny natural shoulder-breathing motion and barely "
 "noticeable hand shift occur while camera moves in a single gentle continuous "
 "slow push-in; real evolving light/reflections and natural motion parallax. "
 "35mm film cinematography with natural anatomy, convincing wood and jacket "
 "textures, restraint and documentary-like plausibility. Keep the lower 22 "
 "percent empty and dark for later Portuguese subtitles, no text rendered. "
 "One camera take without cuts, no pans to a face, no mouth, no titles, no "
 "visible words, no logos, no fantasy, no supernatural imagery, no spectacle, "
 "no transition or slideshow. DO NOT create narration or dialogue."
)
STATUS_BASE = {
 "project":"verbo-no-chao",
 "episode_id":"VNC-W01-E1",
 "scene_id":"VNC-E01V2-S01",
 "provider":SPACE,
 "media_origin":"AI_GENERATED_FICTIONAL_VIDEO",
 "request_duration_seconds":REQUEST_SECONDS,
 "required_scene_duration_seconds":SCENE_SECONDS,
 "requested_resolution":[WIDTH,HEIGHT],
 "requested_seed":SEED,
 "expected_model_frame_count":EXPECTED_FRAMES,
 "expected_native_frame_rate":FRAME_RATE,
 "origin_and_usage_license_review_complete":False,
 "visual_continuity_verified":False,
 "closed_notebook_and_rain_visually_verified":False,
 "native_master_1080x1920_30fps":False,
 "rights_cleared":False,
 "full_episode_completed":False,
 "approved_for_master":False,
 "publication_authorized":False,
 "paid_service_used":False,
 "human_login_performed":False
}

def report(state, **fields):
 OUT.mkdir(parents=True,exist_ok=True)
 obj=dict(STATUS_BASE,status=state)
 obj.update(fields)
 REPORT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":state,"rights_cleared":False,
                   "approved_for_master":False,
                   "publication_authorized":False},ensure_ascii=False),flush=True)
 return obj

def provider_running(data):
 return isinstance(data,dict) and isinstance(data.get("runtime"),dict) and (
      str(data["runtime"].get("stage","")).upper()=="RUNNING")

def classify_public_gpu_quota(message):
 """Extract shortage/reset without exposing vendor links or tokens in the report."""
 if not isinstance(message,str): return None
 m=re.search(
    r"exceeded your ZeroGPU quota \\((\\d+)s requested vs\\. (\\d+)s left\\)",
    message,re.IGNORECASE)
 if m is None: return None
 reset=re.search(r"Try again in (\\d+):(\\d+):(\\d+)",message)
 return {
    "requested_gpu_seconds":int(m.group(1)),
    "available_gpu_seconds":int(m.group(2)),
    "provider_reset_hint_seconds": (
       int(reset.group(1))*3600+int(reset.group(2))*60+
       int(reset.group(3)) if reset else None),
    "retry_without_approval":False
 }

def preflight():
 req=urllib.request.Request(SPACE_API,headers={"User-Agent":"VNC-E01-S01-one-shot-probe/1.0"})
 with urllib.request.urlopen(req,timeout=15) as resp:
  if resp.status!=200: return False,"HTTP_NOT_200"
  body=json.loads(resp.read(150000))
 return provider_running(body),str((body.get("runtime") or {}).get("stage","UNKNOWN"))[:40]

def inspect(path:Path):
 p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,codec_name,avg_frame_rate,nb_frames,duration:format=duration",
        "-of","json",str(path)],capture_output=True,text=True,check=False,timeout=25)
 if p.returncode!=0: raise RuntimeError("probe_failed")
 body=json.loads(p.stdout)
 streams=body.get("streams") or []
 if len(streams)!=1: raise RuntimeError("missing_video_track")
 s=streams[0]
 w,h=int(s["width"]),int(s["height"])
 dur=float(s.get("duration") or body.get("format",{}).get("duration") or 0)
 if w<=0 or h<=0 or not(0<dur<15):raise RuntimeError("bad_video_dimensions_or_duration")
 dec=subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-i",
          str(path),"-map","0:v:0","-an","-f","null","-"],
          capture_output=True,text=True,timeout=95,check=False)
 if dec.returncode!=0:raise RuntimeError("full_stream_decode_failed")
 digest=hashlib.sha256()
 with path.open("rb") as source:
  for chunk in iter(lambda:source.read(1048576),b""):digest.update(chunk)
 return {
   "sha256":digest.hexdigest(),
   "bytes":path.stat().st_size,
   "width":w,"height":h,
   "duration_seconds":round(dur,6),
   "frame_rate":s.get("avg_frame_rate"),
   "reported_frames":s.get("nb_frames"),
   "codec":s.get("codec_name"),
   "full_stream_decoded":True,
   "covers_requested_scene":dur + 0.00001 >= SCENE_SECONDS,
   "portrait_within_2pct":abs(w/h-9/16)<0.02,
   "native_master_resolution":w>=1080 and h>=1920
 }

def run():
 report("STARTED_NO_MEDIA")
 try:
  running,stage=preflight()
  if not running:
   report("BLOCKED_PUBLIC_SPACE_NOT_RUNNING",runtime_stage=stage,media_obtained=False)
   return 2
  report("REQUEST_READY_PROVIDER_RUNNING",runtime_stage=stage,media_obtained=False)
  from gradio_client import Client
  client=Client(SPACE,verbose=False)
  result=client.predict(None,PROMPT,REQUEST_SECONDS,False,SEED,False,HEIGHT,WIDTH,
                        api_name="/generate_video")
  if not isinstance(result,(list,tuple)) or not result:
   raise RuntimeError("unexpected_gradio_response")
  source=result[0]
  if isinstance(source,dict):
   source=source.get("video") or source.get("path") or source.get("name")
  if not isinstance(source,str) or not Path(source).is_file():
   raise RuntimeError("provider_returned_no_video")
  src=Path(source)
  if not(20000 <= src.stat().st_size <= 100000000):
   raise RuntimeError("source_size_out_of_range")
  dest=OUT/"E01_S01_V2_6SEC_LTX23_AI_PREVIEW_NOT_MASTER.mp4"
  shutil.copy2(src,dest)
  media=inspect(dest)
  # Save frames as independent JPEGs for human editorial QA; not a fake video.
  frames=OUT/"frame_samples"
  frames.mkdir(exist_ok=True)
  extract=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",
       str(dest),"-vf","fps=1,scale=240:-2","-frames:v","7",
       str(frames/"sample_%02d.jpg")],
       capture_output=True,text=True,timeout=30,check=False)
  jpg=list(sorted(frames.glob("*.jpg"))) if extract.returncode==0 else []
  report("PHYSICAL_AI_VIDEO_VERIFIED_SCENE_DURATION_CHECKED",
         video_file=dest.name,media=media,
         sampled_jpeg_count=len(jpg),
         storyboard_closed_notebook_visual_review_pending=True,
         storyboard_rain_visible_visual_review_pending=True,
         editorial_decision="AWAITING_MANUAL_FRAME_AUDIT")
  return 0
 except Exception as error:
  quota=classify_public_gpu_quota(str(error))
  if quota is not None:
   report("BLOCKED_ZEROGPU_QUOTA_INSUFFICIENT",
          error_type=type(error).__name__,**quota,
          video_file_returned=False,no_automatic_retry=True)
  else:
   report("BLOCKED_PROVIDER_OR_TECHNICAL_RUNTIME",
          error_type=type(error).__name__,
          error_reason=str(error)[:180].replace("\\n"," "),
          video_file_returned=False,no_automatic_retry=True)
  # CI must fail red if no generated MP4 exists, even if a JSON report exists.
  return 2

if __name__=="__main__":
 raise SystemExit(run())
