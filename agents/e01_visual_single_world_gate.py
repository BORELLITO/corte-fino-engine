"""E01 v2 one-world visual-acquisition gate; planning is never a media master."""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path
from agents.e01_stock_candidates import ROOT, StockIntakeError, require
from agents.e01_stock_editorial_decision import review as first_batch_review
from agents.e01_stock_alt_review_gate import verify as second_batch_review
from agents.e01_editorial_director_gate import validate as director_review
from agents.e01_s01_video_anchor import validate_blueprint as verify_room_references
from agents.e01_source_precision_gate import verify as verify_source_precision

CONTRACT=Path("contracts/e01_v2_visual_single_world_acquisition_v1.json")
STORY=Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
GROUPS={"ROOM_A","SOCIAL_CONTEXT_B","BIBLICAL_SYMBOL_C","COMMUNITY_D"}
ROOM_INDEX={1,2,6,7,8,9,11,12}
SINGLE_SESSION="CONTINUOUS_REAL_FOOTAGE"
OTHER_MODES={"REAL_OBSERVATIONAL_FOOTAGE","SYMBOLIC_REAL_FOOTAGE"}
EXPECTED_GROUPS={
  1:"ROOM_A",2:"ROOM_A",3:"SOCIAL_CONTEXT_B",
  4:"BIBLICAL_SYMBOL_C",5:"BIBLICAL_SYMBOL_C",6:"ROOM_A",7:"ROOM_A",
  8:"ROOM_A",9:"ROOM_A",10:"COMMUNITY_D",11:"ROOM_A",12:"ROOM_A"
}
LOCKED_SCRIPT="c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
LOCKED_AUDIO="4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"

