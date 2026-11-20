"""Independent, fail-closed review of physical E01 alternative stock samples."""
from __future__ import annotations
import json
import re
from pathlib import Path
from agents.e01_stock_candidates import ROOT,StockIntakeError,require
from agents.e01_stock_alternatives import PATH as SOURCES,check as check_sources
EVIDENCE = Path("contracts/e01_v2_stock_alternatives_physical_editorial_v1.json")
EXPECTED_SOURCE_RUN=44264731877
EXPECTED_SOURCE_ARTIFACT=14409886173
CONTACT_SHA="19946e5fe18529d8222f76a7bf0867128308a94e7f42e4412f18e57f6263b955"
PINS={
"E01V2-ALT-S03-B":("315821882a9ed9d0dcaa74b2b111043ea6cbb27681d292a2ace7da38db15d3a7","REJECTED_EDITORIAL"),
"E01V2-ALT-S08-B":("9a07d5142c6cdf460185433e34abf8785cbe3ff98737c88165eedd64de5a10fd","CONDITIONAL_CONTEXT_ONLY"),
"E01V2-ALT-S09-B":("a05fda2c40d250fd4d93bd65126cccfb370983d967f4f3d5b84acbdb8056ec90","REJECTED_EDITORIAL"),
"E01V2-ALT-S09-C":("9c4a5d939a05af05f4d742c5054ee55f520f58ef1de9e73d57b3d87f54b7199f","REJECTED_EDITORIAL"),
}
PINS_METRICS={
"E01V2-ALT-S03-B":(54688332,2160,3840,26.026),
"E01V2-ALT-S08-B":(13979506,2160,3840,14.12),
"E01V2-ALT-S09-B":(38961178,2160,3840,17.086667),
"E01V2-ALT-S09-C":(4813325,1080,1920,19.12),
}

def verify(root:Path=ROOT,proof:dict|None=None)->dict:
    check_sources(root)
    if proof is None:
        proof=json.loads((root/EVIDENCE).read_text(encoding="utf-8"))
    require(isinstance(proof,dict)
        and proof.get("schema_version")=="1.0.0"
        and proof.get("project")=="verbo-no-chao"
        and proof.get("episode_id")=="VNC-W01-E1"
        and proof.get("candidate_version")==2
        and proof.get("stage")=="FOUR_REAL_SOURCE_DECODES_AND_TWELVE_FRAME_EDITORIAL_REVIEW_NOT_MASTER"
        and proof.get("source_manifest")==str(SOURCES)
        and proof.get("source_run_id")==EXPECTED_SOURCE_RUN
        and proof.get("source_run_url")==
            "https://github.com/BORELLITO/corte-fino-engine/actions/runs/"+
            str(EXPECTED_SOURCE_RUN)
        and proof.get("source_artifact_id")==EXPECTED_SOURCE_ARTIFACT
        and proof.get("source_contact_sha256")==CONTACT_SHA
        and proof.get("source_contact_bytes")==151988
        and proof.get("source_samples")==12,
        "alternate_review:unverified_source")
    for field in ("reviewed_full_video_playback","visual_editorial_authorized_for_master",
        "third_party_rights_cleared","narration_license_cleared",
        "music_license_cleared","master_rendered","publication_authorized"):
        require(proof.get(field) is False,"alternate_review:fake_release")
    source=json.loads((root/SOURCES).read_text(encoding="utf-8"))
    indexed={i["asset_id"]:i for i in source["candidates"]}
    entries=proof.get("review_decisions")
    require(isinstance(entries,list) and len(entries)==4,
            "alternate_review:missing_assets")
    seen=set()
    for item in entries:
        require(isinstance(item,dict),"alternate_review:bad_record")
        ident=item.get("asset_id")
        require(ident in PINS and ident not in seen and
                item.get("scene_id")==indexed[ident]["scene_id"] and
                item.get("video_id")==indexed[ident]["video_id"] and
                item.get("sha256")==PINS[ident][0] and
                item.get("decision")==PINS[ident][1],
                "alternate_review:unapproved_or_changed_asset")
        expected_size,w,h,duration=PINS_METRICS[ident]
        require(item.get("bytes")==expected_size and item.get("width")==w
                and item.get("height")==h and item.get("codec")=="h264"
                and item.get("duration_seconds")==duration and
                item.get("full_stream_decoded") is True and
                item.get("visual_samples_at_percent")==[15,50,85],
                "alternate_review:changed_media_observation")
        require(item.get("rights_cleared") is False
                and item.get("allowed_for_master") is False
                and item.get("full_visual_review_complete") is False
                and isinstance(item.get("reason"),str)
                and len(item["reason"])>=50,
                "alternate_review:false_license_or_absent_rationale")
        seen.add(ident)
    require(seen==set(PINS),"alternate_review:incomplete")
    return {"status":"EDITORIAL_ALTERNATIVES_REVIEWED_NO_MASTER_RELEASE",
            "source_assets_verified":4,
            "editorially_rejected":3,
            "conditionally_retained":1,
            "approved_for_master":0,
            "publication_authorized":False}
