"""Real-runtime smoke: Kokoro-82M voice + faster-whisper alignment on ONE original sentence.

No footage, no publication, no secrets. Proves the two heavy engines work on the runner.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .captions import FasterWhisperAligner, build_cues, verify_cues
from .common import ProducerError, audio_integrity_ok, duration_sec, sha256_file
from .voice import KokoroVoice

TEXT = "Tem dias em que a oração parece bater no teto. Mesmo assim, eu continuo de pé."


def main() -> int:
    report: dict = {"text": TEXT, "status": "BLOCKED"}
    try:
        wav = Path(tempfile.mkdtemp()) / "smoke.wav"
        KokoroVoice().synthesize(TEXT, wav)
        dur = duration_sec(wav)
        report.update(voice_ok=True, duration_sec=round(dur, 2), audio_integrity=audio_integrity_ok(wav),
                      wav_sha256=sha256_file(wav))
        words = TEXT.split()
        times = FasterWhisperAligner().align(wav, words)
        cues = build_cues([(TEXT, 0.0, dur)], times)
        errors = verify_cues(cues, [(TEXT, 0.0, dur)])
        report.update(cues=len(cues), cue_errors=errors,
                      first_cue=[round(cues[0].start, 2), round(cues[0].end, 2)])
        if report["audio_integrity"] and not errors and 2.0 < dur < 20.0:
            report["status"] = "PASS"
    except (ProducerError, OSError) as exc:
        report["error"] = str(exc)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
