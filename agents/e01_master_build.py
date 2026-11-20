"""E01 master preview builder. Runs on a GitHub runner only.

Downloads the 12 selected free clips (Pexels, Mixkit, Coverr), crops each to 9:16 around the motion centroid,
cuts them to the scene timings, burns the approved karaoke captions and muxes the existing Johnes Bittar narration
(downloaded from the already generated take; no new voice, no spend). Output is printed as base64 chunks for the
owner's private copy; nothing is uploaded, committed or published."""
import base64, hashlib, io, json, os, re, subprocess, sys, urllib.request
from pathlib import Path
import imageio_ffmpeg, numpy as np
from PIL import Image

from agents.e01_v3_voice_captions import build as build_captions

FF = imageio_ffmpeg.get_ffmpeg_exe()
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
W, H = 1080, 1920
AUDIO_SHA_PREFIX, AUDIO_SHA_SUFFIX = "35f43519", "b5685"
MAX_BYTES = 150_000_000
WORK = Path("/tmp/master"); WORK.mkdir(exist_ok=True)


def get(url, binary=True, timeout=180):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES: raise RuntimeError("too_large")
    return data if binary else data.decode("utf8", "ignore")


def probe(p):
    e = subprocess.run([FF, "-hide_banner", "-i", str(p)], capture_output=True, text=True).stderr
    d = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", e); v = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", e)
    return {"dur": int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]) if d else 0.0, "w": int(v[1]) if v else 0, "h": int(v[2]) if v else 0}


def fetch_clip(c, dest):
    s, i = c["source"], c["id"]
    if s == "pexels":
        urls = [f"https://www.pexels.com/download/video/{i}/"]
    elif s == "mixkit":
        page = get(c["page"], False)
        urls = sorted(set(re.findall(r'https://assets\.mixkit\.co/[^"\'\s<>]+?\.mp4', page)), key=lambda u: -int(re.search(r"-(\d{3,4})\.mp4", u)[1]) if re.search(r"-(\d{3,4})\.mp4", u) else 0)
    elif s == "coverr":
        urls = [f"https://cdn.coverr.co/videos/{i}/{q}.mp4" for q in ("1080p", "720p", "360p")]
    else:
        raise RuntimeError("unknown_source")
    last = None
    for u in urls:
        try:
            data = get(u)
            if len(data) < 100_000 or b"ftyp" not in data[:64]: raise RuntimeError("not_mp4")
            dest.write_bytes(data)
            return {"url_host": re.match(r"https://([^/]+)/", u)[1], "bytes": len(data)}
        except Exception as e:
            last = repr(e)[:80]
    raise RuntimeError(f"download_failed:{last}")


def motion_center(p, dur):
    frames = []
    for k in range(8):
        t = dur * (k + 0.5) / 8
        png = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-vf", "scale=160:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        if png: frames.append(np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=float))
    if len(frames) < 2: return 0.5
    col = sum(np.abs(frames[k + 1] - frames[k]).sum(axis=0) for k in range(len(frames) - 1))
    col = np.convolve(col, np.ones(9) / 9, mode="same")
    if col.sum() <= 0: return 0.5
    return float((col * np.arange(len(col))).sum() / col.sum() / len(col))


