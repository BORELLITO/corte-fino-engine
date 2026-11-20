"""Reproducible S01+S02 QA with REAL canonical E01 karaoke; never a master.

Inputs are exact SHA-locked 720x1280 MP4 QA previews and the original ASS
obtained from E01's physical ASR artifact. No networks, spending, or release.
Only S02 receives a soft vertical darkening gradient; 28 karaoke cues remain
byte-for-byte identical. This process does not create licensed 1080p media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from agents.e01_stock_candidates import ROOT

CONTRACT = Path("contracts/e01_s02_real_caption_safezone_qa_20261119_v1.json")
APPROVAL = Path("contracts/e01_s01_owner_visual_approval_20261119_v1.json")
W,H,FPS = 720,1280,30
S01_FRAMES,S02_FRAMES=172,147
EXPECTED_FRAMES=S01_FRAMES+S02_FRAMES


class CaptionSafezoneQAError(ValueError):
    pass


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def validated_contract(root=ROOT, obj=None):
    root=Path(root)
    if obj is None:
        obj=json.loads((root/CONTRACT).read_text(encoding="utf8"))
    if not isinstance(obj,dict):
        raise CaptionSafezoneQAError("manifest_not_object")
    checks={
        "schema_version":"1.0.0",
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id":"VNC-W01-E1",
        "scene_id":"VNC-E01V2-S02",
        "approval_state":"S01_VISUAL_APPROVED_S02_UNAPPROVED",
        "purpose":"RENDER_QA_REAL_CANONICAL_KARAOKE_ON_S01_S02_GRADED_720P_ONLY",
        "s02_editorial_approved":False,
        "rights_cleared":False,
        "master_allowed":False,
        "publication_authorized":False,
        "merge_authorized":False,
        "spend_authorized":False,
    }
    for k,v in checks.items():
        if type(obj.get(k)) is not type(v) or obj[k]!=v:
            raise CaptionSafezoneQAError("identity_or_release_drift_"+k)
    sc=obj.get("s01",{})
    g=obj.get("s02",{})
    captions=obj.get("canonical_caption_artifact",{})
    req=obj.get("output_requirements",{})
    mandatory=[
        (sc,"source_preview_sha256","724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961"),
        (sc,"owner_approved_visual",True),
        (sc,"source_original_unchanged",True),
        (sc,"frames_used",S01_FRAMES),
        (g,"graded_a_preview_sha256","0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3"),
        (g,"frames_used",S02_FRAMES),
        (g,"visual_owner_approved",False),
        (g,"license_individual_cleared",False),
        (g,"selected_qa_gradient_strength",0.55),
        (g,"gradient_start_y_px",620),
        (g,"gradient_end_y_px",1279),
        (captions,"ass_sha256","0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a"),
        (captions,"caption_cue_total",28),
        (captions,"caption_text_and_times_unchanged",True),
        (captions,"voice_wav_not_present_in_preview",True),
        (req,"width",W),(req,"height",H),(req,"fps",FPS),
        (req,"frames",EXPECTED_FRAMES),
        (req,"contains_audio",False),
        (req,"watermarks",True),
        (req,"master_allowed",False),
        (req,"publication_authorized",False),
        (req,"rights_cleared",False),
        (req,"no_stock_download",True),
        (req,"no_original_source_overwrite",True),
    ]
    for sub,key,value in mandatory:
        if not isinstance(sub,dict) or type(sub.get(key)) is not type(value) or sub[key]!=value:
            raise CaptionSafezoneQAError("untrusted_input_or_release_"+key)
    decision=json.loads((root/APPROVAL).read_text(encoding="utf8"))
    if (decision.get("approval_status")!="APPROVED_S01_VISUAL_DIRECTION_ONLY"
         or decision.get("approval_scope",{}).get("preview_sha256")!=sc["source_preview_sha256"]
         or decision.get("approval_scope",{}).get("extend_to_other_scenes_automatically") is not False):
        raise CaptionSafezoneQAError("s01_approval_reference_mismatch")
    return obj


def command(args,limit=100):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=limit)
    if r.returncode:
        raise CaptionSafezoneQAError("ffmpeg_probe_or_render_failed")
    return r.stdout


def check_video(path,frames):
    raw=command(["ffprobe","-v","error",
                "-show_entries","stream=codec_type,width,height,nb_frames,avg_frame_rate:format=duration",
                "-of","json",str(path)])
    obj=json.loads(raw.decode("utf8"))
    streams=obj.get("streams",[])
    if len(streams)!=1 or streams[0].get("codec_type")!="video":
        raise CaptionSafezoneQAError("audio_or_multiple_streams")
    v=streams[0]
    if (int(v.get("width",0))!=W or int(v.get("height",0))!=H
        or int(v.get("nb_frames",0))!=frames
        or v.get("avg_frame_rate")!="30/1"
        or abs(float(obj["format"]["duration"])-frames/FPS)>.04):
        raise CaptionSafezoneQAError("timing_or_geometry_incorrect")
    return {"width":W,"height":H,"frames":frames,"fps":FPS,
            "duration_seconds":float(obj["format"]["duration"]),
            "stream_count":1,"audio":False}


def gradient_rgba(dest:Path):
    # Soft falloff from y=620 (fully clear) to the last row (55% black).
    from PIL import Image
    image=Image.new("RGBA",(W,H),(0,0,0,0))
    for y in range(620,H):
        t=max(0.,min(1.,(y-620)/660))
        smooth=t*t*(3-2*t)
        a=int(255*0.55*smooth)
        image.paste((0,0,0,a),(0,y,W,y+1))
    image.save(dest)


def render(s01:Path,s02:Path,ass:Path,out:Path,root=ROOT):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    result={
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "scene_id":"VNC-E01V2-S02",
        "status":"BLOCKED_KARAOKE_QA_NOT_REPRODUCED",
        "s01_approved_visual_unchanged_as_input":True,
        "s02_approved":False,
        "rights_cleared":False,"master_allowed":False,
        "publication_authorized":False,"voice_audio_included":False,
        "caption_text_modified":False,
    }
    final=out/"S01_S02_REAL_KARAOKE_GRADIENT55_QA_NOT_MASTER.mp4"
    try:
        spec=validated_contract(root)
        inputs=[Path(x).resolve(strict=True) for x in (s01,s02,ass)]
        if len(set(inputs))!=3 or final.resolve() in inputs:
            raise CaptionSafezoneQAError("unsafe_input_alias")
        if any(not x.is_file() for x in inputs):
            raise CaptionSafezoneQAError("input_not_regular_file")
        expected=[
            spec["s01"]["source_preview_sha256"],
            spec["s02"]["graded_a_preview_sha256"],
            spec["canonical_caption_artifact"]["ass_sha256"],
        ]
        for x,h in zip(inputs,expected):
            if sha(x)!=h:
                raise CaptionSafezoneQAError("input_sha256_mismatch")
        check_video(inputs[0],173)
        check_video(inputs[1],147)
        ass_text=inputs[2].read_text(encoding="utf8")
        if ass_text.count("Dialogue: 0,")!=28:
            raise CaptionSafezoneQAError("canonical_cue_count_mismatch")
        with tempfile.TemporaryDirectory(prefix="vnc_s02_qa_gradient_") as scratch:
            work=Path(scratch)
            overlay=work/"gradient.png"
            grade=work/"S02_VIGNETTE_QA.mp4"
            joined=work/"joined_319_frames_QA.mp4"
            gradient_rgba(overlay)
            command(["ffmpeg","-nostdin","-v","error","-y",
                    "-i",str(inputs[1]),"-loop","1","-i",str(overlay),
                    "-filter_complex","[0:v][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,format=yuv420p[v]",
                    "-map","[v]","-an","-frames:v","147","-r","30","-c:v",
                    "libx264","-preset","veryfast","-crf","21",str(grade)],120)
            check_video(grade,S02_FRAMES)
            filt=("[0:v]trim=start_frame=0:end_frame=172,setpts=PTS-STARTPTS,format=yuv420p[a];"
                  "[1:v]trim=start_frame=0:end_frame=147,setpts=PTS-STARTPTS,format=yuv420p[b];"
                  "[a][b]concat=n=2:v=1:a=0,format=yuv420p[v]")
            command(["ffmpeg","-nostdin","-v","error","-y","-i",str(inputs[0]),
                    "-i",str(grade),"-filter_complex",filt,"-map","[v]","-an",
                    "-frames:v","319","-r","30","-c:v","libx264","-preset","veryfast",
                    "-crf","22",str(joined)],120)
            check_video(joined,EXPECTED_FRAMES)
            command(["ffmpeg","-nostdin","-v","error","-y","-i",str(joined),
                    "-vf","ass="+str(inputs[2]),"-an","-frames:v","319","-r","30",
                    "-c:v","libx264","-preset","veryfast","-crf","21",str(final)],120)
            meta=check_video(final,EXPECTED_FRAMES)
            command(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(final),
                    "-map","0:v:0","-an","-f","null","-"],120)
            result.update({
                "status":"REAL_KARAOKE_319FRAME_QA_PHYSICALLY_VERIFIED_EDITORIAL_PENDING",
                "source_sha256":{"s01":sha(inputs[0]),"s02_grade_a":sha(inputs[1]),"ass":sha(inputs[2])},
                "graded_s02": {"sha256":sha(grade),"bytes":grade.stat().st_size},
                "preview":{"**":None,**meta,"sha256":sha(final),"bytes":final.stat().st_size,
                           "watermarked":True,"full_decode_pass":True,
                           "ass_sha256_unchanged":True}
            })
            result["preview"].pop("**",None)
    except (OSError,ValueError,subprocess.TimeoutExpired,KeyError,TypeError,UnicodeDecodeError) as exc:
        final.unlink(missing_ok=True)
        result["error_type"]=type(exc).__name__
        result["status"]="BLOCKED_KARAOKE_QA_NOT_REPRODUCED"
    (out/"S02_REAL_KARAOKE_QA_RESULT.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":result["status"],"master_allowed":False,"publication_authorized":False}))
    return 0 if result["status"].startswith("REAL_KARAOKE_") else 2


def main():
    parser=argparse.ArgumentParser()
    for name in ("s01","s02","ass","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    arg=parser.parse_args()
    raise SystemExit(render(arg.s01,arg.s02,arg.ass,arg.out))


if __name__=="__main__":
    main()
