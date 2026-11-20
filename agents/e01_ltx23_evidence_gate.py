"""E01 LTX-2.3 evidence validator; physical bytes do NOT clear final export."""
from __future__ import annotations
import json
from pathlib import Path
from agents.e01_stock_candidates import ROOT,require
from agents.e01_visual_single_world_gate import validate as validate_world

EVIDENCE = Path("contracts/e01_v2_ltx23_physical_motion_evidence_v1.json")
STORY = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
SOURCE_SHA = "d682edd7c783ac0c527e05548b83e654437cdfbff0d7b641478e1bf3bd895738"
AUDIO_SHA = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
SCRIPT_SHA = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"

def validate(root=ROOT, evidence=None):
    validate_world(root)
    if evidence is None:
        evidence=json.loads((root/EVIDENCE).read_text(encoding="utf-8"))
    orig=json.loads((root/STORY).read_text(encoding="utf-8"))
    s=orig["scenes"][0]
    require(isinstance(evidence,dict)
      and evidence.get("schema_version")=="1.0.0"
      and evidence.get("project")=="verbo-no-chao"
      and evidence.get("episode_id")==orig["episode_id"]=="VNC-W01-E1"
      and evidence.get("scene_id")==s["id"]=="VNC-E01V2-S01"
      and evidence.get("source_storyboard")==str(STORY)
      and evidence.get("source_continuity_blueprint")==
        "contracts/e01_v2_visual_single_world_acquisition_v1.json"
      and evidence.get("source_run_id")==44283353433
      and evidence.get("source_artifact_id")==14417218508
      and evidence.get("source_model")=="Lightricks/LTX-2.3"
      and evidence.get("generation_type")=="AI_GENERATED_VIDEO"
      and evidence.get("source_access")=="ANONYMOUS_HF_ZEROGPU"
      and evidence.get("source_cost_paid")==0
      and evidence.get("provider_execution_result")==
        "PHYSICAL_AI_MOTION_CLIP_VERIFIED_NO_MASTER",
      "e01_ltx23:provider_or_episode_provenance_changed")
    m=evidence.get("media")
    require(isinstance(m,dict)
      and m.get("sha256")==SOURCE_SHA
      and m.get("bytes")==204030
      and m.get("width")==576 and m.get("height")==1024
      and m.get("frames")==49 and m.get("fps_num")==24 and m.get("fps_den")==1
      and m.get("codec")=="h264"
      and m.get("duration_seconds")==2.041667
      and m.get("full_video_decoded") is True
      and m.get("actual_video_not_slideshow") is True
      and m.get("native_master_1080x1920") is False
      and m.get("source_preview_in_private_drive_verified") is True,
      "e01_ltx23:physical_movie_evidence_invalid")
    q=evidence.get("frame_evaluation")
    require(isinstance(q,dict)
      and q.get("reviewed_human_frames_seconds")==[0.15,0.55,1.05,1.55,1.95]
      and q.get("editorial_decision")==
        "CONDITIONAL_LOOK_REFERENCE_ONLY_NOT_SCENE_APPROVAL"
      and "NOTEBOOK_OPEN_NOT_CLOSED" in q.get("violations",[])
      and "S01_DURATION_SHORT" in q.get("violations",[])
      and q.get("full_playback_reviewed") is False
      and q.get("physical_commercial_model_license_review_complete") is False,
      "e01_ltx23:editorial_disagreement_suppressed")
    require(evidence.get("requested_scene_start_seconds")==s["start_seconds"]==0
      and evidence.get("requested_scene_end_seconds")==s["end_seconds"]==5.74
      and evidence.get("correct_e01_audio_sha256")==orig["audio_sha256"]==AUDIO_SHA
      and evidence.get("correct_script_sha256")==orig["script_sha256"]==SCRIPT_SHA
      and evidence.get("target_fps")==30
      and all(evidence.get(k) is False for k in (
        "script_changed","audio_changed","captions_changed",
        "rights_cleared","editorially_approved",
        "visual_scene_complete","approved_for_master",
        "publication_authorized")),
      "e01_ltx23:false_release_or_canonical_drift")
    return {"status":"REAL_AI_VIDEO_BYTES_AND_HUMAN_FRAME_SAMPLES_VERIFIED_ONLY",
            "source_sha256":SOURCE_SHA,
            "preview_duration_seconds":2.041667,
            "requested_scene_seconds":5.74,
            "rights_and_master_release":False,
            "publication_authorized":False}

if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False))