def validate(root:Path=ROOT,document:dict|None=None)->dict:
    if document is None:
        document=json.loads((root/CONTRACT).read_text(encoding="utf-8"))
    require(isinstance(document,dict) and
      document.get("schema_version")=="1.0.0" and
      document.get("project")=="verbo-no-chao" and
      document.get("episode_id")=="VNC-W01-E1" and
      document.get("candidate_version")==2 and
      document.get("status")=="REAL_LIVE_ACTION_SINGLE_WORLD_ACQUISITION_ONLY" and
      document.get("source_storyboard")==str(STORY) and
      document.get("script_sha256")==LOCKED_SCRIPT and
      document.get("audio_sha256")==LOCKED_AUDIO and
      document.get("design_locked") is True and
      document.get("source_assets_verified_for_this_plan")==0 and
      document.get("license_all_cleared") is False and
      document.get("master_1080x1920_rendered") is False and
      document.get("publication_authorized") is False,
      "single_world:unearned_master_or_wrong_episode")
    # Earlier Pexels rejections cannot be overwritten by this new plan.
    r1=first_batch_review(root)
    r2=second_batch_review(root)
    director=director_review(root)
    room_reference=verify_room_references(root)
    source_precision=verify_source_precision(root)
    require(r1["assets_approved_for_master"]==0 and
        r2["approved_for_master"]==0 and
        director["e01_clips_approved_for_cut"]==0 and
        director["publication_authorized"] is False and
        room_reference["scene_count"]==8 and
        room_reference["publication_authorized"] is False and
        source_precision["scene_briefs"]==12 and
        source_precision["publication_authorized"] is False,
        "single_world:prior_rejections_missing")
    require(document.get("prior_rejections")==[
        "contracts/e01_v2_stock_editorial_review_v1.json",
        "contracts/e01_v2_stock_alternatives_physical_editorial_v1.json"],
        "single_world:lost_rejection_history")
    original=json.loads((root/STORY).read_text(encoding="utf-8"))
    require(original["script_sha256"]==LOCKED_SCRIPT and
        original["audio_sha256"]==LOCKED_AUDIO and
        document.get("target_canvas")==original["canvas"],
        "single_world:timeline_source_changed")
    global_style=document.get("global_continuity")
    require(isinstance(global_style,dict)
        and global_style.get("safe_zone_bottom_px")==380 and
        isinstance(global_style.get("person"),str) and
        "unrecognizable" in global_style["person"] and
        isinstance(global_style.get("room"),str)
        and all(word in global_style["room"] for word in ("window","desk","notebook"))
        and global_style.get("stock_exceptions")==[
            "SOCIAL_CONTEXT_B","BIBLICAL_SYMBOL_C","COMMUNITY_D"],
        "single_world:lost_style_lock")
    scenes=document.get("scenes")
    require(isinstance(scenes,list) and len(scenes)==12,
        "single_world:missing_or_extra_shots")
    expected_cues=[]
    for index,(s,source) in enumerate(zip(scenes,original["scenes"]),start=1):
        require(isinstance(s,dict) and
            s.get("scene_index")==index and
            s.get("shot_id")==source["id"] and
            s.get("title")==source["title"] and
            s.get("start_seconds")==source["start_seconds"] and
            s.get("end_seconds")==source["end_seconds"] and
            s.get("narration_block")==source["narration_block"] and
            s.get("caption_cues")==source["caption_cues"] and
            s.get("continuity_group")==EXPECTED_GROUPS[index],
            "single_world:changed_shot_or_timing")
        mode=SINGLE_SESSION if index in ROOM_INDEX else (
             "SYMBOLIC_REAL_FOOTAGE" if index in {4,5} else
             "REAL_OBSERVATIONAL_FOOTAGE")
        require(s.get("preferred_acquisition")==mode,
             "single_world:wrong_acquisition_world")
        for key in ("camera_instruction","visual_action_pt"):
            floor = 16 if key == "camera_instruction" else 40
            require(isinstance(s.get(key),str) and len(s[key])>=floor,
                "single_world:missing_camera_or_visual_action")
        terms=s.get("verified_real_footage_search_en")
        blocked=s.get("hard_reject_if")
        require(isinstance(terms,list) and len(terms)==2
            and all(isinstance(t,str) and len(t)>=20 for t in terms)
            and isinstance(blocked,list) and len(blocked)==2
            and all(isinstance(t,str) and len(t)>=12 for t in blocked),
            "single_world:search_and_negative_filter_missing")
        require(s.get("asset_state")=="UNSOURCED" and
            s.get("source_asset_id") is None and
            s.get("source_file_sha256") is None and
            s.get("license_status")=="PENDING" and
            s.get("actual_frame_review") is False and
            s.get("same_person_verified") is False and
            s.get("real_motion_verified") is False and
            s.get("safe_zone_verified") is False and
            s.get("allowed_in_master") is False,
            "single_world:unearned_source_or_master_claim")
        expected_cues.extend(s["caption_cues"])
    require(expected_cues==list(range(1,29)),
        "single_world:caption_cues_lost_or_repeated")
    require(scenes[0]["start_seconds"]==0 and
        scenes[-1]["end_seconds"]==70.425 and
        all(scenes[i]["end_seconds"]==scenes[i+1]["start_seconds"]
            for i in range(11)),
        "single_world:timeline_gap_or_overlap")
    return {
      "status":"SHOOTING_BLUEPRINT_READY_NOT_MEDIA",
      "scene_count":12,
      "same_world_scene_count":len(ROOM_INDEX),
      "other_context_scene_count":12-len(ROOM_INDEX),
      "caption_cues":28,
      "physically_verified_assets":0,
      "release_gates_cleared":False,
      "publication_authorized":False
    }

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=ROOT)
    args=ap.parse_args()
    try:
        print(json.dumps(validate(args.root),ensure_ascii=False))
        return 0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError) as err:
        print(json.dumps({"status":"BLOCKED_SINGLE_WORLD_PLAN",
                          "reason":type(err).__name__,
                          "publication_authorized":False},ensure_ascii=False))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
