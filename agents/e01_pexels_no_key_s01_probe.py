"""Test ONE free Pexels camera-footage source as an E01 S01 candidate.

No provider API key, account, payment, user upload or publication.
Uses the openly published source download; on a block, fail closed.
Preview clips remain editorial candidates, not final, and are temporary.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PAGE="https://www.pexels.com/video/a-silhouette-of-a-man-sitting-alone-beside-a-window-8860242/"
DOWNLOAD="https://www.pexels.com/download/video/8860242/"
LICENSE="https://www.pexels.com/license/"
CREATOR="cottonbro studio"
SOURCE_ID=8860242
OUT=Path("artifacts/vnc_e01_pexels_no_key_s01_probe")
MANIFEST=OUT/"evidence.json"
MAX_BYTES=500_000_000
TARGET_SECONDS=5.74
PREVIEW_SECONDS=6.1
EXPECTED_ASPECT=9/16

BASE={
 "project":"verbo-no-chao","episode_id":"VNC-W01-E1",
 "scene_id":"VNC-E01V2-S01","source_type":"REAL_CAMERA_STOCK_FOOTAGE_CANDIDATE",
 "provider":"Pexels","source_asset_id":SOURCE_ID,"source_page":PAGE,
 "source_creator":CREATOR,"license_url":LICENSE,
 "no_api_key":True,"no_authentication":True,"no_payment":True,
 "target_scene_duration":TARGET_SECONDS,"preview_duration":PREVIEW_SECONDS,
 "individual_releases_evaluated":False,"rights_cleared":False,
 "scene_meets_script_narrative":False,"same_actor_as_other_scenes":False,
 "notebook_closed_verified":False,"rain_visible_verified":False,
 "actual_camera_footage_proven_beyond_source_claim":False,
 "approved_for_master":False,"publication_authorized":False,
 "user_reproduces_video_without_source_credit":False
}

def save(status,**extras):
 OUT.mkdir(parents=True,exist_ok=True)
 data=dict(BASE,status=status,**extras)
 MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":status,"approved_for_master":False,
                 "publication_authorized":False},ensure_ascii=False),flush=True)
 return data

def allow_media_url(url):
 v=urllib.parse.urlparse(url)
 return v.scheme=="https" and v.hostname=="videos.pexels.com" and (
     v.path.startswith("/video-files/") and v.path.lower().endswith(".mp4")
 )

def sha256_file(path):
 digest=hashlib.sha256()
 with path.open("rb") as fh:
  for block in iter(lambda:fh.read(1048576),b""):
   digest.update(block)
 return digest.hexdigest()

def download_public_video(dest):
 # Pexels provides its own free video download without requiring an API key.
 req=urllib.request.Request(DOWNLOAD,headers={
     "User-Agent":"Mozilla/5.0 (compatible; E01EditorialProbe/1.0)",
     "Accept":"video/mp4,application/octet-stream,*/*",
 })
 with urllib.request.urlopen(req,timeout=60) as resp:
  if not allow_media_url(resp.url):
   raise ValueError("unexpected_download_redirect_host_or_media_type")
  ctype=resp.headers.get("Content-Type","")
  if not any(x in ctype.lower() for x in ("video/","octet-stream")):
   raise ValueError("provider_did_not_return_video_bytes")
  length=resp.headers.get("Content-Length")
  if length and int(length)>MAX_BYTES:
   raise ValueError("source_media_exceeds_size_limit")
  written=0
  with dest.open("wb") as out:
   while True:
    chunk=resp.read(1048576)
    if not chunk: break
    written+=len(chunk)
    if written>MAX_BYTES:
     raise ValueError("source_download_exceeded_size_limit")
    out.write(chunk)
 if written<100000:
  raise ValueError("source_download_too_small")
 # Do not assume bytes are MP4 from the file extension.
 with dest.open("rb") as fh:
  if b"ftyp" not in fh.read(32):
   raise ValueError("source_not_mp4_header")
 return written

def ffprobe(path):
 p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
  "-show_entries","stream=codec_name,width,height,avg_frame_rate,duration:format=duration",
  "-of","json",str(path)],capture_output=True,text=True,
  timeout=30,check=False)
 if p.returncode!=0:raise ValueError("ffprobe_failed")
 streams=json.loads(p.stdout).get("streams") or []
 if len(streams)!=1:raise ValueError("source_video_stream_unavailable")
 s=streams[0]
 return {"codec":s.get("codec_name"),"width":int(s.get("width") or 0),
         "height":int(s.get("height") or 0),
         "fps":s.get("avg_frame_rate"),
         "duration":float(s.get("duration") or 0)}

def process():
 save("STARTED_NO_FOOTAGE")
 source=OUT/"pexels8860242_original_TEMP.mp4"
 try:
  count=download_public_video(source)
  meta=ffprobe(source)
  if (meta["duration"]<PREVIEW_SECONDS or meta["width"]<1280 or
      meta["height"]<720 or meta["codec"] not in ("h264","hevc","av1","vp9")):
   raise ValueError("source_video_unsuitable_for_vertical_preview")
  source_sha=sha256_file(source)
  save("SOURCE_VIDEO_BYTES_PHYSICALLY_VERIFIED",source_bytes=count,
       source_sha256=source_sha,source_metrics=meta,
       candidates_generated=False)
  variants=[]
  for name,position in (("left","0.12"),("center","0.50"),("right","0.88")):
   dest=OUT/("S01_real_footage_"+name+"_NOT_MASTER.mp4")
   filt=("crop=w=trunc(ih*9/16/2)*2:h=ih:x=(iw-ow)*"+
          position+":y=0,scale=720:1280:flags=lanczos")
   cmd=["ffmpeg","-nostdin","-y","-v","error","-ss","0",
       "-i",str(source),"-t",str(PREVIEW_SECONDS),"-an",
       "-vf",filt,"-c:v","libx264","-preset","veryfast",
       "-threads","2","-crf","24","-pix_fmt","yuv420p",
       "-movflags","+faststart",str(dest)]
   res=subprocess.run(cmd,capture_output=True,text=True,timeout=130)
   if res.returncode!=0:raise ValueError("ffmpeg_reframe_failed")
   check=ffprobe(dest)
   if (check["duration"]<TARGET_SECONDS or
       check["width"]!=720 or check["height"]!=1280):
    raise ValueError("preview_does_not_cover_scene_or_wrong_dimensions")
   decoded=subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
       "-i",str(dest),"-map","0:v:0","-an","-f","null","-"],
       capture_output=True,text=True,timeout=50)
   if decoded.returncode!=0:raise ValueError("preview_full_decode_failed")
   sample=OUT/("S01_sample_"+name+".jpg")
   s=subprocess.run(["ffmpeg","-nostdin","-y","-v","error","-ss","2.0",
       "-i",str(dest),"-frames:v","1",str(sample)],capture_output=True,
       text=True,timeout=15)
   variants.append({
      "crop":name,"mp4":dest.name,"preview_sha256":sha256_file(dest),
      "width":720,"height":1280,"native_source_width":meta["width"],
      "original_fps":meta["fps"],"source_duration":meta["duration"],
      "duration":check["duration"],"valid_full_decode":True,
      "sample":sample.name if s.returncode==0 and sample.is_file() else None,
      "visual_scene_approved":False
   })
  save("THREE_PHYSICAL_REAL_STOCK_PREVIEWS_NEED_EDITORIAL_REVIEW",
       source_sha256=source_sha,source_bytes=count,
       source_metrics=meta,
       variants=variants,original_film_preserved_in_ephemeral_runner_only=True,
       repeatable_source_download=True,
       model_gpu_quota_required=False,
       editor_must_confirm_real_people_not_misrepresented=True)
  return 0
 except (Exception) as error:
  save("BLOCKED_PUBLIC_STOCK_SOURCE_OR_TRANSCODE",
      error_type=type(error).__name__,
      blocked_reason=str(error)[:180].replace("\n"," "),
      no_automatic_retry=True)
  return 2
 finally:
  # Original full 4K stock media is not stored as a GitHub artifact:
  # previews are only 6.1 seconds, original page retains provenance.
  source.unlink(missing_ok=True)

if __name__=="__main__":
 raise SystemExit(process())
