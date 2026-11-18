"""Fail-closed verifier for real E01v2 12-scene media created outside Actions.

The source images/movie are backed up to the owner's private ChatGPT Library,
NOT to the public GitHub repo or Actions. Source ZIP and MP4 must be furnished
as actual local bytes to get a physical verification result. Metadata alone
NEVER unlocks footage, commercial rights, master or publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from agents.content_production import ProductionError, check

PATH="contracts/e01_v2_12_real_visual_roughcut_evidence_v1.json"
EXACT_WAV_SHA="4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
EXACT_ASR_ASS_SHA="0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a"
EXACT_SCRIPT_SHA="c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
EXACT_ZIP_SHA="151f488d6f73416d5a937e726a7a99dc9cb86d922f54a951746ec116228d0b75"
EXACT_VIDEO_SHA="a080e7d572a28befb8657157bfe3fedbb3b0d1b30d1276beee3a2173f45c2cfa"


def sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def manifest(root: Path) -> dict[str, Any]:
    src=root/PATH
    check(src.is_file(), "visual:missing_contract")
    e=json.loads(src.read_text(encoding="utf-8"))
    check(e.get("project")=="verbo-no-chao"
          and e.get("episode_id")=="VNC-W01-E1"
          and e.get("candidate_version")==2
          and e.get("source_script_sha256")==EXACT_SCRIPT_SHA
          and e.get("source_voice_wav_sha256")==EXACT_WAV_SHA
          and e.get("source_caption_ass_sha256")==EXACT_ASR_ASS_SHA
          and e.get("source_package_sha256")==EXACT_ZIP_SHA
          and e.get("real_local_preview",{}).get("sha256")==EXACT_VIDEO_SHA
          and e.get("status")=="REAL_LOCAL_ROUGHCUT_MEDIA_BYTES_VERIFIED_NOT_CLOUD_EXECUTABLE"
          and e.get("reproducible_in_github_actions_now") is False,
          "visual:manifest_unauthenticated_or_false_cloud_claim")
    shots=e.get("shots")
    check(isinstance(shots,list) and len(shots)==12
          and e.get("shot_count")==12,
          "visual:exact_twelve_scenes_required")
    prior=0.0
    paths=set()
    for index,shot in enumerate(shots,1):
        expected_id=f"E01V2-S{index:02}"
        expected_path=f"stills/E01V2_SCENE_{index:02}.jpg"
        check(shot.get("id")==expected_id
              and shot.get("derived_output")==expected_path
              and shot.get("width")==720
              and shot.get("height")==1280
              and shot.get("source")=="CHATGPT_IMAGEGEN_ORIGINAL"
              and re.fullmatch(r"[0-9a-f]{64}",shot.get("sha256",""))
              and isinstance(shot.get("size_bytes"),int)
              and 20000 <= shot["size_bytes"] <= 2000000
              and shot.get("image_is_ai_generated") is True
              and shot.get("source_resolution_adequate_for_master") is False
              and shot.get("licensed_for_commercial_publication") is False
              and shot.get("verified_final_visual_quality") is False,
              "visual:asset_metadata_invalid")
        check(abs(shot["start_seconds"]-prior)<0.001
              and shot["end_seconds"]>prior,
              "visual:scene_timeline_gap_or_overlap")
        prior=shot["end_seconds"]
        check(expected_path not in paths, "visual:duplicate_asset_path")
        paths.add(expected_path)
    check(abs(prior-70.425)<0.001,"visual:duration_does_not_fit_wav")
    vid=e.get("real_local_preview",{})
    check(vid.get("width")==720 and vid.get("height")==1280
          and vid.get("fps")==30 and vid.get("frames")==2113
          and abs(vid.get("duration_seconds",0)-70.433)<.005
          and vid.get("video_codec")=="h264"
          and vid.get("audio_codec")=="aac"
          and vid.get("pan_zoom_motion_simulated") is True
          and vid.get("assets_are_actual_motion_video_clips") is False
          and vid.get("whole_video_playback_verified") is False,
          "visual:fake_clip_or_invalid_video_metrics")
    for field in ("commercial_voice_rights_cleared","music_included",
                  "music_license_verified","full_1080x1920_master_exists",
                  "visual_identity_full_qa_passed",
                  "continuity_and_loop_final_qa_passed",
                  "publication_authorized"):
        check(e.get(field) is False,"visual:fake_commercial_or_release_approval")
    check(e.get("storyboard_tile_native_resolutions_low") is True,
          "visual:low_res_risk_suppressed")
    return e


def package(root: Path, asset_zip: Path) -> dict[str, Any]:
    e=manifest(root)
    check(asset_zip.is_file()
          and asset_zip.stat().st_size==e["source_package_bytes"]
          and sha256(asset_zip)==EXACT_ZIP_SHA,
          "visual:zip_sha_or_size_not_exact")
    with zipfile.ZipFile(asset_zip,"r") as z:
        infos=z.infolist()
        names=[i.filename for i in infos]
        check(len(infos)<=30
              and len(names)==len(set(names))
              and all(not n.startswith("/") and ".." not in Path(n).parts
                      and "\\" not in n for n in names),
              "visual:unsafe_zip_entries")
        check(sum(i.file_size for i in infos) < 11000000
              and all(i.file_size<=3500000 for i in infos),
              "visual:excessive_unpacked_bytes")
        for item in e["shots"]:
            name=item["derived_output"]
            check(name in names,"visual:missing_scene_image")
            raw=z.read(name)
            check(len(raw)==item["size_bytes"]
                  and hashlib.sha256(raw).hexdigest()==item["sha256"]
                  and raw[:3]==b"\xff\xd8\xff" and raw[-2:]==b"\xff\xd9",
                  "visual:scene_image_bytes_or_jpeg_invalid")
        for name,digest in (
            ("original-imagegen-contact-sheet.png",e["source_imagegen_contact_sheet_sha256"]),
            ("original-imagegen-full-opening.png",e["source_imagegen_portrait_sha256"]),
        ):
            check(name in names and hashlib.sha256(z.read(name)).hexdigest()==digest,
                  "visual:original_provenance_image_changed")
    return {"scene_bytes_sha_verified":True,"scene_count":12,
            "original_generation_parent_shas_verified":True,
            "assets_sourced_from_user_private_library":True,
            "commercial_rights_cleared":False,
            "hd_master_approved":False,
            "publication_authorized":False}


def video(root:Path, mp4:Path) -> dict[str,Any]:
    e=manifest(root)
    check(mp4.is_file()
          and mp4.stat().st_size==e["real_local_preview"]["size_bytes"]
          and sha256(mp4)==EXACT_VIDEO_SHA,
          "visual:video_bytes_or_sha_changed")
    return {"real_movie_byte_identity_verified":True,
            "mp4_bytes":mp4.stat().st_size,"sha256":EXACT_VIDEO_SHA,
            "real_video_decoding_in_this_run":False,
            "final_video_master_approved":False,
            "publication_authorized":False}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--zip",type=Path)
    p.add_argument("--mp4",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    out={"status":"BLOCKED_PHYSICAL_SOURCE_ASSETS_NOT_AVAILABLE_IN_THIS_ENVIRONMENT",
         "publication_authorized":False,"final_video_master_approved":False}
    try:
        e=manifest(args.root.resolve())
        if args.zip and args.mp4:
            pack=package(args.root.resolve(),args.zip.resolve())
            mov=video(args.root.resolve(),args.mp4.resolve())
            out={"status":"REAL_LOCAL_ROUGHCUT_REVERIFIED_NOT_MASTER",
                 "episode_id":e["episode_id"],
                 "assets":pack,"video":mov,
                 "voice_rights_cleared":False,"music_included":False,
                 "final_video_master_approved":False,
                 "publication_authorized":False}
    except Exception as exc:
        out["status"]="BLOCKED_INVALID_REAL_MEDIA_PROVENANCE"
        out["error_code"]=str(exc) if isinstance(exc,ProductionError) else type(exc).__name__
    if args.output:
        dst=args.output.resolve();dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False))
    return 0 if out["status"]=="REAL_LOCAL_ROUGHCUT_REVERIFIED_NOT_MASTER" else 2


if __name__=="__main__":
    raise SystemExit(main())
