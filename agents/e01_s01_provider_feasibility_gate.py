"""Fail-closed verification of E01 S01 external-provider outcomes.

This is NOT a content generation workflow. It prevents a failed quota, a
pricing estimate, or a 2s proof from being silently promoted to a 5.74s scene.
"""
import json
from pathlib import Path
from agents.e01_stock_candidates import ROOT

EVIDENCE = Path("contracts/e01_s01_provider_feasibility_20261119.json")
EXPECTED_SCENE = "VNC-E01V2-S01"
KNOWN = {
    ("Agnes Video 2.5 Flash", "agnes-video-2.5-flash"),
    ("Lightricks official ZeroGPU LTX Video Fast", "LTX-Video-0.9.8-13B-distilled"),
    ("Higgsfield", "seedance_2_0_mini"),
    ("Higgsfield", "grok_video_v15_lite"),
}


def assess(root=ROOT):
    e = json.loads((Path(root) / EVIDENCE).read_text(encoding="utf-8"))
    if (e.get("schema_version") != "1.0.0"
        or e.get("project") != "VERBO_NO_CHAO_EXCLUSIVO"
        or e.get("scene_id") != EXPECTED_SCENE
        or e.get("objective", {}).get("min_scene_seconds") != 5.74
        or e.get("objective", {}).get("monetary_spend_ceiling_usd") != 0
        or e.get("publication_authorized") is not False
        or e.get("media_approved") is not False
        or e.get("master_approved") is not False
        or e.get("actual_full_scene_mp4_verified") is not False
        or e.get("authorized_production_state") != "BLOCKED_NO_ELIGIBLE_VERIFIED_FULL_SCENE"):
        raise ValueError("provider_evidence_or_release_gate_tampered")
    vendors = e.get("providers")
    if not isinstance(vendors, list) or len(vendors) != 6:
        raise ValueError("unexpected_provider_set")
    discovered = {(row.get("name"), row.get("model")) for row in vendors}
    if not KNOWN.issubset(discovered):
        raise ValueError("missing_required_provider_evidence")
    for item in vendors:
        if item.get("automatic_retry_allowed") is not False:
            raise ValueError("unexpected_automatic_retry")
        if item.get("editorial_master_approved") is True:
            raise ValueError("unearned_editorial_master_approval")
    h = [row for row in vendors if row.get("name") == "Higgsfield"]
    if len(h) != 2:
        raise ValueError("unknown_higgsfield_quote_set")
    for row in h:
        if (row.get("actual_account_plan") != "free"
            or row.get("quoted_cost_credits") != 6
            or row.get("credits_deducted") != 0
            or row.get("balance_credits_after") != 10
            or row.get("video_returned") is not False
            or "REQUIRES_BASIC_PLAN" not in row.get("result", "")):
            raise ValueError("higgsfield_plan_not_eligible")
    return {
        "scene": EXPECTED_SCENE,
        "state": "BLOCKED_NO_ELIGIBLE_VERIFIED_FULL_SCENE",
        "physically_approved_full_scene_video": False,
        "generation_or_publication_authorized": False,
        "providers_evaluated": len(vendors),
        "no_paid_upgrade_or_auto_retry": True,
    }


if __name__ == "__main__":
    print(json.dumps(assess(), ensure_ascii=False, indent=2))
