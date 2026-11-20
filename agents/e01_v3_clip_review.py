"""Metadata review of every E01 clip candidate against the 76.67 s scene refit and the measured caption band.

No frames are viewed here: this reads the repository evidence only. Anything that needs real frames
stays PENDING_FRAME_REVIEW. Nothing is approved.
"""
import json
from pathlib import Path

REFIT = Path("contracts/e01_v3_12_scene_refit_v1.json")
BAND = Path("contracts/e01_v3_caption_band_v1.json")
CAND = Path("contracts/e01_v2_stock_candidates_v1.json")
PROBE = Path("contracts/e01_v2_stock_physical_probe_evidence_v1.json")
ALT = Path("contracts/e01_v2_stock_alternatives_physical_editorial_v1.json")
DIRECTOR = Path("contracts/e01_director_editorial_decisions_v1.json")
ACQ = Path("contracts/e01_v2_visual_single_world_acquisition_v1.json")
OUT = Path("contracts/e01_v3_clip_review_v1.json")
HANDLE_SECONDS = 1.0  # head+tail handle needed on top of the scene length


def _j(p):
    return json.loads(p.read_text(encoding="utf-8"))


def build() -> dict:
    refit, band, cand = _j(REFIT), _j(BAND), _j(CAND)
    probe = {o["id"]: o for o in _j(PROBE)["observations"]}
    alt = _j(ALT)["review_decisions"]
    director = _j(DIRECTOR)["decisions"]
    acq = {s["shot_id"]: s for s in _j(ACQ)["scenes"]}
    pb = band["protected_band_for_primary_action"]
    clips = {s["id"]: [] for s in refit["scenes"]}
    for c in cand["candidates"]:
        o = probe.get(c["id"])
        clips[c["scene_id"]].append({
            "clip": c["id"], "source": "Pexels " + str(c["video_id"]),
            "native_seconds": o["duration_seconds"] if o else float(c["page_duration_seconds"]),
            "physically_probed": bool(o), "sha256": o["sha256"] if o else None,
            "state": "PENDING_FRAME_REVIEW", "evidence": "contracts/e01_v2_stock_candidates_v1.json"})
    for d in alt:
        clips[d["scene_id"]].append({
            "clip": d["asset_id"], "source": "Pexels " + str(d["video_id"]),
            "native_seconds": d["duration_seconds"], "physically_probed": True, "sha256": d["sha256"],
            "state": d["decision"], "evidence": "contracts/e01_v2_stock_alternatives_physical_editorial_v1.json"})
    for d in director:
        clips[d["scene_id"]].append({
            "clip": d["asset_id"], "source": d["source_type"], "native_seconds": None,
            "physically_probed": True, "sha256": d["source_sha256"], "state": d["verdict"],
            "evidence": "contracts/e01_director_editorial_decisions_v1.json"})
    # a later REJECTED verdict supersedes an earlier pending/conditional one for the same video
    scenes = []
    for s in refit["scenes"]:
        need = round(s["duration_seconds"] + HANDLE_SECONDS, 2)
        rows = clips[s["id"]]
        rejected_ids = {r["sha256"] for r in rows if str(r["state"]).startswith("REJECTED") and r["sha256"]}
        live = []
        for r in rows:
            r = dict(r)
            if r["state"] in ("PENDING_FRAME_REVIEW", "CONDITIONAL_CONTEXT_ONLY"):
                if r["sha256"] in rejected_ids:
                    r["state"] = "SUPERSEDED_BY_REJECTION"
                else:
                    r["covers_scene_with_handles"] = (r["native_seconds"] or 0) >= need
                    live.append(r)
        acqs = acq[s["id"]]
        scenes.append({
            "scene": s["id"], "title": s["title"], "scene_seconds": s["duration_seconds"],
            "min_source_seconds_with_handles": need,
            "needs_second_shot": s["needs_internal_shot_change"],
            "world": acqs["continuity_group"],
            "viable_candidates": live,
            "rejected_or_superseded": sum(1 for r in rows if r["state"] not in ("PENDING_FRAME_REVIEW", "CONDITIONAL_CONTEXT_ONLY")),
            "status": "CANDIDATE_PENDING_FRAME_REVIEW" if live else "NO_VIABLE_CLIP_ACQUISITION_NEEDED",
            "search_terms_en": acqs["verified_real_footage_search_en"],
            "refined_requirements": {
                "min_source_seconds": need,
                "framing_pt": "Ação principal (rosto, mãos, objeto-chave) fora da faixa y %d-%d e x %d-%d do quadro 1080x1920; preferir sujeito no terço superior ou centro-baixo escuro e vazio."
                              % (pb["y_from"], pb["y_to"], pb["x_from"], pb["x_to"]),
                "second_shot_pt": "Cena >= 8 s: exige segundo plano real ou movimento de câmera justificado, nunca congelamento." if s["needs_internal_shot_change"] else None,
            },
        })
    n_cand = sum(1 for x in scenes if x["viable_candidates"])
    return {
        "schema_version": "1", "project": "VERBO NO CHAO", "episode_id": "E01",
        "kind": "CLIP_REVIEW_METADATA_ONLY", "frames_viewed": False,
        "basis": "repository evidence; no frame was viewed in this review",
        "scenes_with_viable_candidate": n_cand, "scenes_without_clip": 12 - n_cand,
        "any_clip_approved": False, "rights_cleared": False, "publication_authorized": False,
        "unreconciled": "Project doc MAPA_12_CENAS cites Mixkit #4331 (S03), #99890 (S09), #8748 (S10) but the repository contracts hold Pexels candidates; the two lists are not reconciled and Mixkit ids are NOT VERIFIED here.",
        "scenes": scenes,
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
