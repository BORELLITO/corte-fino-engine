"""Build v3c SRT/VTT/ASS karaoke for the Johnes Bittar voice CANDIDATE.

Offline and deterministic: reads contracts/e01_v3_voice_johnes_word_timing_v1.json
only. Does not replace the canonical 70.425 s WAV, is not a master and
authorizes no publication.
"""
import argparse
import hashlib
import json
from pathlib import Path

from agents.content_production import check
from agents.e01_v2_caption_pipeline import (
    SCRIPT_SHA, canonical_words, export_ass, export_srt, export_vtt, make_cues,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/e01_v3_voice_johnes_word_timing_v1.json"
SCRIPT = ROOT / "contracts/e01_script_v2_candidate.json"
SPEECH_DURATION = 76.67


def load(path: Path = CONTRACT) -> tuple[list[dict], float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    check(data["provenance"]["script_sha256"] == SCRIPT_SHA
          and data["word_count"] == 182 and len(data["words"]) == 182
          and data["speech_duration_seconds"] == SPEECH_DURATION
          and data["voice_rights_cleared"] is False
          and data["production_audio_master_approved"] is False
          and data["publication_authorized"] is False,
          "voice_v3:contract_pins_mismatch")
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))["episode"]
    canon = canonical_words(script)
    words = data["words"]
    check([w["text"] for w in words] == [c["text"] for c in canon],
          "voice_v3:text_differs_from_canonical_script")
    prev = 0.0
    for w in words:
        check(0 <= w["start"] < w["end"] <= SPEECH_DURATION
              and w["start"] >= prev - 0.001, "voice_v3:bad_word_time")
        prev = w["end"]
    return [dict(w) for w in words], data["speech_duration_seconds"]


def build(out: Path) -> dict[str, str]:
    words, duration = load()
    cues = make_cues(words, duration)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "e01-v3-johnes-captions.srt": export_srt(cues),
        "e01-v3-johnes-captions.vtt": export_vtt(cues),
        "e01-v3-johnes-karaoke-qa.ass": export_ass(cues, duration),
    }
    digests = {}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
        digests[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    print(json.dumps(build(ap.parse_args().output_dir.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
