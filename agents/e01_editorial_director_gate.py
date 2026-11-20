"""Final E01 creative-director decisions; technical MP4s are never scene admission."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from agents.e01_stock_candidates import ROOT, require

FILE = Path("contracts/e01_director_editorial_decisions_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
LEGACY = Path("contracts/e01_v2_supporting_camera_editorial_qa_v1.json")
SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
PINNED = {
  "E01-S01-PEXELS-8860242":("VNC-E01V2-S01","60073bc4a45f816ca4a4e6cce3b7039299ca6ff8824f222aa98ef923dde267e5","REAL_CAMERA_STOCK"),
  "E01-S01-LTX-2S":("VNC-E01V2-S01","d682edd7c783ac0c527e05548b83e654437cdfbff0d7b641478e1bf3bd895738","AI_GENERATED_FICTIONAL_VIDEO"),
  "E01-S05-PEXELS-37340388":("VNC-E01V2-S05","d497186c118041aecb457938e6337f20744b20a7042f24aecbe50e7aee103a34","REAL_CAMERA_STOCK"),
  "E01-S10-PEXELS-4828603":("VNC-E01V2-S10","575423922f4c026cb06e5213d5a4ff4facafbdfe131b795d3ef8ea90680366e1","REAL_CAMERA_STOCK"),
  "E01-S05-PEXELS-6010698":("VNC-E01V2-S05","788b087763625e67e9abe6102eced6d541a6c850be1d03bc213ebc0f6e919f43","REAL_CAMERA_STOCK"),
  "E01-S08-PEXELS-6860448":("VNC-E01V2-S08","9a07d5142c6cdf460185433e34abf8785cbe3ff98737c88165eedd64de5a10fd","REAL_CAMERA_STOCK"),
  "E01-S10-PEXELS-6381001":("VNC-E01V2-S10","46b4219d2f563cb48ffb18c24c1987f9512ac80862fbd0b778ba2cfd6385b926","REAL_CAMERA_STOCK"),
}
RELEASE_FLAGS = (
 "ready_for_full_12_scene_master","soundtrack_license_cleared",
 "voice_runtime_license_cleared","source_license_use_specific_review_complete",
 "end_to_end_editorial_approval","commercial_publication_authorized",
 "publishing_action_authorized","production_cost_authorized"
)
REQUIRED_POLICY = (
 "editor_approves_without_user_per_clip",
 "metadata_or_frame_hash_alone_never_proves_narrative",
 "conditional_or_technically_passed_is_not_approval",
 "source_sha256_is_required",
 "anonymization_and_false_endorsement_restrictions_apply",
 "story_and_continuity_hard_reject_overrides_average_score",
 "source_license_is_distinct_from_contextual_clearance",
 "original_narrative_commentary_and_unique_edit_required",
 "change_to_approved_storyboard_requires_separate_explicit_review",
 "user_approval_still_required_for_publication_and_costs",
 "release_requires_scene_approvals_for_all_12"
)

def validate(root:Path=ROOT, data:dict|None=None)->dict:
 if data is None:
  data=json.loads((root/FILE).read_text(encoding="utf-8"))
 require(isinstance(data,dict) and data.get("schema_version")=="1.0.0"
    and data.get("project")=="verbo-no-chao"
    and data.get("episode_id")=="VNC-W01-E1"
    and data.get("decision_authority")=="AI_ASSISTANT_EDITORIAL_DIRECTOR_DELEGATED_BY_USER"
    and data.get("scope")=="E01_V2_STORYBOARD_SHOT_ADMISSION_ONLY"
    and data.get("source_storyboard")==str(STORY)
    and data.get("script_sha256")==SCRIPT
    and data.get("narration_sha256")==AUDIO
    and data.get("predecessor_evidence_contract")==str(LEGACY)
    and data.get("status")=="SEVEN_SOURCES_REJECTED_FOR_CANONICAL_E01_ALL_RELEASE_BLOCKED",
    "director:wrong_episode_or_authority")
 require(all(data.get(k) is False for k in RELEASE_FLAGS)
    and data.get("approved_for_e01_shots")==[],
    "director:release_claim_without_proof")
 require(all(data.get(k)==4 for k in (
      "min_scene_relevance_0_5","min_world_continuity_0_5","min_visual_quality_0_5")),
      "director:approval_thresholds_changed")
 policy=data.get("policy")
 require(isinstance(policy,dict) and set(policy)==set(REQUIRED_POLICY)
      and all(policy[k] is True for k in REQUIRED_POLICY),
      "director:policy_weakened")
 source=json.loads((root/STORY).read_text(encoding="utf-8"))
 require(source["script_sha256"]==SCRIPT and source["audio_sha256"]==AUDIO
      and len(source["scenes"])==12,
      "director:original_narrative_changed")
 prior_first=json.loads((root/"contracts/e01_v2_stock_editorial_review_v1.json").read_text(encoding="utf-8"))
 prior_second=json.loads((root/"contracts/e01_v2_stock_alternatives_physical_editorial_v1.json").read_text(encoding="utf-8"))
 require(data.get("predecessor_first_stock_review")=="contracts/e01_v2_stock_editorial_review_v1.json"
     and data.get("predecessor_second_stock_review")=="contracts/e01_v2_stock_alternatives_physical_editorial_v1.json",
     "director:historical_predecessor_missing")
 orig_five={r.get("asset_id"):r for r in prior_first.get("decisions",[])}
 orig_eight={r.get("asset_id"):r for r in prior_second.get("review_decisions",[])}
 require(orig_five.get("E01V2-STOCK-S05-A",{}).get("decision")=="CONDITIONAL_METAPHOR"
     and orig_eight.get("E01V2-ALT-S08-B",{}).get("decision")=="CONDITIONAL_CONTEXT_ONLY"
     and orig_eight["E01V2-ALT-S08-B"].get("sha256")==PINNED["E01-S08-PEXELS-6860448"][1],
     "director:prior_conditional_exceptions_not_grounded")
 old=json.loads((root/LEGACY).read_text(encoding="utf-8"))
 require(old.get("s10_candidate",{}).get("video_id")==6381001
      and old["s10_candidate"]["condition"]=="CONDITIONAL_SYMBOLIC_SUPPORT_ONLY"
      and old["s10_candidate"]["accepted_for_locked_storyboard"] is False,
      "director:intermediate_review_mutated")
 reviews=data.get("decisions")
 require(isinstance(reviews,list) and len(reviews)==len(PINNED),
      "director:missing_or_extra_verdicts")
 observed={}
 allowed_scenes={s["id"] for s in source["scenes"]}
 for item in reviews:
  require(isinstance(item,dict),"director:verdict_must_be_object")
  uid=item.get("asset_id")
  require(uid in PINNED and uid not in observed, "director:duplicate_or_unknown_asset")
  sc,hash_,origin=PINNED[uid]
  require(item.get("scene_id")==sc and sc in allowed_scenes
      and item.get("source_sha256")==hash_
      and item.get("source_type")==origin
      and item.get("physical_source_verified") is True
      and item.get("reviewed_frame_samples") is True
      and item.get("exact_video_reviewed_end_to_end") is False
      and item.get("verdict")=="REJECTED_FOR_E01_CANONICAL_SHOT"
      and item.get("can_enter_e01_edit") is False
      and item.get("separate_stock_licensing_and_contextual_rights_cleared") is False
      and item.get("approved_for_master") is False,
      "director:source_identity_or_false_approval")
  require(item.get("prior_conditional_superseded") is
      (uid in {"E01-S10-PEXELS-6381001","E01-S05-PEXELS-6010698","E01-S08-PEXELS-6860448"}),
      "director:conditional_supersession_missing")
  scores=item.get("editorial_scores_0_5")
  require(isinstance(scores,dict)
      and set(scores)=={"story","continuity","visual","authenticity"}
      and all(isinstance(v,int) and not isinstance(v,bool) and 0<=v<=5
              for v in scores.values())
      and (scores["story"]<4 or scores["continuity"]<4 or scores["visual"]<4)
      and isinstance(item.get("rationale"),str)
      and len(item["rationale"])>=65,
      "director:unexplained_or_unsafe_scene_rejection")
  url=item.get("evidence_run_url")
  require(isinstance(url,str) and
      re.fullmatch(r"https://github\.com/BORELLITO/corte-fino-engine/actions/runs/\d+",url),
      "director:untrusted_evidence_url")
  observed[uid]=item["verdict"]
 require(set(observed)==set(PINNED), "director:incomplete_review_history")
 return {
  "status":"EDITORIAL_DIRECTOR_DECISIONS_LOCKED_NO_E01_SHOTS_ADMITTED",
  "reviewed_sources":len(observed),
  "rejected_for_canonical_e01":len(observed),
  "e01_clips_approved_for_cut":0,
  "e01_clips_approved_for_master":0,
  "reused_candidate_override_allowed":False,
  "publication_authorized":False
 }

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--root",type=Path,default=ROOT)
 args=parser.parse_args()
 try:
  print(json.dumps(validate(args.root),ensure_ascii=False))
  return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError) as exc:
  print(json.dumps({"status":"BLOCKED_EDITORIAL_DIRECTOR_GATE",
                    "cause":type(exc).__name__,
                    "publication_authorized":False},ensure_ascii=False))
  return 2

if __name__=="__main__":
 raise SystemExit(main())
