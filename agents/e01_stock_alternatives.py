"""Fail-closed intake of a separate E01 replacement-video sample batch.

No MP4 or individual frame is published. Source media is temporary inside CI.
A contact sheet is for internal QA only, never a clearance of rights.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from agents.e01_stock_candidates import ROOT, StockIntakeError, require, _https_url, probe_item
from agents.e01_stock_frame_qa import FRACTIONS, sample_frame, image_metrics, contact_sheet

PATH = Path("contracts/e01_v2_stock_alternatives_v1.json")
STORYBOARD = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
DECISIONS = Path("contracts/e01_v2_stock_editorial_review_v1.json")
CANONICAL_VIDEO_IDS = {34479513,6860448,13017069,32421244}
REJECTED_SOURCE_IDS = {40417800,7350189,5904567}
EXPECTED_SCENES = {
    "E01V2-ALT-S03-B":"VNC-E01V2-S03",
    "E01V2-ALT-S08-B":"VNC-E01V2-S08",
    "E01V2-ALT-S09-B":"VNC-E01V2-S09",
    "E01V2-ALT-S09-C":"VNC-E01V2-S09",
}

def check(root: Path = ROOT, document: dict | None = None) -> dict:
    if document is None:
        document = json.loads((root/PATH).read_text(encoding="utf-8"))
    require(isinstance(document,dict) and
        document.get("schema_version")=="1.0.0" and
        document.get("project")=="verbo-no-chao" and
        document.get("episode_id")=="VNC-W01-E1" and
        document.get("candidate_version")==2 and
        document.get("stage")=="REPLACEMENT_RESEARCH_NOT_PHYSICAL_QA" and
        document.get("parent_rejected_decisions")==str(DECISIONS) and
        document.get("source_storyboard")==str(STORYBOARD) and
        document.get("full_video_review_completed") is False and
        document.get("third_party_rights_cleared") is False and
        document.get("master_rendered") is False and
        document.get("publication_authorized") is False,
        "alternatives:bad_project_or_unearned_release")
    storyboard=json.loads((root/STORYBOARD).read_text(encoding="utf-8"))
    scenes={s["id"]:s for s in storyboard["scenes"]}
    decisions=json.loads((root/DECISIONS).read_text(encoding="utf-8"))
    rejected={x["scene_id"] for x in decisions["decisions"]
              if x["decision"]=="REJECTED_HARMONY"}
    require(set(EXPECTED_SCENES.values()).issubset(rejected),
            "alternatives:rejected_baseline_changed")
    items=document.get("candidates")
    require(isinstance(items,list) and len(items)==len(EXPECTED_SCENES),
            "alternatives:wrong_candidate_count")
    seen_ids=set();seen_videos=set()
    for i in items:
        require(isinstance(i,dict),"alternatives:not_an_object")
        aid=i.get("asset_id");video_id=i.get("video_id")
        require(aid in EXPECTED_SCENES and aid not in seen_ids and
            i.get("scene_id")==EXPECTED_SCENES[aid] and
            isinstance(video_id,int) and video_id in CANONICAL_VIDEO_IDS and
            video_id not in seen_videos and video_id not in REJECTED_SOURCE_IDS,
            "alternatives:source_scene_repetition_or_wrong_id")
        require(isinstance(i.get("page_url"),str) and
                _https_url(i["page_url"],"www.pexels.com") and
                re.fullmatch(r"/video/[a-z0-9-]+-"+str(video_id)+r"/",
                             urlparse(i["page_url"]).path),
                "alternatives:invalid_source_page")
        require(isinstance(i.get("download_url"),str) and
                _https_url(i["download_url"],"videos.pexels.com") and
                re.fullmatch(r"/video-files/"+str(video_id)+r"/[a-zA-Z0-9_-]+\.mp4",
                             urlparse(i["download_url"]).path),
                "alternatives:invalid_source_file")
        duration=round(scenes[i["scene_id"]]["end_seconds"]-scenes[i["scene_id"]]["start_seconds"],3)
        w,h=i.get("width"),i.get("height")
        require(isinstance(w,int) and isinstance(h,int) and
                w>=1080 and h>=1920 and w*16==h*9 and
                isinstance(i.get("fps"),(int,float)) and i["fps"]>=23 and
                isinstance(i.get("duration_page_seconds"),(int,float)) and
                i["duration_page_seconds"]>=duration,
                "alternatives:bad_geometry_or_duration")
        require(i.get("source_license_name")=="Pexels License" and
                i.get("source_license_url")=="https://www.pexels.com/license/" and
                i.get("page_and_redirect_checked") is True and
                i.get("physical_media_checked") is False and
                i.get("physical_sha256") is None and
                i.get("rights_status")=="PENDING_REVIEW" and
                i.get("editorial_status")=="REQUIRES_REAL_FRAME_REVIEW" and
                i.get("allowed_for_final_master") is False and
                isinstance(i.get("creator"),str) and len(i["creator"])>=2 and
                isinstance(i.get("editorial_intent"),str) and len(i["editorial_intent"])>=20 and
                isinstance(i.get("risk"),str) and len(i["risk"])>=15,
                "alternatives:unearned_asset_approval")
        seen_ids.add(aid);seen_videos.add(video_id)
    require(seen_ids==set(EXPECTED_SCENES) and
            seen_videos==CANONICAL_VIDEO_IDS,
            "alternatives:missing_candidate")
    return {"status":"RESEARCH_VALIDATED_BYTES_NOT_YET_VERIFIED",
            "candidate_count":len(items),"rights_cleared":False,
            "publication_authorized":False}

def execute(root:Path,out:Path,ffprobe:str="ffprobe",ffmpeg:str="ffmpeg")->dict:
    check(root)
    items=json.loads((root/PATH).read_text(encoding="utf-8"))["candidates"]
    out.mkdir(parents=True,exist_ok=True)
    report={"status":"BLOCKED_ALTERNATIVES_QA_INCOMPLETE",
            "episode_id":"VNC-W01-E1","checked_videos":[],
            "contact_sheet":None,"raw_video_persisted":False,
            "full_video_review_completed":False,
            "visual_clearance":False,"rights_clearance":False,
            "master_rendered":False,"publication_authorized":False}
    rows=[]
    try:
        with tempfile.TemporaryDirectory(prefix="vnc_e01_alt_") as folder:
            tmp=Path(folder)
            for item in items:
                source={"id":item["asset_id"],"video_id":item["video_id"],
                    "scene_id":item["scene_id"],"download_url":item["download_url"],
                    "page_duration_seconds":item["duration_page_seconds"],
                    "width":item["width"],"height":item["height"]}
                result=probe_item(source,tmp,ffprobe,ffmpeg)
                movie=tmp/(item["asset_id"]+".mp4")
                frames=[sample_frame(movie,result["duration_seconds"]*fraction,ffmpeg)
                        for fraction in FRACTIONS]
                metrics=image_metrics(frames)
                report["checked_videos"].append({**result,"sampled_frames_qa":metrics,
                    "editorial_status":"REQUIRES_REAL_FRAME_REVIEW",
                    "third_party_rights":"PENDING_REVIEW"})
                rows.append((item["asset_id"].replace("E01V2-ALT-",""),frames))
                movie.unlink(missing_ok=True)
            require(len(rows)==4,"alternatives:missing_real_frames")
            report["contact_sheet"]=contact_sheet(
                rows,out/"e01-alt-contact-sheet-NOT-PUBLISH.jpg")
            report["status"]="PHYSICAL_QA_COMPLETE_EDITORIAL_RIGHTS_PENDING"
    except (StockIntakeError,ValueError,OSError,KeyError,
            subprocess.TimeoutExpired,json.JSONDecodeError) as err:
        (out/"e01-alt-contact-sheet-NOT-PUBLISH.jpg").unlink(missing_ok=True)
        report["failure"]=str(err)[:180]
    (out/"e01-alt-physical-qa.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--ffprobe",default="ffprobe")
    p.add_argument("--ffmpeg",default="ffmpeg")
    a=p.parse_args()
    result=execute(a.root,a.out,a.ffprobe,a.ffmpeg)
    print(json.dumps({k:result.get(k) for k in ("status","failure","contact_sheet",
        "rights_clearance","publication_authorized")},ensure_ascii=False))
    return 0 if result["status"]=="PHYSICAL_QA_COMPLETE_EDITORIAL_RIGHTS_PENDING" else 2

if __name__=="__main__":
    raise SystemExit(main())
