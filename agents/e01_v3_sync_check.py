"""Independent sync check: Whisper (no reference text) vs pinned word timing and the .ass.

Runs on a GitHub runner only. Prints JSON between markers. No upload, spend or publish.
"""
import difflib, json, re, statistics, subprocess, sys, unicodedata, urllib.request
from pathlib import Path

EXPECTED_SHA = "35f435199df54f6380d80d129ddd95b04ddb0ff5f97ede97a74da856995b5685"
START, END = "VNC_SYNC_JSON_BEGIN", "VNC_SYNC_JSON_END"
TIMING = Path("contracts/e01_v3_voice_johnes_word_timing_v1.json")
ASS = Path("contracts/e01_v3_karaoke_under_test.ass")


def norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def ass_t(s):
    h, m, x = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(x)


def ass_active_starts():
    """start time of each event whose text carries the lilac tag, in order."""
    out = []
    for line in ASS.read_text(encoding="utf-8").splitlines():
        if line.startswith("Dialogue:") and "1c&H00F2B0C4&" in line:
            f = line.split(",", 9)
            m = re.search(r"\{\\1c&H00F2B0C4&\}([^{]*)\{", f[9])
            out.append((ass_t(f[1]), ass_t(f[2]), norm(m[1]) if m else ""))
    return out


def main():
    url = Path(sys.argv[1]).read_text().strip()
    wav = Path("/tmp/johnes.mp3")
    wav.write_bytes(urllib.request.urlopen(urllib.request.Request(
        url, headers={"User-Agent": "vnc-sync"}), timeout=120).read())
    import imageio_ffmpeg, numpy as np
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(wav), "-f", "f32le",
                          "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype=np.float32)
    import hashlib
    sha = hashlib.sha256(wav.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA:
        print(START); print(json.dumps({"error": "audio_sha256_mismatch", "got": sha})); print(END); sys.exit(2)
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(samples, language="pt", beam_size=5, temperature=0.0,
                               word_timestamps=True, condition_on_previous_text=False)
    asr = [(norm(w.word), w.start, w.end) for s in segs for w in s.words if norm(w.word)]
    ref = json.loads(TIMING.read_text(encoding="utf-8"))["words"]
    rn = [norm(w["text"]) for w in ref]
    sm = difflib.SequenceMatcher(None, rn, [a[0] for a in asr], autojunk=False)
    pairs = [(i, j) for b in sm.get_matching_blocks() for i, j in zip(range(b.a, b.a + b.size), range(b.b, b.b + b.size))]
    dev = [{"i": i, "word": ref[i]["text"], "ref": ref[i]["start"], "asr": round(asr[j][1], 3),
            "d": round(asr[j][1] - ref[i]["start"], 3)} for i, j in pairs]
    d = [x["d"] for x in dev]
    ass = ass_active_starts()
    ass_dev = [round(ass[i][0] - ref[i]["start"], 3) for i in range(min(len(ass), len(ref)))]
    rep = {
        "ref_words": len(ref), "asr_words": len(asr), "matched": len(pairs),
        "unmatched_ref": [ref[i]["text"] for i in range(len(ref)) if i not in {p[0] for p in pairs}],
        "d_median": round(statistics.median(d), 3), "d_mean": round(statistics.mean(d), 3),
        "d_p95_abs": round(sorted(abs(x) for x in d)[int(.95 * len(d)) - 1], 3),
        "d_max_abs": round(max(abs(x) for x in d), 3),
        "n_abs_gt_0.15": sum(abs(x) > .15 for x in d), "n_abs_gt_0.30": sum(abs(x) > .30 for x in d),
        "worst": sorted(dev, key=lambda x: -abs(x["d"]))[:12],
        "ass_lilac_events": len(ass), "ass_vs_ref_max_abs": max((abs(x) for x in ass_dev), default=None),
        "ass_vs_ref_over_0.05": sum(abs(x) > .05 for x in ass_dev),
        "audio_sha256": sha, "deviations": dev,
        "asr_text": " ".join(a[0] for a in asr),
    }
    print(START); print(json.dumps(rep, ensure_ascii=False, default=float)); print(END)


main()
