"""Measure the Johnes Bittar candidate audio (hash, duration, silences, loudness).

Runs only on a GitHub runner where the signed CDN link is reachable. Prints a
single JSON report to stdout between markers; nothing is uploaded, spent or
published. The audio file itself is never committed.
"""
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

START, END = "VNC_AUDIO_PROBE_JSON_BEGIN", "VNC_AUDIO_PROBE_JSON_END"


def parse_duration(stderr: str) -> float:
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    if not m:
        raise ValueError("duration_not_found")
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


def parse_silences(stderr: str) -> list[dict]:
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?\d+\.?\d*)", stderr)]
    ends = re.findall(r"silence_end:\s*(-?\d+\.?\d*)\s*\|\s*silence_duration:\s*(\d+\.?\d*)", stderr)
    out = []
    for i, s in enumerate(starts):
        e = float(ends[i][0]) if i < len(ends) else None
        out.append({"start": round(max(0.0, s), 3),
                    "end": None if e is None else round(e, 3)})
    return out


def parse_loudness(stderr: str) -> dict:
    tail = stderr[stderr.rfind("Summary:"):] if "Summary:" in stderr else ""
    pick = lambda pat: (float(m[1]) if (m := re.search(pat, tail)) else None)
    return {"integrated_lufs": pick(r"I:\s+(-?\d+\.?\d*) LUFS"),
            "true_peak_dbfs": pick(r"Peak:\s+(-?\d+\.?\d*) dBFS"),
            "loudness_range_lu": pick(r"LRA:\s+(-?\d+\.?\d*) LU")}


def run_ffmpeg(exe: str, path: str, filt: str | None) -> str:
    cmd = [exe, "-hide_banner", "-nostats", "-i", path]
    cmd += ["-af", filt] if filt else []
    cmd += ["-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300).stderr


def main() -> int:
    import imageio_ffmpeg
    url = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    dest = "/tmp/e01_v3_johnes.mp3"
    req = urllib.request.Request(url, headers={"User-Agent": "vnc-audio-probe"})
    data = urllib.request.urlopen(req, timeout=120).read()
    Path(dest).write_bytes(data)
    report = {
        "file_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "duration_seconds": round(parse_duration(run_ffmpeg(exe, dest, None)), 3),
        "silences_-38db_min0.12s": parse_silences(
            run_ffmpeg(exe, dest, "silencedetect=noise=-38dB:d=0.12")),
        "loudness": parse_loudness(run_ffmpeg(exe, dest, "ebur128=peak=true")),
    }
    print(START); print(json.dumps(report, ensure_ascii=False)); print(END)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
