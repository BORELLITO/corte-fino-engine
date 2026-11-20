"""Assemble the provider package (package.json + media) that orchestrator.runflow validates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .captions import Aligner, build_cues, verify_cues, write_ass
from .common import (ProducerError, audio_integrity_ok, decodes_cleanly, duration_sec,
                     run_ffmpeg, sha256_file)
from .footage import FootageProvider
from .music import write_music
from .voice import VoiceProvider, strip_audio_tags

SPEC_REQUIRED = ("episode_id", "scenes")


def _check_spec(spec: Any) -> None:
    if not isinstance(spec, dict) or any(k not in spec for k in SPEC_REQUIRED):
        raise ProducerError("producer:spec:invalid")
    scenes = spec["scenes"]
    if not isinstance(scenes, list) or not scenes:
        raise ProducerError("producer:spec:no_scenes")
    ids = [s.get("id") for s in scenes if isinstance(s, dict)]
    if len(ids) != len(scenes) or len(set(ids)) != len(ids):
        raise ProducerError("producer:spec:scene_ids_invalid_or_duplicate")
    for s in scenes:
        for key in ("narration", "footage_query"):
            value = s.get(key)
            ok = (isinstance(value, str) and value.strip()) or (
                key == "footage_query" and isinstance(value, list) and value
                and all(isinstance(q, str) and q.strip() for q in value))
            if not ok:
                raise ProducerError(f"producer:spec:scene_{s.get('id')}:{key}_missing")


def build_package(spec: dict[str, Any], out_dir: Path, voice: VoiceProvider,
                  footage: FootageProvider, aligner: Aligner | None = None,
                  rejected: set[str] | None = None) -> Path:
    _check_spec(spec)
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "package.json").exists():
        raise ProducerError("producer:refuse_overwrite_existing_package")
    work = out_dir / "work"
    clips_dir = out_dir / "clips"
    work.mkdir(exist_ok=True)
    clips_dir.mkdir(exist_ok=True)
    scenes = spec["scenes"]

    # 1. Voice: one WAV per scene -> measured durations -> concatenated narration.
    durations, scene_wavs = [], []
    for scene in scenes:
        wav = work / f"{scene['id']}.wav"
        voice.synthesize(scene["narration"], wav)
        durations.append(duration_sec(wav))
        scene_wavs.append(wav)
    listing = work / "voice_list.txt"
    listing.write_text("".join(f"file '{w.name}'\n" for w in scene_wavs), encoding="utf-8")
    voice_path = out_dir / "voice.wav"
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-c:a", "pcm_s16le", str(voice_path)])
    total = duration_sec(voice_path)

    # 2. Footage: each scene gets a clip of at least its audio length, never reused.
    used: set[str] = set(rejected or ())  # protected rejections are pre-seeded as "already used"
    assets = []
    for scene, dur in zip(scenes, durations):
        clip = footage.fetch(scene["footage_query"], dur, used, clips_dir)
        digest = sha256_file(clip.path)
        used.update({clip.asset_id, clip.source_url, digest})
        assets.append({
            "asset_id": clip.asset_id, "scene_id": scene["id"],
            "path": str(clip.path.relative_to(out_dir)), "source_url": clip.source_url,
            "source_hash": digest, "in": 0.0, "out": round(dur, 3),
            "license_name": clip.license_name, "license_url": clip.license_url,
            "rights_status": "PENDING_REVIEW",
        })

    # 3. Music: original procedural score, no samples.
    music_path = out_dir / "music.wav"
    write_music(music_path, total + 2.0, seed=int(spec.get("music_seed", 1)))

    # 4. Captions: aligned to real audio; "synchronized" only if ASR alignment verified them.
    windows, cursor = [], 0.0
    for scene, dur in zip(scenes, durations):
        windows.append((strip_audio_tags(scene["narration"]), cursor, cursor + dur))
        cursor += dur
    words = [w for text, _, _ in windows for w in text.split()]
    times = aligner.align(voice_path, words) if aligner else None
    cues = build_cues(windows, times)
    cue_errors = verify_cues(cues, windows)
    write_ass(cues, out_dir / "captions.ass")
    safe_area = not any(e.endswith(":safe_area") for e in cue_errors)
    synchronized = aligner is not None and not cue_errors

    # 5. Gates are computed from bytes, never copied from a claim.
    ids = [a["asset_id"] for a in assets]
    urls = [a["source_url"] for a in assets]
    hashes = [a["source_hash"] for a in assets]
    unique = all(len(set(x)) == len(x) for x in (ids, urls, hashes))
    gates = {
        "clip_repetition": "PASS" if unique else "FAIL",
        "audio_integrity": "PASS" if audio_integrity_ok(voice_path) and audio_integrity_ok(music_path) else "FAIL",
        "video_decode": "PASS" if all(decodes_cleanly(out_dir / a["path"]) for a in assets) else "FAIL",
        "subtitle_safe_area": "PASS" if safe_area else "FAIL",
    }

    package = {
        "engine_id": "verbo-no-chao",
        "episode_id": spec["episode_id"],
        "state": "PREVIEW_READY",
        "owner_approval": False,
        "publication_authorized": False,
        "execution": {"mode": "cloud_only", "device_role": "control_only", "legacy_projects_used": False},
        "assets": assets,
        "audio": {"engine": voice.engine, "language": voice.language,
                  "format": "WAV 24 kHz mono PCM16", "persisted": True, "segments": len(scenes),
                  "duration_sec": round(total, 3), "path": "voice.wav", "sha256": sha256_file(voice_path)},
        "music": {"present": True, "ducking": True, "origin": "original_procedural",
                  "external_samples": False, "license_status": "CLEARED",
                  "path": "music.wav", "hash": sha256_file(music_path)},
        "captions": {"present": True, "safe_area_pass": safe_area, "synchronized": synchronized,
                     "alignment": "asr_word_timestamps" if aligner else "none_proportional_unverified",
                     "path": "captions.ass"},
        "output": {"file": "output.mp4", "width": 1080, "height": 1920},
        "gates": gates,
        "rights": {"visual_review": "PENDING", "voice_review": "PENDING",
                   "music_review": "CLEARED", "monetization": "PENDING"},
        "artifacts": {
            "audio": {"path": "voice.wav", "sha256": sha256_file(voice_path)},
            "music": {"path": "music.wav", "sha256": sha256_file(music_path)},
            "captions": {"path": "captions.ass", "sha256": sha256_file(out_dir / "captions.ass")},
        },
        "render": {"enabled": True},
    }
    (out_dir / "package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    return out_dir
