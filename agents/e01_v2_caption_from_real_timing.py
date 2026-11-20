"""Build v3-layout SRT/VTT/ASS karaoke from the pinned real word timing.

Offline and deterministic: reads contracts/e01_v2_caption_word_timing_real_v1.json
only. No audio, ASR, network or paid service is used.
"""
import argparse
import hashlib
import json
from pathlib import Path

from agents.e01_v2_caption_pipeline import (
    ASR_BYTES, ASR_SHA, SCRIPT_SHA, VOICE_DURATION, WAV_SHA,
    export_ass, export_srt, export_vtt, make_cues,
)
from agents.content_production import check

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/e01_v2_caption_word_timing_real_v1.json"


def load_words(path: Path = CONTRACT) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    p = data["provenance"]
    check(p["script_sha256"] == SCRIPT_SHA and p["wav_sha256"] == WAV_SHA
          and p["asr_report_sha256"] == ASR_SHA and p["asr_report_bytes"] == ASR_BYTES
          and data["speech_duration_seconds"] == VOICE_DURATION
          and len(data["words"]) == 182, "timing:contract_pins_mismatch")
    return [dict(w) for w in data["words"]]


def build(out: Path) -> dict[str, str]:
    cues = make_cues(load_words())
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "e01-v2-captions-v3.srt": export_srt(cues),
        "e01-v2-captions-v3.vtt": export_vtt(cues),
        "e01-v2-karaoke-v3-qa.ass": export_ass(cues),
    }
    digests = {}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
        digests[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(build(args.output_dir.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
