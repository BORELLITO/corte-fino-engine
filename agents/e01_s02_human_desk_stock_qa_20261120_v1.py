"""VNC E01 S02: isolated real Pexels hand/desk stock physical QA, never master.

Single exact source, no API key/AI generator, no third party auth. Reuses
strict origin-limited Pexels downloader. Only short watermarked review media
leaves temporary workdir. Source cannot be released from this agent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from agents.e01_stock_candidates import ROOT
from agents.e01_s01_multi_stock_pilot_v1 import download_source, probe
from agents.e01_s01_single_take_stock_qa import crop_native, frame_at, run_cmd
from agents.e01_s01_night_rain_motif_probe_v1 import watermark

CONTRACT = Path("contracts/e01_s02_human_desk_stock_preflight_20261120_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
S01_APPROVAL = Path("contracts/e01_s01_owner_visual_approval_20261119_v1.json")
SOURCE_ID = 9903488
SOURCE_PAGE = "https://www.pexels.com/video/a-man-organizing-the-things-on-his-table-9903488/"
S01_SHA = "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961"
S02_GRADE_SHA = "0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3"
COMPOSITE_SHA = "979fcb7d630177efc99e76baa98adc0d34cf0d3a89beaf06484060c7bdd6e5f6"
SCRIPT_SHA = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
W,H,FPS,FRAMES = 720,1280,30,147
SAMPLES=(0.5,2.4,4.5)
PREVIEW_NAME="S02_HAND_DESK_9903488_QA_NOT_MASTER.mp4"
FRAMES_NAME="S02_HAND_DESK_9903488_FRAMES_QA.jpg"
REPORT_NAME="S02_HAND_DESK_9903488_REPORT.json"


class S02HandDeskError(ValueError):
    pass


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as r:
        for piece in iter(lambda:r.read(1048576),b""):
            h.update(piece)
    return h.hexdigest()


def validate_contract(root=ROOT, data=None):
    root=Path(root)
    if data is None:
        data=json.loads((root/CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise S02HandDeskError("manifest_not_object")
    strict={
        "schema_version":"1.0.0","project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id":"VNC-W01-E1","scene_id":"VNC-E01V2-S02",
        "purpose":"S02_HUMAN_HAND_ON_WOODEN_DESK_STOCK_PHYSICAL_REVIEW_ONLY",
        "locked_story_sha256":SCRIPT_SHA,
        "source_limit_bytes":160000000,
        "initial_state":"SOURCE_PAGE_VERIFIED_MP4_NOT_DOWNLOADED",
        "result_proof_level":"REQUIRES_REAL_MP4_FFPROBE_FRAMES_AND_VISUAL_REVIEW",
    }
    for k,v in strict.items():
        if type(data.get(k)) is not type(v) or data[k]!=v:
            raise S02HandDeskError("manifest_drift_"+k)
    candidate=data.get("candidate",{})
    facts={
        "id":SOURCE_ID,"creator":"Ron Lach","provider":"Pexels",
        "page_url":SOURCE_PAGE,"listing_width":2160,"listing_height":4096,
        "listing_duration_seconds":32,"listing_fps":25,
        "listing_licence":"Free","rights_cleared":False,
        "media_physically_downloaded":False,"artistic_approval":False,
        "real_camera_origin_independently_proven":False,
        "subject_same_as_s01_proven":False,
    }
    if not isinstance(candidate,dict):
        raise S02HandDeskError("candidate_missing")
    for k,v in facts.items():
        if type(candidate.get(k)) is not type(v) or candidate[k]!=v:
            raise S02HandDeskError("candidate_drift_"+k)
    out=data.get("output",{})
    checks={
        "width":W,"height":H,"fps":FPS,"frames":FRAMES,
        "cut_start_seconds":0,"samples_seconds":list(SAMPLES),
        "watermark":"PREVIA DE QA - NAO PUBLICAR","audio":False,
        "captions":False,"full_preview_decode_required":True,
        "compare_against_s01_approved_sha256":S01_SHA,
    }
    if not isinstance(out,dict):
        raise S02HandDeskError("output_missing")
    for k,v in checks.items():
        if type(out.get(k)) is not type(v) or out[k]!=v:
            raise S02HandDeskError("preview_drift_"+k)
    app=data.get("approval_scope",{})
    flags={
        "s01_visual_approved":True,"s02_visual_approved":False,
        "dont_replace_existing_s02_candidate":True,
        "rights_cleared":False,"master_allowed":False,
        "publication_authorized":False,"new_spending_authorized":False,
        "merge_authorized":False,
    }
    for k,v in flags.items():
        if not isinstance(app,dict) or type(app.get(k)) is not type(v) or app[k]!=v:
            raise S02HandDeskError("release_guard_drift_"+k)
    old=data.get("historical_candidate_to_preserve",{})
    if (old.get("source_id") != 7034348 or
        old.get("grade_a_preview_sha256")!=S02_GRADE_SHA or
        old.get("full_qa_with_voice_and_captions_sha256")!=COMPOSITE_SHA or
        old.get("status")!="UNAPPROVED_EXISTING_CANDIDATE_NOT_DISCARDED"):
        raise S02HandDeskError("approved_baseline_or_prior_candidate_drift")
    scene=data.get("expected_storyboard_scene",{})
    storyboard=json.loads((root/STORY).read_text(encoding="utf-8"))
    s02=storyboard["scenes"][1]
    if (storyboard.get("script_sha256")!=SCRIPT_SHA or
        storyboard.get("episode_id")!="VNC-W01-E1" or
        scene.get("start_seconds")!=5.74 or scene.get("end_seconds")!=10.62 or
        s02.get("id")!="VNC-E01V2-S02" or
        s02.get("title")!="A dor da espera" or
        s02.get("start_seconds")!=5.74 or s02.get("end_seconds")!=10.62 or
        "same anonymous adult hand" not in s02.get("visual_prompt","") or
        "near analog clock" not in s02.get("visual_prompt","") or
        s02.get("approved_for_export") is not False):
        raise S02HandDeskError("storyboard_integrity_or_semantic_drift")
    approval=json.loads((root/S01_APPROVAL).read_text(encoding="utf8"))
    if (approval.get("approval_status")!="APPROVED_S01_VISUAL_DIRECTION_ONLY"
        or approval.get("approval_scope",{}).get("preview_sha256")!=S01_SHA
        or approval.get("approval_scope",{}).get("extend_to_other_scenes_automatically") is not False):
        raise S02HandDeskError("s01_approval_scope_drift")
    return candidate


def evidence_sheet(frames,path:Path):
    from PIL import Image,ImageDraw,ImageStat,ImageChops
    if len(frames)!=3 or any(x.size!=(216,384) for x in frames):
        raise S02HandDeskError("bad_qa_frames")
    sheet=Image.new("RGB",(648,426),(18,18,18))
    d=ImageDraw.Draw(sheet)
    luma=[]
    for i,f in enumerate(frames):
        sheet.paste(f,(i*216,0))
        luma.append(round(ImageStat.Stat(f.convert("L")).mean[0],2))
        d.rectangle((i*216+4,4,i*216+78,23),fill=(13,13,13))
        d.text((i*216+8,8),f"{SAMPLES[i]:.1f}s",fill=(245,245,245))
    drift=[
        round(ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0],3)
        for a,b in zip(frames,frames[1:])
    ]
    d.text((7,397),"S02 HAND/DESK 9903488 - NAO APROVADO / NAO PUBLICAR",fill=(245,245,245))
    sheet.save(path,format="JPEG",quality=88)
    return {"file":path.name,"sha256":sha(path),"luma_means":luma,
            "sample_times":list(SAMPLES),"frame_diff_means":drift,
            "physical_motion_samples_pass":any(d>0.35 for d in drift),
            "not_camera_origin_proof":True}


def output_probe(path):
    raw=run_cmd(["ffprobe","-v","error","-show_entries",
                 "format=duration:stream=codec_name,codec_type,width,height,nb_frames,avg_frame_rate",
                 "-of","json",str(path)],25).stdout
    obj=json.loads(raw)
    ss=obj.get("streams",[])
    if len(ss)!=1 or ss[0].get("codec_type")!="video":
        raise S02HandDeskError("preview_contains_audio_or_other_stream")
    v=ss[0]
    if (v.get("codec_name")!="h264" or
        (v.get("width"),v.get("height"))!=(W,H) or
        v.get("avg_frame_rate")!="30/1" or
        int(v.get("nb_frames",0))!=FRAMES or
        abs(float(obj.get("format",{}).get("duration",0))-FRAMES/FPS)>0.025):
        raise S02HandDeskError("preview_wrong_resolution_frames")
    run_cmd(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(path),
             "-map","0:v:0","-an","-f","null","-"],95)
    return {"width":W,"height":H,"fps":FPS,"frames":FRAMES,
            "seconds":float(obj["format"]["duration"]),
            "audio":False,"full_preview_decode_pass":True}


def produce(out:Path,root=ROOT):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    movie=out/PREVIEW_NAME
    sheet=out/FRAMES_NAME
    report=out/REPORT_NAME
    state={
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id":"VNC-W01-E1","scene_id":"VNC-E01V2-S02",
        "status":"BLOCKED_SOURCE_OR_PHYSICAL_QA",
        "source_id":SOURCE_ID,
        "s01_visual_approved_unchanged":True,
        "s02_visual_approved":False,
        "media_license_individually_verified":False,
        "same_person_continuity_verified":False,
        "master_allowed":False,"publication_authorized":False,
        "new_spending":False,"source_original_persisted":False,
        "artistic_approval_proven":False,
    }
    try:
        validate_contract(root)
        with tempfile.TemporaryDirectory(prefix="vnc_s02_hand_desk_stock_") as folder:
            work=Path(folder)
            original,receipt=download_source(
                {"id":SOURCE_ID,"page":SOURCE_PAGE},work)
            meta=probe(original,min_seconds=5.0,min_width=1080,min_height=1920)
            native=crop_native(meta["width"],meta["height"])
            if native[0]<1080 or native[1]<1920:
                raise S02HandDeskError("native_portrait_resolution_too_low")
            # No claim that Pexels metadata independently proves camera capture.
            frames=[frame_at(original,t,meta["width"],meta["height"]) for t in SAMPLES]
            frame_qa=evidence_sheet(frames,sheet)
            if not frame_qa["physical_motion_samples_pass"]:
                raise S02HandDeskError("motion_samples_not_proven")
            overlay=work/"QA_watermark.png"
            watermark(overlay)
            vf=(f"[0:v]fps={FPS},crop={native[0]}:{native[1]}:"
                f"(iw-{native[0]})/2:(ih-{native[1]})/2,"
                f"scale={W}:{H}:flags=lanczos,setsar=1[base];"
                "[base][1:v]overlay=0:0:repeatlast=1:shortest=0:format=auto,"
                "format=yuv420p[v]")
            run_cmd(["ffmpeg","-nostdin","-v","error","-y",
                     "-i",str(original),"-loop","1","-i",str(overlay),
                     "-filter_complex",vf,"-map","[v]","-an",
                     "-frames:v",str(FRAMES),"-r",str(FPS),"-c:v","libx264",
                     "-preset","veryfast","-crf","24","-movflags","+faststart",
                     str(movie)],150)
            op=output_probe(movie)
            state.update(status="PHYSICAL_REVIEW_CLIP_READY_UNAPPROVED",
                         source={**receipt,**meta,
                                 "native_portrait_crop":list(native),
                                 "source_full_decode_not_claimed":True},
                         frames=frame_qa,
                         preview={**op,"file":movie.name,"sha256":sha(movie),
                                  "bytes":movie.stat().st_size,"watermarked":True})
            original.unlink(missing_ok=True)
    except Exception as exc:
        movie.unlink(missing_ok=True)
        state["error_type"]=type(exc).__name__
        state["error_code"]=str(exc)[:180] if isinstance(exc,S02HandDeskError) else "provider_or_media_process_error"
    report.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":state["status"],
                      "scene":"VNC-E01V2-S02","rights_cleared":False,
                      "master_allowed":False,"publication_authorized":False}))
    return 0 if state["status"]=="PHYSICAL_REVIEW_CLIP_READY_UNAPPROVED" else 2


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    raise SystemExit(produce(parser.parse_args().out))


if __name__=="__main__":
    main()
