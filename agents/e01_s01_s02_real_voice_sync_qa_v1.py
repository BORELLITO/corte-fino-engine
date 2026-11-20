"""VERBO NO CHAO E01: safely mux REAL pinned WAV into QA-only S01/S02 preview.

The 28 original karaoke cues are already burned into the pinned 319-frame
source video. This tool never generates speech, downloads stock, alters script,
normalizes loudness, merges to production, or publishes anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import uuid
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/e01_s01_s02_real_voice_sync_qa_20261120_v1.json"
DEST_NAME = "S01_S02_REAL_KARAOKE_AND_ORIGINAL_VOICE_10S_QA_NOT_MASTER.mp4"
REPORT_NAME = "S01_S02_REAL_VOICE_SYNC_QA_REPORT.json"


class VoiceSyncQAError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def contract_checked(path: Path = CONTRACT) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise VoiceSyncQAError("wrong_manifest")
    expected = {
        "schema_version": "1.0.0",
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "scope": "FIRST_319_FRAMES_OF_E01_ONLY_NO_MASTER",
        "approval_state": "S01_VISUAL_APPROVED_S02_CANDIDATE_NOT_APPROVED",
        "status": "PHYSICALLY_VERIFIED_LOCAL_QA_NOT_OWNER_APPROVED_OR_RELEASED",
        "s01_approved_only": True,
        "s02_approved": False,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
    }
    for key, value in expected.items():
        if type(obj.get(key)) is not type(value) or obj.get(key) != value:
            raise VoiceSyncQAError("unsafe_manifest_" + key)
    sources = obj.get("input", {})
    items = (
        ("video", "sha256", "f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c"),
        ("video", "frames", 319), ("video", "width", 720),
        ("video", "height", 1280), ("video", "fps", 30),
        ("video", "audio_streams", 0),
        ("video", "with_original_karaoke_burned", True),
        ("wav", "sha256", "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"),
        ("wav", "sample_rate_hz", 24000), ("wav", "channels", 1),
        ("wav", "duration_seconds", 70.425),
        ("ass", "sha256", "0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a"),
        ("ass", "caption_dialogue_cues", 28), ("ass", "unchanged", True),
    )
    for section, field, value in items:
        value_actual = sources.get(section, {}).get(field)
        if type(value_actual) is not type(value) or value_actual != value:
            raise VoiceSyncQAError("untrusted_input_" + section + "_" + field)
    outputs = obj.get("output_requirements", {})
    req = {
        "mp4_audio_codec": "aac", "audio_sample_rate_hz": 48000,
        "channels": 1, "aac_bitrate": "160k", "fps": 30,
        "video_frames": 319, "width": 720, "height": 1280,
        "video_bitstream_copy": True, "voice_start_offset_seconds": 0,
        "voice_duration_seconds": 10.633333,
        "must_not_add_music": True,
        "must_not_timestretch_or_rerender_voice": True,
        "output_must_not_overwrite_existing": True,
        "full_decode_required": True,
        "master_allowed": False,
        "publication_authorized": False,
        "rights_cleared": False, "merge_authorized": False,
    }
    for key, value in req.items():
        actual = outputs.get(key)
        if type(actual) is not type(value) or actual != value:
            raise VoiceSyncQAError("unsafe_output_" + key)
    return obj


def run_cmd(args: list[str], timeout: int = 90) -> bytes:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False, timeout=timeout)
    if p.returncode != 0:
        raise VoiceSyncQAError("ffmpeg_or_ffprobe_failed")
    return p.stdout


def probe(path: Path) -> dict:
    raw = run_cmd(["ffprobe", "-v", "error", "-show_entries",
                   "format=duration,size:stream=codec_name,codec_type,width,height,"
                   "avg_frame_rate,nb_frames,sample_rate,channels,duration",
                   "-of", "json", str(path)])
    return json.loads(raw)


def check_video(video: Path) -> None:
    d = probe(video)
    streams = d.get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_type") != "video":
        raise VoiceSyncQAError("video_not_video_only")
    v = streams[0]
    if (v.get("codec_name") != "h264" or
        int(v.get("width", 0)) != 720 or
        int(v.get("height", 0)) != 1280 or
        v.get("avg_frame_rate") != "30/1" or
        int(v.get("nb_frames", 0)) != 319 or
        abs(float(d.get("format", {}).get("duration", 0)) - 319 / 30) > 0.002):
        raise VoiceSyncQAError("video_geometry_timing_invalid")


def check_wav(wav: Path) -> None:
    with wave.open(str(wav), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate(),
            w.getnframes(), w.getcomptype()) != (
                1, 2, 24000, 1690200, "NONE"):
            raise VoiceSyncQAError("wav_not_exact_canonical_pcm16")


def check_output(movie: Path) -> dict:
    d = probe(movie)
    streams = d.get("streams", [])
    if len(streams) != 2 or [s.get("codec_type") for s in streams] != ["video", "audio"]:
        raise VoiceSyncQAError("output_streams_not_video_plus_voice")
    v, a = streams
    if (v.get("codec_name") != "h264" or
        (int(v.get("width", 0)), int(v.get("height", 0))) != (720, 1280) or
        v.get("avg_frame_rate") != "30/1" or int(v.get("nb_frames", 0)) != 319):
        raise VoiceSyncQAError("output_video_mismatch")
    if (a.get("codec_name") != "aac" or a.get("sample_rate") != "48000"
        or a.get("channels") != 1 or
        abs(float(a.get("duration", 0)) - 319 / 30) > .035 or
        abs(float(d.get("format", {}).get("duration", 0)) - 319 / 30) > .035):
        raise VoiceSyncQAError("output_audio_duration_or_codec_mismatch")
    run_cmd(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(movie),
             "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], timeout=90)
    return {"duration_seconds": float(d["format"]["duration"]),
            "video_frames": 319, "audio_duration_seconds": float(a["duration"]),
            "audio_codec": "aac", "sample_rate_hz": 48000,
            "channels": 1, "width": 720, "height": 1280,
            "full_audio_and_video_decode_passed": True}


def mux(video: Path, wav: Path, ass: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / DEST_NAME
    report_path = out_dir / REPORT_NAME
    report = {
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "status": "BLOCKED_REAL_VOICE_QA_NOT_REPRODUCED",
        "s01_visual_approved": True,
        "s02_visual_approved": False,
        "rights_cleared": False,
        "master_allowed": False,
        "publication_authorized": False,
        "music_added": False,
    }
    temp = out_dir / ("." + uuid.uuid4().hex + ".mp4")
    try:
        c = contract_checked()
        files = [Path(x).resolve(strict=True) for x in (video, wav, ass)]
        if len(set(files)) != 3 or dest.resolve() in files or temp.resolve() in files:
            raise VoiceSyncQAError("input_alias")
        if dest.exists():
            raise VoiceSyncQAError("existing_output_will_not_be_overwritten")
        if report_path.exists():
            raise VoiceSyncQAError("existing_report_will_not_be_overwritten")
        for x, key in zip(files, ("video", "wav", "ass")):
            if not x.is_file() or sha256(x) != c["input"][key]["sha256"]:
                raise VoiceSyncQAError("input_sha256_mismatch_" + key)
        check_video(files[0])
        check_wav(files[1])
        if files[2].read_text(encoding="utf-8").count("Dialogue: 0,") != 28:
            raise VoiceSyncQAError("captions_28_cues_missing")
        run_cmd([
            "ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
            "-i", str(files[0]), "-i", str(files[1]),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-ac", "1", "-af", "atrim=0:10.633333,asetpts=PTS-STARTPTS",
            "-movflags", "+faststart", "-shortest", str(temp),
        ], timeout=100)
        details = check_output(temp)
        # Exclusive hard link prevents a race from overwriting any prior QA.
        os.link(temp, dest)
        report.update(
            status="REAL_WAV_ASS_AAC_QA_VERIFIED_SCENE_S02_STILL_PENDING",
            source_sha256={k: sha256(v) for k,v in zip(("video","wav","ass"), files)},
            preview={**details, "filename": DEST_NAME,
                     "sha256": sha256(dest), "bytes": dest.stat().st_size},
            source_wav_does_not_change=True,
            video_bitstream_copied_without_reencode=True,
            preview_is_full_episode=False
        )
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired,
            UnicodeDecodeError, wave.Error) as exc:
        report["error_type"] = type(exc).__name__
        if isinstance(exc, VoiceSyncQAError):
            report["error_code"] = str(exc)
    finally:
        temp.unlink(missing_ok=True)
    if not report_path.exists():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "s02_visual_approved": False,
                      "master_allowed": False, "publication_authorized": False}))
    return 0 if report["status"].startswith("REAL_WAV_ASS_AAC_QA_VERIFIED") else 2


def main() -> int:
    p = argparse.ArgumentParser()
    for arg in ("video", "wav", "ass", "out_dir"):
        p.add_argument("--" + arg.replace("_", "-"), type=Path, required=True)
    a = p.parse_args()
    return mux(a.video, a.wav, a.ass, a.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
