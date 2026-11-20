"""VNC E01: TWO exact Mixkit Free stock samples, not an episode master.

S03 rain traffic and S10 human support. Real video download with per-source
host/path allowlist, size budget, SHA receipt, 9:16 crop, physical 3-frame
contact sheet, bounded watermarked review preview and full preview decode.
Each source independently fails closed and cannot become approved via CI.
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, tempfile
import urllib.request, urllib.parse
from pathlib import Path

from agents.e01_mixkit_s09_physical_qa_20261120_v1 import (
    ROOT, CONTRACT, IntakeError, NoRedirect, file_sha, checked, probe
)

SOURCES={
 "S03":{
  "id":4331,"page":"https://mixkit.co/free-stock-video/traffic-on-a-rainy-night-4331/",
  "url":"https://assets.mixkit.co/videos/4331/4331-1080.mp4",
  "frames":184,"start":10.62,"end":16.76,"narrative":"NIGHT_RAIN_SOCIAL_METAPHOR_NOT_BIBLICAL_HISTORY"
 },
 "S10":{
  "id":8748,"page":"https://mixkit.co/free-stock-video/sad-and-crestfallen-young-man-is-comforted-by-his-girlfriend-8748/",
  "url":"https://assets.mixkit.co/videos/8748/8748-2160.mp4",
  "frames":198,"start":55.56,"end":62.16,"narrative":"HUMAN_SUPPORT_WITHOUT_MIRACLE_OR_SAME_ACTOR_CLAIM"
 }
}
LIMIT_BYTES=155_000_000
FPS=30
W,H=540,960

def verify(root=ROOT):
    d=json.loads((Path(root)/CONTRACT).read_text(encoding="utf-8"))
    if d.get("project_id")!="VERBO_NO_CHAO_EXCLUSIVO" or d.get("episode_id")!="VNC-W01-E1" or d.get("no_full_master") is not True or d.get("no_publication") is not True or d.get("no_paid_sources") is not True:
        raise IntakeError("unsafe_project_or_release_policy")
    rows=d.get("source_candidates",[])
    scenes=d.get("scenes",[])
    if len(rows)!=10 or len(scenes)!=12:
        raise IntakeError("scene_coverage_drift")
    for name,s in SOURCES.items():
        entry=next((c for c in rows if c.get("video_id")==s["id"]),None)
        index=int(name[1:])-1
        slot=scenes[index]
        if (not entry or entry.get("page_url")!=s["page"] or
            entry.get("page_license")!="Mixkit Stock Video Free License" or
            any(entry.get(x) is not False for x in ("visual_approved","individual_rights_cleared","publication_authorized")) or
            slot.get("scene_id")!="VNC-E01V2-"+name or slot.get("primary_candidate_id")!=s["id"] or
            slot.get("start_seconds")!=s["start"] or slot.get("end_seconds")!=s["end"] or
            any(slot.get(x) is not False for x in ("owner_visual_approved","rights_cleared","master_allowed","publication_authorized"))):
            raise IntakeError("source_license_scene_or_rights_drift_"+name)
    return True

def download(s,work):
    expected=urllib.parse.urlsplit(s["url"])
    if (expected.scheme!="https" or expected.netloc!="assets.mixkit.co"
        or expected.path!=f"/videos/{s['id']}/{s['id']}-{'1080' if s['id']==4331 else '2160'}.mp4"
        or expected.query or expected.fragment):
        raise IntakeError("external_asset_url_untrusted")
    dest=work/f"mixkit_{s['id']}_source.mp4"
    req=urllib.request.Request(s["url"],headers={"User-Agent":"VNC-Physical-Source-QA/1.0","Accept":"video/mp4"})
    size=0;hasher=hashlib.sha256()
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=60) as response:
        if response.status!=200 or response.headers.get("Content-Type","").lower().split(";")[0]!="video/mp4":
            raise IntakeError("source_is_not_real_mp4_response")
        reported=response.headers.get("Content-Length")
        if reported and int(reported)>LIMIT_BYTES:
            raise IntakeError("oversize_header")
        with dest.open("wb") as output:
            while True:
                block=response.read(1048576)
                if not block:break
                size+=len(block)
                if size>LIMIT_BYTES:raise IntakeError("oversize_stream")
                hasher.update(block);output.write(block)
    if size<100000:raise IntakeError("source_bytes_too_short")
    return dest,{"bytes":size,"sha256":hasher.hexdigest(),"url_host":"assets.mixkit.co",
                 "source_full_decode_claimed":False,"individual_rights_cleared":False}

def source_probe(src):
    p=probe(src)
    v=next((x for x in p.get("streams",[]) if x.get("codec_type")=="video"),None)
    if not v:raise IntakeError("no_video_stream")
    w,h=int(v["width"]),int(v["height"])
    duration=float(p.get("format",{}).get("duration",0))
    if w<1280 or h<720 or duration<7:
        raise IntakeError("minimum_source_dimensions_or_duration")
    crop_w=2*math.floor(h*9/16/2)
    if crop_w>w or crop_w<400:raise IntakeError("portrait_crop_not_possible")
    return {"width":w,"height":h,"duration_seconds":duration,
            "source_codec":v.get("codec_name"),"source_fps":v.get("avg_frame_rate"),
            "crop_width":crop_w,"crop_height":h}

def frames_contact(src,out,meta,name):
    from PIL import Image,ImageDraw,ImageStat,ImageChops
    from io import BytesIO
    width,height=meta["width"],meta["height"]
    crop=meta["crop_width"]
    samples=(.5,2.6,5.5)
    image=Image.new("RGB",(216*3,384+48),(19,19,20))
    draw=ImageDraw.Draw(image)
    drift=[];frames=[]
    for i,t in enumerate(samples):
        raw=checked(["ffmpeg","-nostdin","-v","error","-ss",str(t),"-i",str(src),
          "-an","-frames:v","1","-vf",f"crop={crop}:{height}:(iw-{crop})/2:0,scale=216:384:flags=lanczos",
          "-pix_fmt","rgb24","-f","rawvideo","pipe:1"],50)
        if len(raw)!=216*384*3:raise IntakeError("frame_bytes_not_genuine")
        frame=Image.frombytes("RGB",(216,384),raw)
        image.paste(frame,(i*216,0))
        draw.rectangle((i*216+5,5,i*216+78,24),fill=(6,6,6))
        draw.text((i*216+9,8),f"{t:.1f}s",fill=(250,250,250))
        frames.append(frame)
    for a,b in zip(frames,frames[1:]):
        drift.append(round(ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0],2))
    draw.text((6,396),f"{name} — MIXKIT REAL VIDEO QA - NAO PUBLICAR",fill=(245,245,245))
    out.parent.mkdir(parents=True,exist_ok=True)
    image.save(out,quality=85)
    if max(drift)<.3:raise IntakeError("movement_not_detected")
    return {"sha256":file_sha(out),"bytes":out.stat().st_size,
            "samples_seconds":list(samples),"frame_drift":drift,
            "no_static_slideshow_proven_in_samples":True}

def render_preview(src,out,s,meta):
    from PIL import Image,ImageDraw
    with tempfile.TemporaryDirectory(prefix="vnc-watermark-") as temp:
        overlay=Path(temp)/"w.png"
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rectangle((0,0,W,52),fill=(0,0,0,170))
        d.text((9,16),f"VERBO NO CHAO {s['id']} / PREVIA - NAO PUBLICAR",fill=(255,255,255,255))
        im.save(overlay)
        crop=meta["crop_width"]
        f=(f"[0:v]fps={FPS},crop={crop}:{meta['height']}:(iw-{crop})/2:0,"
           f"scale={W}:{H}:flags=lanczos,setsar=1[scene];"
           "[scene][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,format=yuv420p[v]")
        checked(["ffmpeg","-nostdin","-v","error","-y","-i",str(src),
          "-loop","1","-i",str(overlay),"-filter_complex",f,"-map","[v]","-an",
          "-frames:v",str(s["frames"]),"-r",str(FPS),"-c:v","libx264",
          "-preset","veryfast","-crf","24","-movflags","+faststart",str(out)],150)
    p=probe(out);ss=p.get("streams",[])
    if len(ss)!=1 or ss[0].get("codec_type")!="video":
        raise IntakeError("qa_audio_or_extra_streams")
    v=ss[0]
    if (v.get("codec_name")!="h264" or
      (int(v.get("width",0)),int(v.get("height",0)))!=(W,H) or
      v.get("avg_frame_rate")!="30/1" or int(v.get("nb_frames",0))!=s["frames"] or
      abs(float(p["format"]["duration"])-s["frames"]/FPS)>.03):
        raise IntakeError("qa_video_not_exact_cut")
    checked(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(out),
             "-map","0:v:0","-an","-f","null","-"],75)
    return {"sha256":file_sha(out),"bytes":out.stat().st_size,
            "width":W,"height":H,"fps":FPS,"frames":s["frames"],
            "duration_seconds":float(p["format"]["duration"]),
            "full_decode_pass":True,"audio":False,"watermarked":True}

def run(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    summary={"project_id":"VERBO_NO_CHAO_EXCLUSIVO","episode_id":"VNC-W01-E1",
             "status":"BLOCKED_UNTIL_ALL_PHYSICAL_QA_PASSES","sources":{},
             "publication_authorized":False,"rights_cleared":False,
             "master_allowed":False,"owner_approved":False,
             "original_source_persisted":False}
    try:
        verify()
        for name,s in SOURCES.items():
            entry={"status":"BLOCKED_SOURCE_NOT_VERIFIED","video_id":s["id"],
                   "page_url":s["page"],"license_page_label":"Mixkit Stock Video Free License",
                   "editorial_intent":s["narrative"],"owner_approved":False,
                   "rights_cleared":False,"master_allowed":False}
            summary["sources"][name]=entry
            try:
                with tempfile.TemporaryDirectory(prefix=f"vnc-{name}-") as temp:
                    src,receipt=download(s,Path(temp))
                    entry["source"]=receipt
                    meta=source_probe(src)
                    entry["technical_source"]=meta
                    contact=out/f"{name}_MIXKIT_{s['id']}_3_REAL_FRAMES.jpg"
                    preview=out/f"{name}_MIXKIT_{s['id']}_MOTION_QA_NOT_MASTER.mp4"
                    entry["contact"]=frames_contact(src,contact,meta,name)
                    entry["preview"]=render_preview(src,preview,s,meta)
                    entry["status"]="PHYSICAL_MOVING_QA_PASS_EDITORIAL_PENDING"
            except Exception as e:
                entry["error_type"]=type(e).__name__
                entry["error_code"]=str(e)[:130] if isinstance(e,IntakeError) else "provider_or_media_error"
                (out/f"{name}_MIXKIT_{s['id']}_MOTION_QA_NOT_MASTER.mp4").unlink(missing_ok=True)
        summary["status"]="PHYSICAL_BOTH_PASS_EDITORIAL_PENDING" if all(
            x.get("status")=="PHYSICAL_MOVING_QA_PASS_EDITORIAL_PENDING" for x in summary["sources"].values()
        ) else "PARTIAL_OR_ALL_BLOCKED_PHYSICAL"
    except Exception as e:
        summary["fatal_error_type"]=type(e).__name__
        summary["fatal_error_code"]=str(e) if isinstance(e,IntakeError) else "contract_error"
    (out/"S03_S10_MIXKIT_QA_REPORT.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":summary["status"],"sources":{k:v["status"] for k,v in summary["sources"].items()},
                      "master_allowed":False,"publication_authorized":False}))
    return 0 if summary["status"]=="PHYSICAL_BOTH_PASS_EDITORIAL_PENDING" else 2

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    raise SystemExit(run(p.parse_args().out))

if __name__=="__main__": main()
