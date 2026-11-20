"""E01 S09 — physically audit a Mixkit 4K notebook video without any generation.

The only eligible source is Mixkit Free clip #99890, URL resolved by live
Firecrawl browser on 2026-11-20 (HTTP 200, video/mp4). It is NOT an approved
shot or proof of genuine camera capture. No public release or subscription.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/e01_multibank_scene_coverage_20261120_v1.json"
SOURCE_URL = "https://assets.mixkit.co/active_storage/video_items/99890/1717186770/99890-video-2160.mp4"
SOURCE_PAGE = "https://mixkit.co/free-stock-video/close-up-a-hand-writing-notes-on-a-notebook-with-99890/"
MAX_BYTES = 125_000_000
TARGET_FPS = 30
PREVIEW_FRAMES = 173
W,H=720,1280
CONTACT = "S09_MIXKIT_99890_3x3_REAL_CROPS_QA.jpg"
PREVIEW = "S09_MIXKIT_99890_RIGHT75_CROP_MOTION_QA_NOT_MASTER.mp4"
REPORT = "S09_MIXKIT_99890_PHYSICAL_REPORT.json"
QA_NOTICE = "PREVIA TECNICA / NAO PUBLICAR"


class IntakeError(ValueError):
    pass


def file_sha(path:Path)->str:
    hasher=hashlib.sha256()
    with path.open("rb") as r:
        for piece in iter(lambda:r.read(1024*1024),b""):
            hasher.update(piece)
    return hasher.hexdigest()


def check_manifest(root=ROOT, data=None):
    if data is None:
        data=json.loads((Path(root)/CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise IntakeError("missing_contract")
    checks={
      "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
      "episode_id":"VNC-W01-E1",
      "root_baseline_commit":"db6e1d4acf23e82793f6230535a1716842ba5cd0",
      "script_sha256":"c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6",
      "voice_wav_sha256":"4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e",
      "canonical_ass_sha256":"0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a",
      "narration_seconds":70.425,"editorial_stage":"MULTIBANK_CURATION_RESEARCH_NOT_RELEASE",
      "no_paid_sources":True,"no_tinyfish":True,"no_full_master":True,
      "no_merge":True,"no_publication":True,"no_auto_approval_after_technical_tests":True,
      "no_replacement_of_original_s01":True,
    }
    for k,v in checks.items():
        if type(data.get(k)) is not type(v) or data[k]!=v:
            raise IntakeError("manifest_drift_"+k)
    scenes=data.get("scenes",[])
    if len(scenes)!=12 or [s.get("scene_id") for s in scenes]!=[
            f"VNC-E01V2-S{i:02d}" for i in range(1,13)]:
        raise IntakeError("scene_coverage_invalid")
    s09=scenes[8]
    if (s09.get("start_seconds")!=49.8 or
        s09.get("end_seconds")!=55.56 or
        s09.get("primary_candidate_id")!=99890 or
        s09.get("owner_visual_approved") is not False or
        s09.get("master_allowed") is not False or
        s09.get("publication_authorized") is not False):
        raise IntakeError("wrong_s09_approval_or_timing")
    candidates=data.get("source_candidates",[])
    ids=[x.get("video_id") for x in candidates]
    if len(candidates)!=10 or len(ids)!=len(set(ids)) or ids.count(99890)!=1:
        raise IntakeError("sources_duplicate_or_missing")
    candidate=next(x for x in candidates if x.get("video_id")==99890)
    req={
       "provider":"Mixkit","scene":"S09","page_url":SOURCE_PAGE,
       "page_license":"Mixkit Stock Video Free License",
       "preview_physically_decoded":False,
       "individual_rights_cleared":False,
       "visual_approved":False,
       "master_approved":False,
       "publication_authorized":False,
    }
    for k,v in req.items():
        if type(candidate.get(k)) is not type(v) or candidate[k]!=v:
            raise IntakeError("source_drift_"+k)
    b=candidate.get("browser_probe",{})
    if (b.get("download_final_url")!=SOURCE_URL or
        b.get("observed_http_status")!=200 or
        b.get("observed_content_type")!="video/mp4" or
        b.get("listed_resolution")!=[4096,2160] or
        b.get("listed_seconds")!=8 or
        b.get("physical_file_sha256") is not None):
        raise IntakeError("browser_provenance_not_exact")
    lock=data.get("strict_quality_policy",{})
    for flag in ("no_still_photo_as_video","no_false_historical_depiction",
                 "no_recurring_protagonist_forgery","must_check_crop_camera_motion_and_caption_zone",
                 "individual_identifiable_person_property_brand_risks_pending"):
        if lock.get(flag) is not True:
            raise IntakeError("editorial_gate_disabled_"+flag)
    return candidate


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise IntakeError("source_redirect_denied")


def download_original(folder:Path):
    parsed=urllib.parse.urlsplit(SOURCE_URL)
    if (parsed.scheme!="https" or parsed.hostname!="assets.mixkit.co" or
        parsed.port is not None or parsed.username is not None or
        parsed.path!="/active_storage/video_items/99890/1717186770/99890-video-2160.mp4"
        or parsed.query or parsed.fragment):
        raise IntakeError("download_url_not_whitelisted")
    path=folder/"original_mixkit_99890.mp4"
    count=0
    sha=hashlib.sha256()
    req=urllib.request.Request(SOURCE_URL,headers={
        "Accept":"video/mp4,application/octet-stream",
        "User-Agent":"VNC-Stock-Physical-QA/1.0"})
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=60) as r:
        if r.status!=200:
            raise IntakeError("source_status_not_200")
        mime=r.headers.get("Content-Type","").lower().split(";")[0].strip()
        if mime!="video/mp4":
            raise IntakeError("source_not_mp4")
        length=r.headers.get("Content-Length")
        if length and int(length)>MAX_BYTES:
            raise IntakeError("source_size_exceeds_limit")
        with path.open("wb") as output:
            while True:
                buf=r.read(1048576)
                if not buf:break
                count+=len(buf)
                if count>MAX_BYTES:
                    raise IntakeError("download_limit_exceeded")
                output.write(buf)
                sha.update(buf)
    if count<100000:
        raise IntakeError("source_empty_or_invalid")
    return path,{"source_bytes":count,"source_sha256":sha.hexdigest(),
                 "source_url":SOURCE_URL,"provider":"Mixkit",
                 "page_url":SOURCE_PAGE,"individual_rights_cleared":False}


def checked(command,timeout=90):
    p=subprocess.run(command,capture_output=True,timeout=timeout)
    if p.returncode:
        raise IntakeError("subprocess_failed_"+str(p.returncode))
    return p.stdout


def probe(path:Path):
    raw=checked(["ffprobe","-v","error","-show_entries",
                "stream=index,codec_type,codec_name,width,height,avg_frame_rate,nb_frames:"
                "format=duration,size","-of","json",str(path)],35)
    return json.loads(raw)


def source_metadata(path:Path):
    d=probe(path)
    stream=next((x for x in d.get("streams",[]) if x.get("codec_type")=="video"),None)
    if not stream:
        raise IntakeError("no_actual_video_stream")
    w,h=int(stream["width"]),int(stream["height"])
    if w<3840 or h<2160 or float(d.get("format",{}).get("duration",0))<5.8:
        raise IntakeError("source_not_minimum_4k_duration")
    return {"width":w,"height":h,"duration_seconds":float(d["format"]["duration"]),
            "codec":stream.get("codec_name"),"source_frame_rate":stream.get("avg_frame_rate")}


def sample_frame(src,t,cropx,cropw,croph):
    from PIL import Image
    filter=f"crop={cropw}:{croph}:{cropx}:0,scale=216:384:flags=lanczos,format=rgb24"
    raw=checked(["ffmpeg","-nostdin","-v","error","-ss",str(t),"-i",str(src),
                 "-an","-frames:v","1","-vf",filter,"-pix_fmt","rgb24",
                 "-f","rawvideo","pipe:1"],60)
    if len(raw)!=216*384*3:
        raise IntakeError("real_frame_decode_wrong_size")
    return Image.frombytes("RGB",(216,384),raw)


def contact_sheet(src,out,width,height):
    from PIL import Image, ImageDraw, ImageStat, ImageChops
    import math
    cw=2*math.floor(height*9/16/2)
    if cw<1080 or height<1920 or width-cw<0:
        raise IntakeError("native_9_16_crop_not_1080p")
    xvalues=[0,(width-cw)//2,width-cw]
    samples=[0.5,2.4,5.25]
    sheet=Image.new("RGB",(216*3,384*3+65),(15,15,17))
    draw=ImageDraw.Draw(sheet)
    gradients={}
    for col,(x,label) in enumerate(zip(xvalues,("LEFT","CENTER","RIGHT"))):
        luma=[];frames=[]
        for row,t in enumerate(samples):
            frame=sample_frame(src,t,x,cw,height)
            frames.append(frame)
            sheet.paste(frame,(col*216,row*384))
            luma.append(round(ImageStat.Stat(frame.convert("L")).mean[0],2))
            draw.rectangle((col*216+3,row*384+4,col*216+87,row*384+22),fill=(5,5,5))
            draw.text((col*216+6,row*384+8),f"{label} {t:g}s",fill=(255,255,255))
        drift=[
            round(ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0],3)
            for a,b in zip(frames,frames[1:])
        ]
        gradients[label]={"mean_luma":luma,"frame_drift":drift,
                          "sample_motion_confirmed":any(v>0.35 for v in drift)}
    draw.text((8,384*3+20),"VNC E01 S09 | REAL MIXKIT FRAMES | QA ONLY - DO NOT RELEASE",
              fill=(240,240,240))
    out.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(out,"JPEG",quality=87)
    if not any(v["sample_motion_confirmed"] for v in gradients.values()):
        raise IntakeError("source_samples_appear_static")
    return {"filename":out.name,"sha256":file_sha(out),"bytes":out.stat().st_size,
            "native_crop_width":cw,"native_crop_height":height,
            "sample_times_seconds":samples,"cropping_variants":gradients}


def render_right75(src,dst,width,height):
    import math
    from PIL import Image, ImageDraw
    with tempfile.TemporaryDirectory(prefix="vnc-mixkit-overlay-") as td:
        overlay=Path(td)/"watermark.png"
        # Self-contained QA watermark: no dependency on unmerged S01 draft code.
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        drawing=ImageDraw.Draw(im)
        drawing.rectangle((0,0,W,60),fill=(0,0,0,165))
        drawing.text((12,18),"VNC E01 S09 - PREVIA QA - NAO PUBLICAR",
                     fill=(250,250,250,255))
        im.save(overlay)
        cw=2*math.floor(height*9/16/2)
        filt=(f"[0:v]fps={TARGET_FPS},crop={cw}:{height}:3*(iw-{cw})/4:0,"
              f"scale={W}:{H}:flags=lanczos,setsar=1[scene];"
              "[scene][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,"
              "format=yuv420p[v]")
        checked(["ffmpeg","-nostdin","-v","error","-y","-i",str(src),
                 "-loop","1","-i",str(overlay),"-filter_complex",filt,
                 "-map","[v]","-an","-frames:v",str(PREVIEW_FRAMES),"-r",str(TARGET_FPS),
                 "-c:v","libx264","-preset","veryfast","-crf","23",
                 "-movflags","+faststart",str(dst)],165)
    q=probe(dst)
    ss=q.get("streams",[])
    if len(ss)!=1 or ss[0].get("codec_type")!="video":
        raise IntakeError("preview_other_streams")
    v=ss[0]
    if (v.get("codec_name")!="h264" or int(v.get("width",0))!=W
        or int(v.get("height",0))!=H or
        int(v.get("nb_frames",0))!=PREVIEW_FRAMES or
        v.get("avg_frame_rate")!="30/1" or
        abs(float(q.get("format",{}).get("duration",0))-PREVIEW_FRAMES/TARGET_FPS)>0.03):
        raise IntakeError("preview_geometry_invalid")
    checked(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(dst),
             "-map","0:v:0","-an","-f","null","-"],90)
    return {"filename":dst.name,"sha256":file_sha(dst),"bytes":dst.stat().st_size,
            "width":W,"height":H,"fps":TARGET_FPS,
            "frames":PREVIEW_FRAMES,"seconds":float(q["format"]["duration"]),
            "full_preview_decode":True,"audio":False,"captions":False,"master":False}


def run(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    report={"project_id":"VERBO_NO_CHAO_EXCLUSIVO",
            "episode_id":"VNC-W01-E1","scene_id":"VNC-E01V2-S09",
            "status":"BLOCKED_NO_PHYSICAL_CANDIDATE_YET","owner_approved":False,
            "original_story_changed":False,"rights_cleared":False,
            "camera_origin_independently_proven":False,
            "music_added":False,"voice_changed":False,"master_allowed":False,
            "publication_authorized":False}
    qa_mp4=out/PREVIEW
    qa_jpg=out/CONTACT
    try:
        check_manifest()
        with tempfile.TemporaryDirectory(prefix="vnc-mixkit99890-") as working:
            source,receipt=download_original(Path(working))
            meta=source_metadata(source)
            report["source"]={**receipt,**meta,"source_full_decode_claimed":False}
            contact=contact_sheet(source,qa_jpg,meta["width"],meta["height"])
            report["cropping"]=contact
            movie=render_right75(source,qa_mp4,meta["width"],meta["height"])
            report.update(status="PHYSICAL_MIXKIT_S09_PREVIEW_READY_FOR_EDITORIAL_QA",
                          source={**receipt,**meta,"source_full_decode_claimed":False},
                          cropping=contact,preview=movie,
                          source_video_not_persisted=True,
                          artistic_qc_pending=True)
    except Exception as exc:
        qa_mp4.unlink(missing_ok=True)
        report["error_type"]=type(exc).__name__
        report["error_code"]=str(exc)[:120] if isinstance(exc,IntakeError) else "provider_or_binary_failed"
    (out/REPORT).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                             encoding="utf-8")
    print(json.dumps({"status":report["status"],"rights_cleared":False,
                      "master_allowed":False,"publication_authorized":False}))
    return 0 if report["status"]=="PHYSICAL_MIXKIT_S09_PREVIEW_READY_FOR_EDITORIAL_QA" else 2


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    raise SystemExit(run(ap.parse_args().out))


if __name__=="__main__":
    main()
