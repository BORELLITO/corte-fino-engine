"""Read-only frame review helper: download each shortlisted clip on a GitHub runner, probe it,
extract 5 frames, measure motion and the caption-band activity, and print a small contact sheet
(base64 JPEG) between markers. Nothing is committed, uploaded, spent or published."""
import base64, io, json, re, subprocess, sys, urllib.request
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

START, END = "VNC_CLIP_JSON_BEGIN", "VNC_CLIP_JSON_END"
FF = imageio_ffmpeg.get_ffmpeg_exe()
BAND = (1100, 1360, 140, 940)  # y0, y1, x0, x1 on a 1080x1920 canvas


def run(args):
    return subprocess.run([FF, "-v", "info", *args], capture_output=True, text=True)


def fetch(cid, dest):
    url = f"https://www.pexels.com/download/video/{cid}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 vnc-clip-review"})
    with urllib.request.urlopen(req, timeout=180) as r:
        dest.write_bytes(r.read())
    return url


def probe(p):
    err = run(["-i", str(p)]).stderr
    d = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", err)
    v = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", err)
    f = re.search(r"(\d+(?:\.\d+)?)\s*fps", err)
    return {"seconds": round(int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]), 2) if d else None,
            "w": int(v[1]) if v else None, "h": int(v[2]) if v else None, "fps": float(f[1]) if f else None,
            "audio": "Audio:" in err}


def frame(p, t):
    out = subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", str(p), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(out)).convert("RGB")


def main():
    sl = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["candidates"]
    work = Path("/tmp/clips"); work.mkdir(exist_ok=True)
    for c in sl:
        rep = {"scene": c["scene"], "id": c["id"], "need_s": c["need_s"]}
        try:
            f = work / f"{c['id']}.mp4"
            fetch(c["id"], f)
            rep["bytes"] = f.stat().st_size
            rep.update(probe(f))
            n = 5; secs = rep["seconds"] or 5
            times = [round(secs * (i + .5) / n, 2) for i in range(n)]
            frames = [frame(f, t) for t in times]
            small = [np.asarray(im.convert("L").resize((108, 192)), dtype=np.float32) for im in frames]
            rep["motion_mean_abs_diff"] = round(float(np.mean([np.abs(a - b).mean() for a, b in zip(small, small[1:])])), 2)
            y0, y1, x0, x1 = BAND
            vert = rep["h"] and rep["w"] and rep["h"] > rep["w"]
            if vert:
                g = [np.asarray(im.convert("L").resize((1080, 1920)), dtype=np.float32)[y0:y1, x0:x1] for im in frames]
                rep["band_mean_luma"] = round(float(np.mean([x.mean() for x in g])), 1)
                rep["band_luma_std"] = round(float(np.mean([x.std() for x in g])), 1)
            rep["covers_need"] = bool(rep["seconds"] and rep["seconds"] >= c["need_s"])
            tw, th = 160, 284
            sheet = Image.new("RGB", (tw * n, th))
            for i, im in enumerate(frames):
                im.thumbnail((tw, th)); sheet.paste(im, (i * tw + (tw - im.width) // 2, (th - im.height) // 2))
            buf = io.BytesIO(); sheet.save(buf, "JPEG", quality=50)
            rep["sheet_b64"] = base64.b64encode(buf.getvalue()).decode()
        except Exception as e:  # report, never hide
            rep["error"] = repr(e)[:300]
        b64 = rep.pop("sheet_b64", "")
        print(START); print(json.dumps(rep)); print(END, flush=True)
        for i in range(0, len(b64), 2000):
            print("VNC_CLIP_B64", c["id"], i // 2000, b64[i:i + 2000], flush=True)
        print("VNC_CLIP_B64_DONE", c["id"], len(b64), flush=True)


main()
