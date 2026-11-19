"""E01 S01: keep newly inspected free-stock sources out of approved masters."""
from __future__ import annotations
import json
from pathlib import Path
from agents.e01_stock_candidates import ROOT

CONTRACT = Path("contracts/e01_s01_stock_nov19_editorial_v1.json")
SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
AUDIO = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
EXPECTED = {
    16835716: ("REJECTED_FOR_S01", "5052434451984e22fc4c098f73d9a1eb902a9830cf35403aa39918e56f45d2e4"),
    32788087: ("STYLE_REFERENCE_ONLY_NOT_S01", "1d2b0773699ad984730d7c1d4ff0930cebea136bfd6aefc062da8f664117c767"),
    6944291: ("REJECTED_FOR_S01", "206a172759ff982dd80b75ac43da2c0e25d2f3c9c89e8707e29479073f75718a"),
}


def verify(root=ROOT):
    root = Path(root)
    contract = json.loads((root / CONTRACT).read_text(encoding="utf8"))
    story = json.loads((root / "contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf8"))
    if (contract.get("schema_version") != "1.0.0" or
        contract.get("project") != "VERBO_NO_CHAO_EXCLUSIVO" or
        contract.get("episode_id") != "VNC-W01-E1" or
        contract.get("scene_id") != "VNC-E01V2-S01" or
        contract.get("script_sha256") != SCRIPT or
        contract.get("audio_sha256") != AUDIO or
        contract.get("source_storyboard") != "contracts/e01_v2_12_scene_visual_plan_v1.json" or
        story.get("script_sha256") != SCRIPT or
        story.get("audio_sha256") != AUDIO or
        story.get("publication_authorized") is not False or
        story["scenes"][0].get("asset_sha256") is not None or
        contract.get("full_video_playback_reviewed") is not False or
        contract.get("stills_reviewed") != 18 or
        contract.get("footage_approved_for_s01") != 0 or
        contract.get("source_rights_cleared") is not False or
        contract.get("identifiable_people_negative_portrayal_cleared") is not False or
        contract.get("publication_authorized") is not False or
        contract.get("mastered_1080x1920") is not False):
        raise ValueError("source_or_release_gate_modified")
    decisions = contract.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 3:
        raise ValueError("unexpected_decision_count")
    seen = set()
    for row in decisions:
        ident = row.get("video_id")
        if ident in seen or ident not in EXPECTED:
            raise ValueError("unapproved_source_present")
        seen.add(ident)
        if (row.get("editorial_decision") != EXPECTED[ident][0] or
            row.get("source_mp4_sha256") != EXPECTED[ident][1] or
            row.get("physical_full_decode_verified") is not True or
            row.get("scene_approved") is not False or
            row.get("rights_cleared") is not False or
            row.get("can_publish") is not False or
            not isinstance(row.get("qa_contact_sheet_sha256"), str) or
            len(row["qa_contact_sheet_sha256"]) != 64):
            raise ValueError("forged_qa_or_publication_status")
    if seen != set(EXPECTED):
        raise ValueError("missing_source_result")
    return {
        "status": "THREE_REAL_VIDEOS_AUDITED_ZERO_S01_APPROVED",
        "verified_original_source_files": 3,
        "visual_sample_frames_reviewed": 18,
        "style_reference_only_video_id": 32788087,
        "scene_media_ready": False,
        "master_allowed": False,
        "publication_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
