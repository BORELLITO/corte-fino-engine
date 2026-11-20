"""Keep E01 real-film editorial rejections binding until deliberate re-review."""
import json
from pathlib import Path
from agents.e01_stock_candidates import ROOT, CONTRACT, StockIntakeError, require, validate
from agents.e01_stock_probe_evidence import EXPECTED_HASHES, verify
PATH=Path("contracts/e01_v2_stock_editorial_review_v1.json")
SHA="54e3f9b9ba891565b1fae13146cda41804c68269b564551b574abcd709bb367b"
EXPECTED={
"E01V2-STOCK-S03-A":"REJECTED_HARMONY",
"E01V2-STOCK-S05-A":"CONDITIONAL_METAPHOR",
"E01V2-STOCK-S08-A":"REJECTED_HARMONY",
"E01V2-STOCK-S09-A":"REJECTED_HARMONY",
}

def review(root:Path=ROOT,data:dict|None=None)->dict:
    validate(root);verify(root)
    if data is None:
        data=json.loads((root/PATH).read_text(encoding="utf-8"))
    require(isinstance(data,dict)
            and data.get("schema_version")=="1.0.0"
            and data.get("project")=="verbo-no-chao"
            and data.get("episode_id")=="VNC-W01-E1"
            and data.get("candidate_version")==2
            and data.get("scope")=="THREE_SAMPLED_FRAMES_PER_STOCK_VIDEO_EDITORIAL_REVIEW"
            and data.get("evidence_action_run")==44222503550
            and data.get("evidence_artifact_id")==14391027472
            and data.get("evidence_action_url")=="https://github.com/BORELLITO/corte-fino-engine/actions/runs/44222503550"
            and data.get("contact_sheet_sha256")==SHA
            and data.get("frames_inspected_total")==12,
            "editorial:wrong_provenance")
    for field in ("reviewed_video_full_playback","rights_cleared",
                  "first_party_music_license_cleared","voice_runtime_license_cleared",
                  "editorial_release_authorized","master_rendered",
                  "publication_authorized"):
        require(data.get(field) is False,"editorial:invented_release_claim")
    catalog=json.loads((root/CONTRACT).read_text(encoding="utf-8"))
    source={c["id"]:c["scene_id"] for c in catalog["candidates"]}
    entries=data.get("decisions")
    require(isinstance(entries,list) and len(entries)==4,
            "editorial:incomplete_decisions")
    actual={}
    for i in entries:
        require(isinstance(i,dict),"editorial:not_object")
        ident=i.get("asset_id")
        require(ident in EXPECTED and ident not in actual
                and i.get("scene_id")==source[ident]
                and i.get("decision")==EXPECTED[ident]
                and i.get("rights_released") is False
                and i.get("allowed_for_master") is False,
                "editorial:decision_forged_or_duplicate")
        require(isinstance(i.get("rationale"),str)
                and len(i["rationale"])>=35
                and isinstance(i.get("shot_score_0_5"),int)
                and 0<=i["shot_score_0_5"]<=5,
                "editorial:missing_rationale")
        actual[ident]=i["decision"]
    require(set(actual)==set(EXPECTED),"editorial:missing_candidate")
    return {"status":"EDITORIAL_SHORTLIST_REVIEWED_NO_APPROVED_MASTER_CANDIDATES",
            "rejected":sum(v=="REJECTED_HARMONY" for v in actual.values()),
            "conditional":sum(v=="CONDITIONAL_METAPHOR" for v in actual.values()),
            "assets_approved_for_master":0,"publication_authorized":False}
