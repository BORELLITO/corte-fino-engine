"""One-time two independent camera-stock support-shot acquisitions. Never final master."""
from __future__ import annotations
import hashlib,json,subprocess,urllib.parse,urllib.request
from pathlib import Path

OUT=Path("artifacts/e01_two_stock_support_candidates")
SOURCES=[
 {"scene_id":"VNC-E01V2-S10","video_id":4828603,"start":1.0,"seconds":8.0,
  "minimum":6.6,"creator":"cottonbro studio","group":"COMMUNITY_D",
  "source_page":"https://www.pexels.com/video/two-persons-sitting-by-the-table-while-drinking-their-coffee-4828603/"},
 {"scene_id":"VNC-E01V2-S05","video_id":37340388,"start":1.0,"seconds":8.0,
  "minimum":7.62,"creator":"HÜSEYİN AVCI","group":"BIBLICAL_SYMBOL_C",
  "source_page":"https://www.pexels.com/video/historic-stone-corridor-with-arches-37340388/"}
]
MAX_BYTES=250_000_000
BASE={"schema":"1.0","project":"VERBO NO CHAO","episode":"VNC-W01-E1",
      "source_license":"https://www.pexels.com/license/",
      "source_kind":"AUTHENTIC_PEXELS_STOCK_FILM",
      "login_required":False,"api_key_required":False,"financial_spend":0,
      "visual_story_approved":False,"individual_rights_cleared":False,
      "historical_accuracy_cleared":False,"master_created":False,
      "publication_authorized":False}

def media_host(url):
 u=urllib.parse.urlparse(url)
 return (u.scheme=="https" and u.hostname=="videos.pexels.com" and
         u.path.startswith("/video-files/") and u.path.endswith(".mp4")
         and u.username is None and u.password is None)

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1_048_576),b""):h.update(b)
 return h.hexdigest()

def cmd(args,timeout):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError("command_failed")
 return p.stdout

def info(path):
 data=json.loads(cmd(["ffprobe","-v","error","-select_streams","v:0",
   "-show_entries","stream=codec_name,width,height,avg_frame_rate,duration:format=duration",
   "-of","json",str(path)],35))
 streams=data.get("streams") or []
 if len(streams)!=1:raise RuntimeError("video_track_missing")
 s=streams[0]
 return {"width":int(s.get("width",0)),"height":int(s.get("height",0)),
         "codec":s.get("codec_name"),"fps":s.get("avg_frame_rate"),
         "seconds":round(float(s.get("duration") or data.get("format",{}).get("duration") or 0),4)}

def download(src,record):
 url=f'https://www.pexels.com/download/video/{record["video_id"]}/'
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0",
                                          "Accept":"video/mp4,application/octet-stream,*/*"})
 with urllib.request.urlopen(req,timeout=80) as r:
  if not media_host(r.url):raise RuntimeError("untrusted_redirect")
  typ=r.headers.get("Content-Type","").lower()
  if "video/" not in typ and "octet-stream" not in typ:raise RuntimeError("not_video_content")
  length=int(r.headers.get("Content-Length") or 0)
  if length>MAX_BYTES:raise RuntimeError("source_too_large")
  length=0
  with src.open("wb") as out:
   while True:
    b=r.read(1_048_576)
    if not b:break
    length+=len(b)
    if length>MAX_BYTES:raise RuntimeError("source_exceeded_limit")
    out.write(b)
 if length<100000:raise RuntimeError("source_too_small")
 with src.open("rb") as f:
  if b"ftyp" not in f.read(32):raise RuntimeError("not_mp4")
 return length

def inspect(rec):
 id=rec["scene_id"][-3:]
 src=OUT/("SOURCE_"+id+"_DELETED_AFTER_PREVIEW.mp4")
 result=dict(rec,approved_for_master=False,rights_cleared=False)
 try:
  bytes_count=download(src,rec)
  meta=info(src)
  if meta["seconds"]<rec["start"]+rec["minimum"] or meta["width"]<720 or meta["height"]<1280:
   raise RuntimeError("source_insufficient_to_extract_scene")
  result.update(source_bytes=bytes_count,source_sha256=sha(src),source_native=meta)
  dest=OUT/("E01_"+id+"_CAMERA_8SEC_NOT_PUBLISH.mp4")
  filter_expr="crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)',scale=720:1280:flags=lanczos,fps=30"
  cmd(["ffmpeg","-nostdin","-y","-v","error","-ss",str(rec["start"]),
    "-i",str(src),"-t",str(rec["seconds"]),"-an","-vf",filter_expr,
    "-c:v","libx264","-threads","2","-preset","veryfast","-crf","24",
    "-pix_fmt","yuv420p","-movflags","+faststart",str(dest)],180)
  m=info(dest)
  if m["width"]!=720 or m["height"]!=1280 or m["seconds"]+.02<rec["minimum"]:
   raise RuntimeError("preview_duration_or_ratio_invalid")
  cmd(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(dest),
      "-map","0:v:0","-an","-f","null","-"],65)
  samples=[]
  for i,r in enumerate((.15,.50,.85),1):
   second=round(m["seconds"]*r,3)
   frame=OUT/("E01_"+id+"_sample_"+str(i)+".jpg")
   cmd(["ffmpeg","-nostdin","-y","-v","error","-ss",str(second),
     "-i",str(dest),"-frames:v","1",str(frame)],20)
   if not frame.is_file():raise RuntimeError("missing_sample")
   samples.append({"file":frame.name,"sha256":sha(frame),"second":second})
  result.update(status="PHYSICAL_VIDEO_VALIDATED_EDITORIAL_PENDING",
    preview=dest.name,preview_sha256=sha(dest),preview_metrics=m,
    derived_fps_30_not_native=True,full_decode_verified=True,
    sample_frames=samples,actor_continuity_verified=False)
 except Exception as e:
  result.update(status="BLOCKED_VIDEO_SOURCE",reason=str(e)[:110],
                error_type=type(e).__name__)
 finally:
  src.unlink(missing_ok=True)
 return result

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 results=[]
 for rec in SOURCES:
  results.append(inspect(rec))
  print(json.dumps({"scene_id":rec["scene_id"],"status":results[-1]["status"]}),flush=True)
  (OUT/"report.json").write_text(json.dumps(dict(BASE,shots=results),
     ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 ok=sum(x["status"]=="PHYSICAL_VIDEO_VALIDATED_EDITORIAL_PENDING" for x in results)
 (OUT/"report.json").write_text(json.dumps(dict(BASE,shots=results,
     physical_video_count=ok),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return 0 if ok else 2

if __name__=="__main__":
 raise SystemExit(main())
