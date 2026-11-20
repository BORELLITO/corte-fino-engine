"""Refit the 12 E01 scenes to the real Johnes voice (76.67 s). Timing only: no media, no rights change.

A scene starts at the first word of a sentence; the cut is the midpoint of the silence before it,
so no cut ever lands inside a spoken word.
"""
import json
from pathlib import Path

from agents.content_production import check
from agents.e01_v3_voice_captions import PLAN, SPEECH_DURATION, load
from agents.e01_v2_caption_pipeline import make_cues_from_plan

OLD_PLAN = Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
OUT = Path("contracts/e01_v3_12_scene_refit_v1.json")
# first word index of each scene (all are sentence starts), chosen by narrative function
STARTS = [0, 16, 20, 34, 41, 57, 75, 100, 120, 130, 151, 161]
MIN_SCENE, MAX_SCENE = 2.5, 10.0


def build() -> dict:
    words, duration = load()
    check(abs(duration - SPEECH_DURATION) < 1e-9, "refit:duration")
    old = json.loads(OLD_PLAN.read_text(encoding="utf-8"))["scenes"]
    check(len(old) == 12 and len(STARTS) == 12, "refit:scene_count")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))["cues"]
    cues = make_cues_from_plan(words, plan, duration)
    cue_of = {w["index"]: n + 1 for n, c in enumerate(cues) for w in c["words"]}
    cuts = [0.0]
    for i in STARTS[1:]:
        prev, cur = words[i - 1], words[i]
        check(prev["text"][-1] in ".?!", "refit:not_sentence_start")
        cuts.append(round((prev["end"] + cur["start"]) / 2, 3))
    cuts.append(round(duration, 3))
    scenes = []
    for n, o in enumerate(old):
        a, b = cuts[n], cuts[n + 1]
        first = STARTS[n]
        last = (STARTS[n + 1] if n < 11 else len(words)) - 1
        scenes.append({
            "id": o["id"], "title": o["title"],
            "start_seconds": a, "end_seconds": b, "duration_seconds": round(b - a, 3),
            "previous_start_seconds": o["start_seconds"], "previous_end_seconds": o["end_seconds"],
            "first_word_index": first, "last_word_index": last,
            "first_caption_cue": cue_of[first], "last_caption_cue": cue_of[last],
            "text": " ".join(w["text"] for w in words[first:last + 1]),
            "needs_internal_shot_change": (b - a) >= 8.0,
        })
    return {
        "schema_version": "1", "project": "VERBO NO CHAO", "episode_id": "E01",
        "kind": "SCENE_TIMING_REFIT_ONLY",
        "voice": "Johnes Bittar", "duration_seconds": round(duration, 3),
        "audio_sha256": "35f435199df54f6380d80d129ddd95b04ddb0ff5f97ede97a74da856995b5685",
        "rule": "scene starts at a sentence start; cut = midpoint of the silence before it",
        "media_changed": False, "rights_changed": False, "approved_for_export": False,
        "publication_authorized": False,
        "note": "S01 stays the approved visual DIRECTION only (not a master); S02 not approved; "
                "S03/S09 candidates; S10 crop vetoed. Scenes flagged needs_internal_shot_change "
                "(>=8 s) need a second real shot or a justified slow move, not a freeze.",
        "scenes": scenes,
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
