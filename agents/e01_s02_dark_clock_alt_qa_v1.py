"""VERBO NO CHAO E01 S02: dark-clock 4K stock physical QA, NOT a master.

Single source Pexels ID 29862379, with strict redirect and 160MB cap inherited.
Crop 3840x2160 landscape to native 1214x2160 vertical *before* 720x1280
review scaling. S01 approval is never inherited or changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from agents.e01_stock_candidates import ROOT
from agents.e01_s01_multi_stock_pilot_v1 import download_source, probe
from agents.e01_s01_single_take_stock_qa import crop_native, frame_at, run_cmd
from agents.e01_s02_waiting_clock_qa_v1 import contact_sheet, render
from agents.e01_s01_night_rain_motif_probe_v1 import watermark

CONTRACT = Path("contracts/e01_s02_dark_clock_alt_preflight_20261119_v1.json")
S01_APPROVAL = Path("contracts/e01_s01_owner_visual_approval_20261119_v1.json")
SOURCE_ID = 29862379
SOURCE_URL = "https://www.pexels.com/video/dramatic-clock-ticking-in-dark-room-29862379/"
S01_SHA = "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961"
FRAMES = 147


class DarkClockQAError(ValueError):
    pass


def validate_contract(root=ROOT, obj=None):
    root = Path(root)
    if obj is None:
        obj = json.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise DarkClockQAError("invalid_contract")
    expected = {
        "schema_version": "1.0.0",
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "scene_id": "VNC-E01V2-S02",
        "purpose": "COMPARE_DARK_CLOCK_REAL_STOCK_WITH_EXISTING_S02_QA_ONLY",
        "artistic_state": "S01_USER_APPROVED_S02_UNAPPROVED",
        "s01_preview_sha256": S01_SHA,
        "s01_preview_immutable": True,
        "current_s02_reference_source_id": 7034348,
        "current_s02_grade_a_preview_sha256": "0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3",
        "current_s02_not_rejected_or_approved": True,
        "source_media_persisted": False,
        "s02_user_approved": False,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
        "paid_services_authorized": False,
    }
    for key, value in expected.items():
        if type(obj.get(key)) is not type(value) or obj[key] != value:
            raise DarkClockQAError("identity_rights_or_approval_drift_" + key)
    cand = obj.get("candidate")
    if not isinstance(cand, dict):
        raise DarkClockQAError("candidate_missing")
    e = {
        "source_id": SOURCE_ID, "page_url": SOURCE_URL,
        "source_page_license": "Free",
        "listing_width": 3840, "listing_height": 2160,
        "listing_fps": 50, "listing_duration_seconds": 11,
        "minimum_native_portrait_crop": [1080, 1920],
        "expected_exact_center_native_crop": [1214, 2160],
        "mp4_verified": False, "rights_cleared": False,
        "editorial_approved": False,
    }
    for key, value in e.items():
        if type(cand.get(key)) is not type(value) or cand[key] != value:
            raise DarkClockQAError("untrusted_candidate_" + key)
    p = obj.get("required_output")
    e = {
        "portrait_width":720, "portrait_height":1280,
        "fps":30, "frames":FRAMES,
        "watermark":"PREVIA DE QA - NAO PUBLICAR",
        "audio":False, "captions":False
    }
    if not isinstance(p, dict) or any(
        type(p.get(k)) is not type(v) or p[k] != v for k,v in e.items()
    ):
        raise DarkClockQAError("release_preview_contract_invalid")
    if obj.get("requested_frame_samples_s") != [0.5,2.4,4.5]:
        raise DarkClockQAError("frame_sampling_drift")
    approval = json.loads((root / S01_APPROVAL).read_text(encoding="utf-8"))
    if (approval.get("approval_status") != "APPROVED_S01_VISUAL_DIRECTION_ONLY"
        or approval.get("approval_scope",{}).get("preview_sha256") != S01_SHA
        or approval.get("approval_scope",{}).get("extend_to_other_scenes_automatically") is not False):
        raise DarkClockQAError("prior_s01_approval_drift")
    return cand


def run(out: Path, root=ROOT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    video = out / "S02_DARK_CLOCK_29862379_REVIEW_ONLY.mp4"
    contact = out / "S02_DARK_CLOCK_29862379_FRAMES_QA.jpg"
    evidence = {
        "project_id":"VERBO_NO_CHAO_EXCLUSIVO",
        "scene_id":"VNC-E01V2-S02",
        "candidate_source_id":SOURCE_ID,
        "status":"BLOCKED_NO_PHYSICAL_VIDEO",
        "art_direction_approved":False,
        "rights_cleared":False,
        "master_allowed":False,
        "publication_authorized":False,
        "original_stock_persisted":False,
        "source_camera_capture_independently_proven":False,
        "existing_s01_source_modified":False,
    }
    try:
        validate_contract(root)
        with tempfile.TemporaryDirectory(prefix="vnc_s02_dark_clock_") as scratch:
            work = Path(scratch)
            movie, meta = download_source({"id": SOURCE_ID, "page": SOURCE_URL}, work)
            p = probe(movie, min_seconds=4.88, min_width=1080, min_height=1920)
            cw,ch = crop_native(p["width"], p["height"])
            if cw < 1080 or ch < 1920:
                raise DarkClockQAError("native_crop_not_1080x1920")
            run_cmd([
                "ffmpeg","-nostdin","-v","error","-xerror",
                "-i",str(movie),"-map","0:v:0","-an","-f","null","-"
            ],180)
            frames = [frame_at(movie, t, p["width"], p["height"])
                      for t in (0.5, 2.4, 4.5)]
            contacts = contact_sheet(frames, contact)
            watermark(work / "qa_overlay.png")
            preview = render(movie, work / "qa_overlay.png", video,
                             p["width"], p["height"])
            # 'render' performs full MP4 decode before returning.
            evidence.update(
                status="PHYSICAL_ALT_READY_FOR_VISUAL_INSPECTION_ONLY",
                source={**meta,**p,"full_decode_success":True,
                        "portrait_native_crop":[cw,ch],
                        "origin_and_third_party_rights_unverified":True},
                frames=contacts,
                preview={**preview,"path":video.name,"sha256":hashlib.sha256(
                    video.read_bytes()).hexdigest(),
                    "bytes":video.stat().st_size,"frames":FRAMES,"fps":30,
                    "full_preview_decode_success":True,
                    "watermarked":True,"contains_audio":False},
            )
            movie.unlink(missing_ok=True)
    except Exception as exc:
        video.unlink(missing_ok=True)
        evidence["error_type"] = type(exc).__name__
        evidence["error_code"] = (str(exc) if isinstance(exc,DarkClockQAError)
                                  else "provider_or_media_processing_error")
    (out / "S02_DARK_CLOCK_29862379_REPORT.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8"
    )
    print(json.dumps({"status":evidence["status"],
                      "source_id":SOURCE_ID,
                      "editorial_approved":False,
                      "master_allowed":False,
                      "publication_authorized":False,
                      "error":evidence.get("error_type")}))
    return 0 if evidence["status"].startswith("PHYSICAL_ALT") else 2


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    return run(parser.parse_args().out)


if __name__ == "__main__":
    raise SystemExit(main())
