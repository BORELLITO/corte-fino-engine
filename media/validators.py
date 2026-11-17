"""Dry-run validation for visual, audio and caption contracts."""

from __future__ import annotations

from typing import Any


def _required(mapping: Any, keys: tuple[str, ...], prefix: str) -> list[str]:
    if not isinstance(mapping, dict):
        return [f"{prefix}:not_object"]
    return [
        f"{prefix}:{key}"
        for key in keys
        if mapping.get(key) is None
        or (isinstance(mapping.get(key), str) and not mapping[key].strip())
    ]


def _valid_interval(item: dict[str, Any], prefix: str) -> list[str]:
    start = item.get("start_ms")
    end = item.get("end_ms")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        return [f"{prefix}:interval"]
    return []


def validate_audiovisual_package(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["audiovisual:not_object"]
    errors = _required(
        payload,
        ("video_id", "format", "resolution", "fps", "scenes", "audio", "captions"),
        "audiovisual",
    )
    if payload.get("format") != "vertical_short":
        errors.append("audiovisual:format")
    if payload.get("resolution") != "1080x1920":
        errors.append("audiovisual:resolution")
    if payload.get("fps") not in {30, 60}:
        errors.append("audiovisual:fps")

    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("audiovisual:scenes")
    else:
        previous_end = -1
        for index, scene in enumerate(scenes):
            prefix = f"scene:{index}"
            errors.extend(_required(
                scene,
                ("scene_id", "narration_ref", "visual_intent", "relation", "rights_ref"),
                prefix,
            ))
            errors.extend(_valid_interval(scene, prefix))
            if isinstance(scene, dict):
                if scene.get("relation") not in {"direct", "symbolic", "atmospheric", "contextual"}:
                    errors.append(f"{prefix}:relation")
                start = scene.get("start_ms")
                end = scene.get("end_ms")
                if isinstance(start, int) and isinstance(end, int):
                    if start < previous_end:
                        errors.append(f"{prefix}:overlap")
                    previous_end = max(previous_end, end)

    errors.extend(validate_audio(payload.get("audio")))
    errors.extend(validate_captions(payload.get("captions")))
    return sorted(set(errors))


def validate_audio(audio: Any) -> list[str]:
    if not isinstance(audio, dict):
        return ["audio:not_object"]
    errors = []
    voice = audio.get("voice")
    music = audio.get("music")
    errors.extend(_required(
        voice,
        ("source", "language", "commercial_use", "evidence_ref", "intelligibility_status"),
        "voice",
    ))
    errors.extend(_required(
        music,
        ("source", "commercial_use", "evidence_ref", "voice_priority", "lyrics"),
        "music",
    ))
    if isinstance(voice, dict):
        if voice.get("language") != "pt-BR":
            errors.append("voice:language")
        if voice.get("commercial_use") is not True:
            errors.append("voice:commercial_use")
        if voice.get("intelligibility_status") != "PASSED":
            errors.append("voice:intelligibility_status")
    if isinstance(music, dict):
        if music.get("commercial_use") is not True:
            errors.append("music:commercial_use")
        if music.get("voice_priority") is not True:
            errors.append("music:voice_priority")
        if music.get("lyrics") not in {"none", "instrumental", "cleared"}:
            errors.append("music:lyrics")
    return errors


def validate_captions(captions: Any) -> list[str]:
    if not isinstance(captions, dict):
        return ["captions:not_object"]
    errors = _required(captions, ("language", "max_lines", "no_overlap", "segments"), "captions")
    if captions.get("language") != "pt-BR":
        errors.append("captions:language")
    if captions.get("max_lines") != 2:
        errors.append("captions:max_lines")
    if captions.get("no_overlap") is not True:
        errors.append("captions:no_overlap")
    segments = captions.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("captions:segments")
        return errors
    previous_end = -1
    for index, segment in enumerate(segments):
        prefix = f"caption:{index}"
        errors.extend(_required(segment, ("start_ms", "end_ms", "text"), prefix))
        errors.extend(_valid_interval(segment, prefix))
        if isinstance(segment, dict):
            text = segment.get("text", "")
            if isinstance(text, str) and text.count("\n") + 1 > 2:
                errors.append(f"{prefix}:max_lines")
            start = segment.get("start_ms")
            if isinstance(start, int) and start < previous_end:
                errors.append(f"{prefix}:overlap")
            end = segment.get("end_ms")
            if isinstance(end, int):
                previous_end = max(previous_end, end)
    return errors