def main():
    audio_link = os.environ.get("VNC_E01_AUDIO_URL", "").strip()
    if not audio_link.startswith("https://elevenlabsusercontent.com/"):
        print("VNC_MASTER_ABORT no_audio_secret"); sys.exit(4)
    sel = json.loads(Path("contracts/e01_v3_scene_clip_selection_v1.json").read_text())["clips"]
    refit = {s["id"][-3:]: s for s in json.loads(Path("contracts/e01_v3_12_scene_refit_v1.json").read_text())["scenes"]}
    report = {"scenes": [], "errors": []}
    audio = get(audio_link); (WORK / "voice.mp3").write_bytes(audio)
    sha = hashlib.sha256(audio).hexdigest(); report["audio_sha256"] = sha
    if not (sha.startswith(AUDIO_SHA_PREFIX) and sha.endswith(AUDIO_SHA_SUFFIX)):
        print("VNC_MASTER_ABORT audio_sha_mismatch", sha); sys.exit(2)
    adur = probe(WORK / "voice.mp3")["dur"]; report["audio_seconds"] = round(adur, 2)
    caps = WORK / "caps"; build_captions(caps)
    segs = []
    for c in sel:
        sc = c["scene"]; sd = refit[sc]["duration_seconds"]; r = {"scene": sc, "source": c["source"], "id": c["id"], "need_s": sd}
        try:
            src = WORK / f"{sc}.src.mp4"; r.update(fetch_clip(c, src)); pr = probe(src); r.update({"src_w": pr["w"], "src_h": pr["h"], "src_s": round(pr["dur"], 2)})
            start = min(max(0.4, pr["dur"] * 0.08), max(0.0, pr["dur"] - sd - 0.2)); r["start"] = round(start, 2)
            if pr["w"] > pr["h"] * 0.6:
                cx = c.get("crop_cx") or motion_center(src, pr["dur"]); cw = int(pr["h"] * 9 / 16) // 2 * 2; x0 = int(min(max(cx * pr["w"] - cw / 2, 0), pr["w"] - cw)); r["crop_cx"] = round(cx, 2)
                vf = f"crop={cw}:{pr['h']}:{x0}:0,scale={W}:{H}:flags=lanczos,setsar=1,fps=30"
            else:
                vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps=30"
            out = WORK / f"{sc}.seg.mp4"
            subprocess.run([FF, "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", str(src), "-t", f"{sd:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)], check=True)
            r["seg_s"] = round(probe(out)["dur"], 2); segs.append(out)
        except Exception as e:
            r["error"] = repr(e)[:160]; report["errors"].append(sc)
        report["scenes"].append(r)
    if report["errors"]:
        print("VNC_MASTER_ABORT scenes_failed", report["errors"]); print("VNC_MASTER_REPORT", json.dumps(report, ensure_ascii=False)); sys.exit(3)
    (WORK / "list.txt").write_text("".join(f"file '{p}'\n" for p in segs))
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"), "-c", "copy", str(WORK / "video.mp4")], check=True)
    final = WORK / "e01_master_preview_720.mp4"
    ass = str(caps / "e01-v3-johnes-karaoke-qa.ass")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(WORK / "video.mp4"), "-i", str(WORK / "voice.mp3"),
        "-vf", f"ass={ass}:original_size={W}x{H}:fontsdir=assets/fonts,scale=720:1280:flags=lanczos",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{adur:.2f}", "-movflags", "+faststart", str(final)], check=True)
    fp = probe(final); report["final"] = {"w": fp["w"], "h": fp["h"], "seconds": round(fp["dur"], 2), "bytes": final.stat().st_size, "sha256": hashlib.sha256(final.read_bytes()).hexdigest()}
    tiles = []
    for sc, s in refit.items():
        t = (s["start_seconds"] + s["end_seconds"]) / 2
        png = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(final), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        tiles.append(Image.open(io.BytesIO(png)).convert("RGB").resize((240, 427)))
    sheet = Image.new("RGB", (6 * 240, 2 * 427))
    for k, im in enumerate(tiles): sheet.paste(im, ((k % 6) * 240, (k // 6) * 427))
    b = io.BytesIO(); sheet.save(b, "JPEG", quality=80); sb = base64.b64encode(b.getvalue()).decode()
    print("VNC_MASTER_SHEET", len(sb))
    for n in range(0, len(sb), 1800): print("VNC_MASTER_SHEETB64", n // 1800, sb[n:n + 1800])
    print("VNC_MASTER_REPORT", json.dumps(report, ensure_ascii=False))
    vb = base64.b64encode(final.read_bytes()).decode(); print("VNC_MASTER_VIDEO", len(vb))
    for n in range(0, len(vb), 1800): print("VNC_MASTER_B64", n // 1800, vb[n:n + 1800])
    print("VNC_MASTER_END")


if __name__ == "__main__":
    main()
