"""Integrity-only attestation of physical Pexels byte probes; NOT a rights release."""
from __future__ import annotations
import json
import re
from pathlib import Path
from agents.e01_stock_candidates import ROOT, CONTRACT, StockIntakeError, validate, require

EVIDENCE = Path("contracts/e01_v2_stock_physical_probe_evidence_v1.json")
EXPECTED_RUN = 44219643779
EXPECTED_COMMIT = "9b8d2a481995a9fb084195a068a0f8db6dca6889"
EXPECTED_HASHES = {
    "E01V2-STOCK-S03-A": "7cc0d7691ff862ff416fddf446c89b6d2b457bb6bc8b812dcf53a07ef5fb326f",
    "E01V2-STOCK-S05-A": "788b087763625e67e9abe6102eced6d541a6c850be1d03bc213ebc0f6e919f43",
    "E01V2-STOCK-S08-A": "70b69f800d6bb1ec8386afee61e8ae07e5e2d4f0ce97d4851b19ce37dc7d2cba",
    "E01V2-STOCK-S09-A": "40c6d291f47e607d3d9fbf6d9952803a9e6e630040a88515b729a2dd2657bd78",
}

def verify(root: Path = ROOT, proof: dict | None = None) -> dict:
    validate(root)
    catalog = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if proof is None:
        proof = json.loads((root / EVIDENCE).read_text(encoding="utf-8"))
    require(isinstance(proof, dict)
            and proof.get("schema_version") == "1.0.0"
            and proof.get("project") == "verbo-no-chao"
            and proof.get("episode_id") == "VNC-W01-E1"
            and proof.get("candidate_version") == 2
            and proof.get("source_contract") == str(CONTRACT),
            "probe_evidence:wrong_source")
    require(proof.get("github_run_id") == EXPECTED_RUN
            and proof.get("git_head_sha") == EXPECTED_COMMIT
            and proof.get("github_run_url")
                == "https://github.com/BORELLITO/corte-fino-engine/actions/runs/"
                   + str(EXPECTED_RUN)
            and proof.get("artifact_id") == 14389892333
            and proof.get("status")
                == "PHYSICAL_PROBE_COMPLETE_EDITORIAL_RIGHTS_PENDING",
            "probe_evidence:run_or_state_mismatch")
    require(proof.get("files_persisted_for_master") is False
            and proof.get("frame_by_frame_visual_qa_completed") is False
            and proof.get("third_party_rights_cleared") is False
            and proof.get("final_master_rendered") is False
            and proof.get("publication_authorized") is False,
            "probe_evidence:false_release")
    items = proof.get("observations")
    original = {i["id"]: i for i in catalog["candidates"]}
    require(isinstance(items, list) and len(items) == len(original),
            "probe_evidence:incomplete_assets")
    seen = set()
    hashes = set()
    for o in items:
        require(isinstance(o, dict), "probe_evidence:invalid_observation")
        ident = o.get("id")
        require(ident in original and ident not in seen,
                "probe_evidence:missing_duplicate_or_unknown_asset")
        src = original[ident]
        seen.add(ident)
        require(o.get("video_id") == src["video_id"]
                and o.get("scene_id") == src["scene_id"],
                "probe_evidence:changed_source")
        sha = o.get("sha256")
        require(isinstance(sha, str)
                and re.fullmatch(r"[0-9a-f]{64}", sha)
                and sha not in hashes and sha == EXPECTED_HASHES[ident],
                "probe_evidence:invalid_or_repeated_sha")
        hashes.add(sha)
        require(isinstance(o.get("size_bytes"), int)
                and 100000 <= o["size_bytes"] <= 140*1024*1024,
                "probe_evidence:implausible_size")
        require(o.get("width") == src["width"]
                and o.get("height") == src["height"]
                and o.get("codec") == "h264"
                and isinstance(o.get("duration_seconds"), (float,int))
                and o["duration_seconds"] >= src["page_duration_seconds"]-1.5
                and o.get("physical_full_video_decode") is True,
                "probe_evidence:physical_metrics_changed")
    return {"status": "BYTE_HASH_ATTESTATION_FORMAT_VALID_NOT_RIGHTS_CLEARED",
            "assets": len(seen), "run": EXPECTED_RUN,
            "file_materialization_available_now": False,
            "rights_cleared": False, "publication_authorized": False}
