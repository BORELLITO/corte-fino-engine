"""Pre-download source precision gate for VNC E01.

IMPORTANT: this gate proves only that research is relevant *enough to inspect*.
Metadata and file hashes NEVER prove scene truth or grant editorial admission.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from agents.e01_stock_candidates import ROOT, require

POLICY = Path("contracts/e01_source_precision_policy_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
WORLD = Path("contracts/e01_v2_visual_single_world_acquisition_v1.json")
CATALOG1 = Path("contracts/e01_v2_stock_candidates_v1.json")
CATALOG2 = Path("contracts/e01_v2_stock_alternatives_v1.json")
DIRECTOR = Path("contracts/e01_director_editorial_decisions_v1.json")
SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
EXCLUDED_PEXELS = frozenset((
 4828603,5904567,6010698,6381001,6860448,7350189,
 8860242,13017069,32421244,34479513,37340388,40417800,
))
# All source SHA values previously rejected by actual visual-frame reviews.
# Includes historic Pexels tests and the too-short LTX proof.
EXCLUDED_SHA = frozenset((
 "7cc0d7691ff862ff416fddf446c89b6d2b457bb6bc8b812dcf53a07ef5fb326f",
 "788b087763625e67e9abe6102eced6d541a6c850be1d03bc213ebc0f6e919f43",
 "70b69f800d6bb1ec8386afee61e8ae07e5e2d4f0ce97d4851b19ce37dc7d2cba",
 "40c6d291f47e607d3d9fbf6d9952803a9e6e630040a88515b729a2dd2657bd78",
 "315821882a9ed9d0dcaa74b2b111043ea6cbb27681d292a2ace7da38db15d3a7",
 "9a07d5142c6cdf460185433e34abf8785cbe3ff98737c88165eedd64de5a10fd",
 "a05fda2c40d250fd4d93bd65126cccfb370983d967f4f3d5b84acbdb8056ec90",
 "9c4a5d939a05af05f4d742c5054ee55f520f58ef1de9e73d57b3d87f54b7199f",
 "60073bc4a45f816ca4a4e6cce3b7039299ca6ff8824f222aa98ef923dde267e5",
 "d682edd7c783ac0c527e05548b83e654437cdfbff0d7b641478e1bf3bd895738",
 "d497186c118041aecb457938e6337f20744b20a7042f24aecbe50e7aee103a34",
 "575423922f4c026cb06e5213d5a4ff4facafbdfe131b795d3ef8ea90680366e1",
 "46b4219d2f563cb48ffb18c24c1987f9512ac80862fbd0b778ba2cfd6385b926",
))
EXPECTED_SCENE_IDS=tuple("VNC-E01V2-S%02d"%i for i in range(1,13))
GROUPS={
 "ROOM_A":"AI_FIRST_FRAME_SINGLE_WORLD",
 "SOCIAL_CONTEXT_B":"LICENSED_STOCK_EDITORIAL",
 "BIBLICAL_SYMBOL_C":"LICENSED_STOCK_EDITORIAL",
 "COMMUNITY_D":"LICENSED_STOCK_EDITORIAL"
}
REQUIRED_FLAGS=(
 "previously_rejected_source_ids_are_never_auto_reconsidered",
 "unknown_published_stock_is_not_automatically_approved",
 "source_page_metadata_only_allows_research_not_edit",
 "director_visually_approves_clips_not_user",
 "exact_scene_specific_query_required",
 "thumbnail_does_not_count_as_video_evidence",
 "room_a_independent_stock_forbidden",
 "contextual_people_endorsement_not_assumed",
 "unverifiable_rights_block_publishing",
 "source_permissions_proof_required_before_release"
)

def read_json(root:Path, path:Path)->dict:
 return json.loads((root/path).read_text(encoding="utf-8"))

def verify(root:Path=ROOT, data:dict|None=None)->dict:
 if data is None: data=read_json(root,POLICY)
 storyboard=read_json(root,STORY)
 world=read_json(root,WORLD)
 source_a=read_json(root,CATALOG1)
 source_b=read_json(root,CATALOG2)
 director=read_json(root,DIRECTOR)
 require(isinstance(data,dict) and data.get("schema_version")=="1.0.0"
     and data.get("project")=="verbo-no-chao"
     and data.get("episode_id")==storyboard.get("episode_id")=="VNC-W01-E1"
     and data.get("source_storyboard")==str(STORY)
     and data.get("source_world_blueprint")==str(WORLD)
     and data.get("source_director_verdict")==str(DIRECTOR)
     and data.get("script_sha256")==storyboard.get("script_sha256")==SCRIPT
     and data.get("audio_sha256")==storyboard.get("audio_sha256")==AUDIO
     and data.get("state")=="PRECISION_PREFLIGHT_ONLY_NOT_ASSET_APPROVAL",
     "source_precision:wrong_episode_or_contract")
 require(all(data.get(k) is True for k in REQUIRED_FLAGS)
     and data.get("auto_web_source_acquisition") is False
     and data.get("selected_candidate_count")==0
     and data.get("selected_candidates")==[]
     and data.get("publication_authorized") is False
     and data.get("master_rendered") is False,
     "source_precision:unexpected_source_or_rights_promotion")
 historical={
  c["video_id"] for c in source_a["candidates"]
 } | {
  c["video_id"] for c in source_b["candidates"]
 } | {8860242,4828603,37340388,6381001}
 require(historical==EXCLUDED_PEXELS
    and data.get("excluded_pexels_video_ids")==sorted(EXCLUDED_PEXELS)
    and data.get("excluded_known_video_sha256")==sorted(EXCLUDED_SHA)
    and len(EXCLUDED_SHA)==13 and all(
      re.fullmatch(r"[0-9a-f]{64}",s) for s in EXCLUDED_SHA),
    "source_precision:rejected_source_registry_changed")
 require(len(director.get("decisions",[]))==7 and all(
   r.get("verdict")=="REJECTED_FOR_E01_CANONICAL_SHOT"
   and r.get("can_enter_e01_edit") is False
   and r.get("source_sha256") in EXCLUDED_SHA
   for r in director["decisions"]), "source_precision:director_history_missing")
 scenes=data.get("scenes")
 require(isinstance(scenes,list) and len(scenes)==12
     and len(storyboard.get("scenes",[]))==12
     and len(world.get("scenes",[]))==12,
     "source_precision:incomplete_twelve_scene_plan")
 for i,(candidate,canonical,world_scene) in enumerate(zip(
      scenes,storyboard["scenes"],world["scenes"])):
  ident=EXPECTED_SCENE_IDS[i]
  group=world_scene["continuity_group"]
  require(isinstance(candidate,dict)
      and ident==candidate.get("scene_id")==canonical.get("id")==world_scene.get("shot_id")
      and group==candidate.get("continuity_group") and group in GROUPS
      and candidate.get("allowed_acquisition_lane")==GROUPS[group]
      and candidate.get("duration_seconds")==round(
            canonical["end_seconds"]-canonical["start_seconds"],3)
      and candidate.get("narrative_action_pt")==world_scene.get("visual_action_pt")
      and candidate.get("locked_search_queries_en")==world_scene.get("verified_real_footage_search_en")
      and candidate.get("hard_reject_conditions_pt")==world_scene.get("hard_reject_if")
      and candidate.get("current_research_decision")==
         "NO_NEW_CANDIDATE_EDITORIALLY_APPROVED"
      and candidate.get("new_actor_independent_footage_forbidden") is (group=="ROOM_A")
      and candidate.get("requires_approved_s01_actor_anchor") is (group=="ROOM_A" and i!=0)
      and candidate.get("source_video_id") is None
      and candidate.get("source_sha256") is None
      and candidate.get("editorial_approved") is False
      and candidate.get("rights_cleared") is False
      and candidate.get("can_enter_master") is False,
      "source_precision:scene_query_drift_or_false_approval")
  terms=candidate["locked_search_queries_en"]
  reject=candidate["hard_reject_conditions_pt"]
  require(len(terms)==2 and len(reject)==2 and
     all(isinstance(t,str) and len(t.split())>=5 for t in terms) and
     all(isinstance(t,str) and len(t)>=12 for t in reject),
     "source_precision:weak_or_missing_scene_search_terms")
 return {
    "status":"TWELVE_SOURCE_SCOUT_BRIEFS_LOCKED_REJECTIONS_INDEXED",
    "scene_briefs":12,
    "previously_rejected_pexels_ids_blocked":len(EXCLUDED_PEXELS),
    "previously_rejected_media_hashes_blocked":len(EXCLUDED_SHA),
    "new_sources_downloaded":0,"new_clips_approved":0,
    "publication_authorized":False
 }

def rejected_sha(sha:str)->bool:
 return isinstance(sha,str) and sha.lower() in EXCLUDED_SHA

def preflight_stock(scene_id:str,video_id:int,page_url:str,query:str,
                    root:Path=ROOT)->dict:
 """Select a new public stock page for inspection, NEVER for scene admission.

 New IDs passing here have NOT been proven to exist, licensed or narratively right.
 """
 verify(root)
 data=read_json(root,POLICY)
 plans={x["scene_id"]:x for x in data["scenes"]}
 require(scene_id in plans,"source_precision:unknown_scene")
 scene=plans[scene_id]
 require(scene["continuity_group"]!="ROOM_A",
         "source_precision:recurring_actor_must_use_approved_actor_reference")
 require(type(video_id) is int and video_id>0 and video_id not in EXCLUDED_PEXELS,
         "source_precision:rejected_reused_or_invalid_video_id")
 require(isinstance(query,str)
         and query in scene["locked_search_queries_en"],
         "source_precision:generic_or_cross_scene_query")
 require(isinstance(page_url,str),"source_precision:missing_page_url")
 p=urlsplit(page_url)
 require(p.scheme=="https" and p.hostname=="www.pexels.com"
      and p.port is None and p.username is None and p.password is None
      and not p.query and not p.fragment
      and re.fullmatch(r"/video/[a-z0-9-]+-"+str(video_id)+r"/",p.path),
      "source_precision:untrusted_or_wrong_source_page")
 return {
   "status":"ELIGIBLE_FOR_PHYSICAL_MEDIA_REVIEW_ONLY",
   "scene_id":scene_id,"video_id":video_id,
   "storyboard_action_pt":scene["narrative_action_pt"],
   "reject_if":scene["hard_reject_conditions_pt"],
   "query":query,
   "source_page_verified_live":False,
   "actual_video_frames_reviewed":False,
   "story_or_actor_match_verified":False,
   "right_to_use_verified":False,
   "editorially_approved":False,
   "can_enter_master":False,
   "publication_authorized":False
 }

def main()->int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--scene-id")
 p.add_argument("--video-id",type=int)
 p.add_argument("--page-url")
 p.add_argument("--query")
 a=p.parse_args()
 try:
  if any(x is not None for x in (a.scene_id,a.video_id,a.page_url,a.query)):
   require(all(x is not None for x in (a.scene_id,a.video_id,a.page_url,a.query)),
           "source_precision:incomplete_proposal")
   result=preflight_stock(a.scene_id,a.video_id,a.page_url,a.query)
  else:
   result=verify()
  print(json.dumps(result,ensure_ascii=False))
  return 0
 except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
  print(json.dumps({"status":"BLOCKED_WRONG_OR_REPEAT_SOURCE",
                    "reason":str(exc)[:180],
                    "publication_authorized":False},ensure_ascii=False))
  return 2

if __name__=="__main__":
 raise SystemExit(main())
