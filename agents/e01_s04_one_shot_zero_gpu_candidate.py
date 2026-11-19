"""ONE-SHOT, anonymous free ZeroGPU text-to-video S04 experiment.

No private images, no tokens, no paid APIs, no retries, no publication.
A successful GPU run is ONLY a visual candidate and physical evidence.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

PROJECT="VERBO_NO_CHAO_EXCLUSIVO"
SCENE="VNC-E01V2-S04"
HOST="Fhwang/wan2-video-generation"
FRAMES=145
FPS_TARGET=24
DURATION_REQUIRED=5.82
WIDTH,HEIGHT=576,1024
SEED=47291
PROMPT=(
    "Single uninterrupted photorealistic live-action cinematic macro shot, 6 seconds, "
    "vertical portrait frame. An anonymous adult's hands, no identifiable face, "
    "holding a simple natural reed pen hovering just above completely BLANK "
    "handmade parchment on aged wooden table lit by a tiny oil lamp. "
    "Symbolic ancient Near Eastern-inspired scholarly reenactment, "
    "NOT a historical portrait of the prophet Habakkuk or an authentic artifact. "
    "Slow delicate hand movement, subtle oil flame flutter, gentle real camera "
    "rack focus between reed pen tip and parchment texture, "
    "warm amber light against deep charcoal shadows, 35mm natural film texture, "
    "realistic anatomy and physical camera movement. "
    "No ink marks, no letters, no words, no book, no Bible, no logos, "
    "no decorative text, no typography, no fantasy, no illustration, "
    "no supernatural effects, no graphic design. "
    "Keep lower portion mostly dark and clear for future captions."
)

def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda:source.read(1048576),b""):
            digest.update(part)
    return digest.hexdigest()

def exec_cmd(*args:str,timeout:int=60)->subprocess.CompletedProcess:
    return subprocess.run(list(args),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,timeout=timeout,check=False)

def report_template()->dict:
    return {
        "schema_version":"1.0.0","project":PROJECT,"episode":"VNC-W01-E1",
        "scene":SCENE,"source":"PUBLIC_HF_ZERO_GPU_RESEARCH",
        "space":HOST,"model":"Wan-AI/Wan2.2-TI2V-5B-Diffusers",
        "model_license_claim":"APACHE-2.0_UPSTREAM_MODEL_NOT_SERVICE_APPROVAL",
        "scene_seconds_required":DURATION_REQUIRED,
        "input":{"prompt_sha256":hashlib.sha256(PROMPT.encode()).hexdigest(),
                 "seed":SEED,"num_frames":FRAMES,"width":WIDTH,"height":HEIGHT,
                 "steps":20,"guidance":5.0,"input_image":None,"api":"/generate_video"},
        "job_submissions":0,"user_private_media_uploaded":False,
        "money_spent":0,"external_account_used":False,
        "generation_status":"NOT_STARTED","video_physically_validated":False,
        "visual_director_review":"PENDING","commercial_rights":"PENDING",
        "can_enter_master":False,"publication_authorized":False,
        "is_master":False,
    }

def extract_output_file(result)->Path:
    candidate=result[0] if isinstance(result,(tuple,list)) and result else result
    if isinstance(candidate,dict):
        candidate=candidate.get("video") or candidate.get("path")
    if not isinstance(candidate,(str,Path)):
        raise ValueError("provider_result_has_no_local_video_file")
    path=Path(candidate)
    if not path.is_file():
        raise ValueError("provider_returned_nonexistent_local_video")
    return path

def physical_validate(video:Path,out:Path)->dict:
    from portable_ffmpeg import get_ffmpeg
    ffmpeg,ffprobe=get_ffmpeg()
    probed=exec_cmd(str(ffprobe),"-v","error","-show_entries",
                    "format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate",
                    "-of","json",str(video),timeout=30)
    if probed.returncode:
        raise ValueError("ffprobe_failed")
    data=json.loads(probed.stdout)
    streams=[s for s in data.get("streams",[]) if s.get("codec_type")=="video"]
    if len(streams)!=1:
        raise ValueError("invalid_video_stream_count")
    duration=float(data["format"]["duration"])
    stream=streams[0]
    result={"duration":duration,"width":stream.get("width"),
            "height":stream.get("height"),"fps":stream.get("avg_frame_rate"),
            "codec":stream.get("codec_name")}
    if duration<DURATION_REQUIRED or duration>8.0:
        raise ValueError("provider_duration_out_of_contract")
    if result["width"]!=WIDTH or result["height"]!=HEIGHT:
        raise ValueError("provider_dimensions_differ_from_requested")
    dec=exec_cmd(str(ffmpeg),"-nostdin","-v","error","-xerror",
                 "-i",str(video),"-map","0:v:0","-f","null","-",timeout=100)
    if dec.returncode:
        raise ValueError("full_frame_decode_failed")
    sheet=out/"S04_SIX_REAL_FRAMES_QA.jpg"
    frames=exec_cmd(str(ffmpeg),"-nostdin","-y","-v","error","-i",str(video),
                    "-vf","fps=1,scale=288:512:flags=lanczos,tile=3x2",
                    "-frames:v","1",str(sheet),timeout=60)
    if frames.returncode or not sheet.is_file():
        raise ValueError("contact_sheet_failed")
    result["source_video_sha256"]=sha256(video)
    result["contact_sheet_sha256"]=sha256(sheet)
    result["full_video_decode"]=True
    return result

def run(out:Path)->dict:
    out.mkdir(parents=True,exist_ok=True)
    evidence=report_template()
    try:
        # Precheck before ANY provider submission: this job cannot be priced.
        if FRAMES!=145 or FPS_TARGET!=24 or WIDTH!=576 or HEIGHT!=1024:
            raise ValueError("unexpected_frozen_generation_contract")
        from gradio_client import Client
        client=Client(HOST,verbose=False)
        # Do not retry even if the first call fails or its result is ambiguous.
        evidence["job_submissions"]=1
        evidence["generation_status"]="SUBMITTED_ANONYMOUS_ZERO_GPU"
        job=client.submit(PROMPT,None,WIDTH,HEIGHT,FRAMES,20,5.0,SEED,
                          api_name="/generate_video")
        deadline=time.monotonic()+330
        while not job.done():
            if time.monotonic()>deadline:
                raise TimeoutError("single_zero_gpu_job_timeout_no_retry")
            time.sleep(2)
        result=job.result()
        source=extract_output_file(result)
        if source.stat().st_size<100000 or source.stat().st_size>100_000_000:
            raise ValueError("invalid_source_size")
        target=out/"S04_REAL_GENERATED_FOOTAGE_QA_NOT_MASTER.mp4"
        if target.exists():
            raise ValueError("would_overwrite_source")
        shutil.copyfile(source,target)
        evidence["source_video_bytes"]=target.stat().st_size
        evidence["source_video_sha256"]=sha256(target)
        evidence["generation_status"]="GOT_MP4_UNAPPROVED"
        evidence["physical"]=physical_validate(target,out)
        evidence["generation_status"]="TECHNICAL_MP4_VALID_REQUIRES_EDITORIAL_QA"
        evidence["video_physically_validated"]=True
    except (Exception) as exc:  # preserve candidate status and evidence, no automatic retry
        evidence["generation_status"]="BLOCKED_PROVIDER_OR_VALIDATION"
        evidence["error_type"]=type(exc).__name__
        evidence["error_detail"]=str(exc)[:280]
    (out/"S04_ONE_SHOT_GENERATION_EVIDENCE.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return evidence

if __name__=="__main__":
    v=run(Path("artifacts/vnc_e01_s04_free_trial"))
    print(json.dumps({"status":v["generation_status"],
        "provider_submissions":v["job_submissions"],
        "media_verified":v["video_physically_validated"],
        "master":v["is_master"],"publication":v["publication_authorized"],
        "error":v.get("error_type")},ensure_ascii=False))
    raise SystemExit(0 if v["video_physically_validated"] else 2)
