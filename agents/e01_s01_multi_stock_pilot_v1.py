"""VERBO NO CHÃO E01 S01 — deterministic real-stock short-form montage proof.

Two independently licensed Pexels pages, real camera footage, no AI video.
Only a candidate preview is created; no user data, master or publication.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from agents.e01_stock_candidates import ROOT
from agents.e01_s01_stock_rejection_gate import classify_s01_stock_preview

OUTPUT = Path("artifacts/vnc_e01_s01_multi_stock_pilot")
INPUTS = [
    {"id":8860242,"role":"ANONYMOUS_PERSON_AT_WINDOW","page":"https://www.pexels.com/video/a-silhouette-of-a-man-sitting-alone-beside-a-window-8860242/","frames":93,"seek_seconds":5,"crop":"center","risk":"Check center crop and no readable wall text or recognizable face; this replaces prior unsuitable 32788087 source."},
    {"id":4458845,"role":"RAINY_WINDOW_AT_NIGHT","page":"https://www.pexels.com/video/rainy-nights-4458845/","frames":80,"seek_seconds":1,"crop":"center","risk":"Separate source; symbolic montage, never claim same physical room."},
]
CLOSED_SCRIPT_SHA="c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
CLOSED_VOICE_SHA="4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
FPS=30
TARGET=5.74
FRAME_COUNT=sum(x["frames"] for x in INPUTS)
CANVAS=(720,1280)
MAX_BYTES=160_000_000

class PilotError(ValueError): pass

def assert_inputs():
    if FRAME_COUNT!=173 or abs(FRAME_COUNT/FPS-TARGET)>0.03:
        raise PilotError("bad_target_duration")
    if [x["id"] for x in INPUTS]!=[8860242,4458845]:
        raise PilotError("unapproved_candidate_set")
    if len({x["id"] for x in INPUTS})!=2:
        raise PilotError("duplicate_sources")
    if any(x["frames"]<30 or x["seek_seconds"]<0 or x["crop"]!="center" or
           not x["page"].startswith("https://www.pexels.com/video/") or
           not x["page"].endswith("-"+str(x["id"])+"/")
           for x in INPUTS):
        raise PilotError("invalid_stock_input")
    return True

def verify_story(root=ROOT):
    data=json.loads((Path(root)/"contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf8"))
    first=data["scenes"][0]
    if not (data["script_sha256"]==CLOSED_SCRIPT_SHA and data["audio_sha256"]==CLOSED_VOICE_SHA
            and first["id"]=="VNC-E01V2-S01" and first["start_seconds"]==0
            and first["end_seconds"]==TARGET and not first["approved_for_export"]
            and first["asset_sha256"] is None and data["publication_authorized"] is False):
        raise PilotError("storyboard_not_immutable")
    return True

class StrictPexels(urllib.request.HTTPRedirectHandler):
    def __init__(self,ident):
        super().__init__()
        self.ident=ident
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urllib.parse.urlsplit(newurl)
        if not (parsed.scheme=="https" and parsed.hostname=="videos.pexels.com"
                and parsed.port is None and parsed.username is None and parsed.password is None
                and re.fullmatch(r"/video-files/"+str(self.ident)+r"/[A-Za-z0-9_.-]+\.mp4",parsed.path)):
            raise PilotError("untrusted_media_redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download_source(source,temp:Path):
    ident=source["id"]
    out=temp/(str(ident)+".mp4")
    req=urllib.request.Request(
        "https://www.pexels.com/download/video/"+str(ident)+"/",
        headers={"User-Agent":"VNC-S01-RealFootage-Pilot/1.0",
                 "Accept":"video/mp4,application/octet-stream,*/*"})
    opener=urllib.request.build_opener(StrictPexels(ident))
    sha=hashlib.sha256();count=0
    with opener.open(req,timeout=45) as response:
        if response.status!=200 or urllib.parse.urlsplit(response.url).hostname!="videos.pexels.com":
            raise PilotError("unverified_media_origin")
        size=response.headers.get("Content-Length")
        if size and int(size)>MAX_BYTES:raise PilotError("oversized_source")
        mime=response.headers.get("Content-Type","").lower()
        if "video/" not in mime and "octet-stream" not in mime:
            raise PilotError("invalid_content_type")
        with out.open("wb") as writer:
            while True:
                block=response.read(1048576)
                if not block:break
                count+=len(block)
                if count>MAX_BYTES:raise PilotError("oversized_source")
                sha.update(block);writer.write(block)
    if count<100000:raise PilotError("media_too_small")
    return out,{"video_id":ident,"page_url":source["page"],"bytes":count,
                "source_sha256":sha.hexdigest(),"source_rights_cleared":False}

def probe(filename,min_seconds=7.0,min_width=1080,min_height=720):
    a=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=codec_name,width,height,avg_frame_rate:format=duration",
         "-of","json",str(filename)],capture_output=True,text=True,timeout=35)
    if a.returncode:raise PilotError("ffprobe_failed")
    obj=json.loads(a.stdout)
    video=(obj.get("streams")or[None])[0]
    if not video:raise PilotError("no_video")
    dur=float(obj["format"]["duration"])
    if dur<min_seconds or int(video["width"])<min_width or int(video["height"])<min_height:
        raise PilotError("source_not_compatible")
    return {"duration_seconds":round(dur,3),"width":video["width"],
            "height":video["height"],"source_codec":video.get("codec_name")}

def checked_run(command,limit,err):
    p=subprocess.run(command,capture_output=True,timeout=limit)
    if p.returncode:raise PilotError(err)
    return p

def render_piece(src,dest,seek,frames):
    w,h=CANVAS
    # Explicit 9:16 center crop of physical frames, no generative transformations.
    vf=f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},eq=contrast=1.05:saturation=0.88"
    checked_run(["ffmpeg","-nostdin","-v","error","-y",
         "-ss",str(seek),"-i",str(src),"-an","-frames:v",str(frames),
         "-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","22",
         "-pix_fmt","yuv420p","-r",str(FPS),str(dest)],75,"piece_render_failed")

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    result={
       "project":"VERBO_NO_CHAO_EXCLUSIVO","scene_id":"VNC-E01V2-S01",
       "status":"BLOCKED_NO_MEDIA_YET",
       "mode":"REAL_STOCK_EDITORIAL_MONTAGE_V2_NOT_SINGLE_WORLD",
       "source_audio_added":False,"captions_added":False,
       "editorial_reviewed":False,"rights_cleared":False,
       "original_scene_contract_modified":False,"master_allowed":False,
       "publication_authorized":False,
       "source_clips":[]}
    try:
        assert_inputs();verify_story()
        with tempfile.TemporaryDirectory(prefix="vnc-real-stock-") as working:
            temp=Path(working)
            parts=[]
            for idx,source in enumerate(INPUTS):
                movie,evidence=download_source(source,temp)
                evidence.update(probe(movie))
                result["source_clips"].append(evidence)
                piece=temp/(f"part_{idx}.mp4")
                render_piece(movie,piece,source["seek_seconds"],source["frames"])
                parts.append(piece)
                movie.unlink(missing_ok=True)
            concat=temp/"parts.txt"
            concat.write_text("".join(f"file '{p.name}'\n" for p in parts),encoding="utf8")
            target=OUTPUT/"VNC-E01-S01-REAL-STOCK-MONTAGE-V2-CANDIDATE-NOT-MASTER.mp4"
            checked_run(["ffmpeg","-nostdin","-v","error","-y",
                "-f","concat","-safe","0","-i",str(concat),
                "-an","-c","copy","-movflags","+faststart",str(target)],45,
                "concat_failed")
            q=probe(target,min_seconds=5.70,min_width=720,min_height=1280)
            duration=q["duration_seconds"]
            if not 5.70<=duration<=5.80:
                raise PilotError("wrong_montage_duration")
            checked_run(["ffmpeg","-nostdin","-v","error","-xerror",
                "-i",str(target),"-map","0:v:0","-an","-f","null","-"],65,
                "full_preview_decode_failed")
            digest=hashlib.sha256(target.read_bytes()).hexdigest()
            result.update(status="REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_EDITORIAL_AND_RIGHTS_PENDING",
                output_sha256=digest,output_bytes=target.stat().st_size,
                actual_duration_seconds=duration,
                width=q["width"],height=q["height"],
                visual_duration_covers_s01=True,full_video_decode_ok=True,
                video_file=target.name,frames=FRAME_COUNT)
            # Technical PASS must not re-promote a previously rejected cinematic cut.
            result.update(classify_s01_stock_preview(result, movie_path=target))
            if result["editorial_decision"] == "REJECTED_EDITORIAL_PREVIOUS_QA":
                result["status"] = "REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_REJECTED_EDITORIAL"
    except (PilotError,OSError,KeyError,ValueError,subprocess.TimeoutExpired,urllib.error.URLError) as error:
        (OUTPUT/"VNC-E01-S01-REAL-STOCK-MONTAGE-V2-CANDIDATE-NOT-MASTER.mp4").unlink(missing_ok=True)
        result.update(status="BLOCKED_NO_APPROVED_VIDEO",error_type=type(error).__name__,
            error_reason=str(error) if isinstance(error,PilotError) else None)
    (OUTPUT/"technical_report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:result.get(k) for k in ("status","actual_duration_seconds","output_sha256","error_type","error_reason","publication_authorized")}))
    return 0 if result["status"].startswith("REAL_STOCK") else 2

if __name__=="__main__":
    raise SystemExit(main())
