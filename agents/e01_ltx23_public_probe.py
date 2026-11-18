"""One bounded LTX-2.3 ZeroGPU text-to-video *proof*, never a release asset.

Public anonymous Space only. No paid endpoint, HF token, private files or retries.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SPACE = "Lightricks/LTX-2-3"
SPACE_API = "https://huggingface.co/api/spaces/Lightricks/LTX-2-3"
OUTPUT = Path("artifacts/e01_ltx23_zero_probe")
REPORT = OUTPUT / "report.json"
PROMPT = (
    "A single uninterrupted cinematic shot inside a modest home at night. "
    "An anonymous adult seen from behind in a charcoal jacket sits beside a "
    "rain-streaked dark window, a closed notebook on a worn wooden desk. "
    "Warm dim amber lamp, steady slow camera push in, natural breathing and "
    "raindrops sliding on the glass. Photorealistic, restrained faith noir, "
    "hands anatomically natural, no identifiable face or text, no logos, "
    "no voiceover or miracles. This is original fictional AI video."
)
BASE = {
    "project": "verbo-no-chao",
    "episode_id": "VNC-W01-E1",
    "scene_id": "VNC-E01V2-S01",
    "source": SPACE,
    "generator": "LTX-2.3 Distilled official public ZeroGPU Space",
    "generation_origin": "AI_GENERATED_NOT_CAMERA_FOOTAGE",
    "license_name": "LTX-2 Community License Agreement",
    "requested_seconds": 2.0,
    "requested_resolution": [576, 1024],
    "target_scene_seconds": 5.74,
    "master_resolution": [1080, 1920],
    "anonymous": True,
    "no_account_login": True,
    "no_credit_card_or_paid_plan": True,
    "third_party_rights_cleared": False,
    "commercial_release_authorized": False,
    "source_copyright_review_complete": False,
    "native_master_resolution": False,
    "matches_full_scene_duration": False,
    "approved_for_master": False,
    "publication_authorized": False,
    "master_rendered": False,
}

def stage_is_running(payload):
    if not isinstance(payload, dict):
        return False
    stage = (payload.get("runtime") or {}).get("stage")
    return isinstance(stage,str) and stage.upper() in {"RUNNING"}

def save(state, **data):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    result = dict(BASE,status=state)
    result.update(data)
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":state,"report":str(REPORT),
        "approved_for_master":False,"publication_authorized":False},
        ensure_ascii=False),flush=True)

def preflight():
    req=urllib.request.Request(SPACE_API,headers={"User-Agent":"VNC-E01-public-preflight/1.0"})
    with urllib.request.urlopen(req,timeout=15) as response:
        if response.status!=200:
            return False,"unexpected_http_status"
        body=response.read(180000)
    payload=json.loads(body)
    stage=(payload.get("runtime") or {}).get("stage")
    return stage_is_running(payload),str(stage or "NO_RUNTIME_STATUS")[:64]

def run():
    save("STARTED_NO_FOOTAGE")
    try:
        running,stage=preflight()
        if not running:
            save("BLOCKED_PROVIDER_NOT_RUNNING",runtime_stage=stage,
                 media_file_received=False)
            return 0
        save("PROVIDER_RUNNING_RENDER_UNVERIFIED",runtime_stage=stage,
             media_file_received=False)
        # Gradio endpoint is authored by official Space's generate_video function.
        from gradio_client import Client
        client=Client(SPACE,verbose=False)
        output=client.predict(None,PROMPT,2.0,False,42,False,1024,576,
                              api_name="/generate_video")
        if not isinstance(output,(tuple,list)) or not output:
            raise RuntimeError("invalid_return_payload")
        path=output[0]
        if isinstance(path,dict):
            path=path.get("video") or path.get("path") or path.get("name")
        if not isinstance(path,str) or not Path(path).is_file():
            raise RuntimeError("no_video_file_returned")
        original=Path(path)
        if original.stat().st_size<15000 or original.stat().st_size>80000000:
            raise RuntimeError("unreasonable_media_size")
        dest=OUTPUT/"VNC-E01-S01-LTX23-MOVEMENT-TEST-NOT-MASTER.mp4"
        shutil.copy2(original,dest)
        p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=width,height,codec_name,avg_frame_rate,duration:format=duration",
            "-of","json",str(dest)],text=True,capture_output=True,
            timeout=30,check=False)
        if p.returncode!=0:
            raise RuntimeError("ffprobe_failed")
        info=json.loads(p.stdout)
        streams=info.get("streams") or []
        if len(streams)!=1 or not streams[0].get("width") or not streams[0].get("height"):
            raise RuntimeError("video_stream_invalid")
        full=subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
            "-i",str(dest),"-map","0:v:0","-an","-f","null","-"],
            capture_output=True,text=True,timeout=90,check=False)
        if full.returncode!=0:
            raise RuntimeError("full_decode_failed")
        duration=float(streams[0].get("duration") or info.get("format",{}).get("duration") or 0)
        save("PHYSICAL_AI_MOTION_CLIP_VERIFIED_NO_MASTER",
             sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
             bytes=dest.stat().st_size,
             width=streams[0]["width"],height=streams[0]["height"],
             duration_seconds=duration,codec=streams[0].get("codec_name"),
             frame_rate=streams[0].get("avg_frame_rate"),
             full_stream_decoded=True,scene_duration_coverage=duration>=5.74,
             mp4_artifact_name=dest.name,rights_cleared=False)
        return 0
    except Exception as err:
        # Failure is a terminal no-release diagnostic, never automatic retry.
        save("BLOCKED_PUBLIC_GPU_OR_CLIENT",error_type=type(err).__name__,
             error_description=str(err)[:200].replace("\n"," "),
             media_file_received=False)
        return 0

if __name__=="__main__":
    raise SystemExit(run())
