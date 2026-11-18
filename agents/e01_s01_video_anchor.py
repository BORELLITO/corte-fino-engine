"""Prepare S01 physically-proven reference frames; never silently approve actor identity.

This module **does not generate AI video** or spend GPU credits. It is called
after the scheduled 5.8 second video generation returns real MP4 bytes and
requires the source's QA report to match the file's SHA256. It generates
candidate images and a contact sheet only for creative-director review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from agents.e01_ltx23_s01_v2_render import (
    OUT, REPORT, SCENE_SECONDS, inspect, assess_video_eligibility,
)
from agents.e01_stock_candidates import ROOT, require

BLUEPRINT = Path("contracts/e01_room_a_reference_handoff_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
EXPECTED = (
    "VNC-E01V2-S01", "VNC-E01V2-S02", "VNC-E01V2-S06",
    "VNC-E01V2-S07", "VNC-E01V2-S08", "VNC-E01V2-S09",
    "VNC-E01V2-S11", "VNC-E01V2-S12",
)
SHA_SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
SHA_AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
TIMES = (0.0, 0.9, 2.35, 3.85, 5.45)
SAMPLE_FPS = 6
SMALL_WIDTH = 72
SMALL_HEIGHT = 128
FRAME_BYTES = SMALL_WIDTH * SMALL_HEIGHT
MIN_MEAN_LUMA_DELTA = 0.35
MIN_ACTIVE_PAIR_FRACTION = 0.20

def validate_blueprint(root:Path=ROOT, data:dict|None=None)->dict:
    if data is None:
        data=json.loads((root/BLUEPRINT).read_text(encoding="utf-8"))
    story=json.loads((root/STORY).read_text(encoding="utf-8"))
    require(isinstance(data,dict) and data.get("schema_version")=="1.0.0"
        and data.get("episode_id")==story.get("episode_id")=="VNC-W01-E1"
        and data.get("project")=="verbo-no-chao"
        and data.get("source_storyboard")==str(STORY)
        and data.get("source_scene_id")==EXPECTED[0]
        and data.get("script_sha256")==story.get("script_sha256")==SHA_SCRIPT
        and data.get("audio_sha256")==story.get("audio_sha256")==SHA_AUDIO
        and data.get("source_reference_status")==
          "WAITING_FOR_PHYSICALLY_VALID_AND_EDITORIALLY_APPROVED_S01"
        and data.get("first_frame_conditioning_verified_in_official_source") is True
        and data.get("first_frame_conditioning_cannot_guarantee_identity") is True,
        "room_reference:source_or_episode_drift")
    require(data.get("approved_source_video_sha256") is None
        and data.get("approved_first_frame_sha256") is None
        and data.get("reference_strategy")==
           "START_WITH_APPROVED_S01_FIRST_FRAME_THEN_CREATE_SCENE_MATCHED_FRAMES"
        and data.get("verified_provider_implementation_url")==
           "https://huggingface.co/spaces/Lightricks/LTX-2-3/blob/main/app.py",
        "room_reference:unearned_reference_approval")
    for key in (
        "source_rights_verified","reference_qa_verified",
        "same_person_across_scenes_verified","multiscene_generation_authorized",
        "master_1080x1920_rendered","publication_authorized",
        "automation_may_generate_followups_without_director_approval",
    ):
        require(data.get(key) is False,"room_reference:unearned_release_"+key)
    require(data.get("technical_preview_not_master") is True,
        "room_reference:missing_preview_disclosure")
    shots=data.get("room_a_scene_plan")
    original={s["id"]:s for s in story["scenes"]}
    require(isinstance(shots,list) and len(shots)==len(EXPECTED),
        "room_reference:shots_missing")
    for idx,shot in enumerate(shots):
        ident=EXPECTED[idx]
        baseline=original[ident]
        require(shot.get("id")==ident
            and shot.get("start_seconds")==baseline["start_seconds"]
            and shot.get("end_seconds")==baseline["end_seconds"]
            and shot.get("narration_block")==baseline["narration_block"]
            and shot.get("initial_reference_scene")==(
                None if idx==0 else EXPECTED[0])
            and shot.get("asset_sha256") is None
            and shot.get("actor_continuity_requires_visual_qa") is True
            and shot.get("editorial_approved") is False
            and shot.get("can_enter_master") is False,
            "room_reference:time_shift_or_false_shot_approval")
    return {"status":"ROOM_A_REFERENCE_PLAN_VALID_UNGENERATED",
            "scene_count":len(shots),"first_frame_conditioning_supported":True,
            "reference_images_editorially_approved":0,
            "publication_authorized":False}

def validate_source_report(report:dict,media:dict,filename:str)->None:
    require(isinstance(report,dict)
        and report.get("episode_id")=="VNC-W01-E1"
        and report.get("scene_id")=="VNC-E01V2-S01"
        and report.get("media_origin")=="AI_GENERATED_FICTIONAL_VIDEO"
        and report.get("status")==
            "PHYSICAL_AI_PREVIEW_ELIGIBLE_FOR_EDITORIAL_REVIEW_ONLY"
        and report.get("video_file")==filename
        and report.get("technically_eligible_for_editorial") is True,
        "anchor:unverified_scene_or_video_report")
    for key in ("rights_cleared","approved_for_master","publication_authorized",
                "origin_and_usage_license_review_complete",
                "visual_continuity_verified",
                "closed_notebook_and_rain_visually_verified"):
        require(report.get(key) is False,"anchor:false_approval_"+key)
    rm=report.get("media")
    require(isinstance(rm,dict) and rm.get("sha256")==media.get("sha256")
         and rm.get("bytes")==media.get("bytes")
         and abs(rm.get("duration_seconds",0)-media.get("duration_seconds",0))<=0.04
         and rm.get("width")==media.get("width")
         and rm.get("height")==media.get("height")
         and assess_video_eligibility(media)==
               "PHYSICAL_AI_PREVIEW_ELIGIBLE_FOR_EDITORIAL_REVIEW_ONLY",
         "anchor:source_integrity_or_duration_invalid")

def byte_motion_stats(gray:bytes,pixel_count:int=FRAME_BYTES)->dict:
    require(isinstance(gray,bytes)
        and isinstance(pixel_count,int) and pixel_count>=4
        and len(gray)%pixel_count==0,
        "anchor:malformed_decoded_frame_bytes")
    frames=len(gray)//pixel_count
    require(frames>=6,"anchor:insufficient_frames")
    changes=[]
    for i in range(1,frames):
        lo=(i-1)*pixel_count
        prev=gray[lo:lo+pixel_count]
        curr=gray[lo+pixel_count:lo+2*pixel_count]
        changes.append(sum(abs(a-b) for a,b in zip(prev,curr))/pixel_count)
    mean_change=sum(changes)/len(changes)
    moving_frac=sum(s>=0.5 for s in changes)/len(changes)
    return {
      "sampled_frames":frames,
      "mean_absolute_luma_change":round(mean_change,4),
      "fraction_active_pairs":round(moving_frac,4),
      "motion_signal_detected":(
          mean_change>=MIN_MEAN_LUMA_DELTA
          and moving_frac>=MIN_ACTIVE_PAIR_FRACTION),
      "not_a_semantic_quality_or_actor_consistency_test":True,
    }

def extract_gray_motion(path:Path)->dict:
    cmd=["ffmpeg","-nostdin","-v","error","-i",str(path),
         "-t","6.2","-an","-vf",
         f"fps={SAMPLE_FPS},scale={SMALL_WIDTH}:{SMALL_HEIGHT}:flags=bilinear,format=gray",
         "-pix_fmt","gray","-f","rawvideo","pipe:1"]
    proc=subprocess.run(cmd,capture_output=True,timeout=70,check=False)
    require(proc.returncode==0 and not proc.stderr,
        "anchor:ffmpeg_gray_decode_error")
    return byte_motion_stats(proc.stdout)

def hash_file(path:Path)->str:
    sha=hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1048576),b""):
            sha.update(block)
    return sha.hexdigest()

def make_candidate_frames(video:Path,report_path:Path,output:Path)->dict:
    validate_blueprint()
    require(video.is_file() and report_path.is_file(),
        "anchor:video_or_source_report_missing")
    media=inspect(video)
    report=json.loads(report_path.read_text(encoding="utf-8"))
    validate_source_report(report,media,video.name)
    motion=extract_gray_motion(video)
    require(motion["motion_signal_detected"],
        "anchor:near_static_video_not_real_motion_proof")
    require(max(TIMES)<SCENE_SECONDS
        and media["duration_seconds"]>=SCENE_SECONDS,
        "anchor:sampling_outside_canonical_scene")
    output.mkdir(parents=True,exist_ok=True)
    refs=[]
    for i,time_s in enumerate(TIMES):
        file=output/f"reference_sample_{i+1:02d}.png"
        cmd=["ffmpeg","-nostdin","-y","-v","error","-i",str(video),
             "-ss",str(time_s),"-frames:v","1",
             "-pix_fmt","rgb24",str(file)]
        res=subprocess.run(cmd,capture_output=True,text=True,timeout=35,check=False)
        require(res.returncode==0 and file.is_file()
            and file.stat().st_size>500,
            "anchor:missing_or_invalid_sample_"+str(i))
        refs.append({"index":i+1,"frame_second":time_s,"name":file.name,
                     "sha256":hash_file(file),
                     "director_approved":False})
    inputs=[]
    for item in refs:
        inputs+=["-i",str(output/item["name"])]
    names="".join(f"[{j}:v]scale=144:256[p{j}];" for j in range(len(refs)))
    names+="".join(f"[p{j}]" for j in range(len(refs)))
    names+=f"hstack=inputs={len(refs)}[v]"
    contact=output/"s01_five_frame_contact_sheet_EDITORIAL_ONLY.png"
    montage=subprocess.run(["ffmpeg","-nostdin","-y","-v","error",
         *inputs,"-filter_complex",names,"-map","[v]",
         "-frames:v","1",str(contact)],
         capture_output=True,text=True,timeout=40,check=False)
    require(montage.returncode==0 and contact.is_file()
            and contact.stat().st_size>500,
            "anchor:contact_sheet_build_failed")
    data={
      "schema_version":"1.0.0",
      "episode_id":"VNC-W01-E1",
      "scene_id":"VNC-E01V2-S01",
      "source_sha256":media["sha256"],
      "source_mp4_file":video.name,
      "source_mp4_duration_seconds":media["duration_seconds"],
      "source_mp4_width":media["width"],
      "source_mp4_height":media["height"],
      "original_camera_footage":False,
      "source_kind":"GENERATED_AI_VIDEO",
      "model":"Lightricks/LTX-2.3",
      "source_model_license_review_complete":False,
      "motion_check":motion,
      "source_video_exact_storyboard_compliance_verified":False,
      "actor_identity_continuity_verified":False,
      "rain_and_closed_notebook_verified":False,
      "reference_promoted_to_i2v":False,
      "reference_for_other_scenes_approved":False,
      "scene_e01_approved_for_master":False,
      "master_resolution_1080x1920":False,
      "publication_authorized":False,
      "candidate_start_frame_sha256":refs[0]["sha256"],
      "samples":refs,
      "contact_sheet_file":contact.name,
      "contact_sheet_sha256":hash_file(contact),
      "status":"FRAME_ANCHOR_CANDIDATES_AWAIT_DIRECTORIAL_VISUAL_QA",
    }
    (output/"continuity_reference_evidence.json").write_text(
        json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-blueprint",action="store_true")
    parser.add_argument("--video",type=Path,
      default=OUT/"E01_S01_V2_6SEC_LTX23_AI_PREVIEW_NOT_MASTER.mp4")
    parser.add_argument("--source-report",type=Path,default=REPORT)
    parser.add_argument("--output",type=Path,default=OUT/"continuity_reference_review")
    args=parser.parse_args()
    try:
        if args.check_blueprint:
            result=validate_blueprint()
        else:
            result=make_candidate_frames(args.video,args.source_report,args.output)
        print(json.dumps({
          "status":result["status"],"publication_authorized":False,
          "reference_approved":False},ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,
            subprocess.TimeoutExpired) as err:
        print(json.dumps({"status":"BLOCKED_S01_REFERENCE_HANDOFF",
          "failure_type":type(err).__name__,"publication_authorized":False}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
