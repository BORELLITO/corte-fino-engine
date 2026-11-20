"""Read-only: per scene, list free (non-premium, non-AI) Coverr clips from search, download the 360p preview on the
runner, probe it, take 3 frames and print one contact sheet per scene (base64 JPEG chunks). Nothing is committed."""
import base64, io, json, re, subprocess, sys, urllib.parse, urllib.request
import imageio_ffmpeg, numpy as np
from PIL import Image, ImageDraw
FF = imageio_ffmpeg.get_ffmpeg_exe()
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
cfg = json.load(open(sys.argv[1]))
def get(u, binary=False):
    d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
    return d if binary else d.decode("utf8", "ignore")
def probe(p):
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    d = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", e); v = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", e)
    return (round(int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]), 1) if d else None, int(v[1]) if v else 0, int(v[2]) if v else 0)
def frame(p, t):
    png = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")
out = {}
print("VNC_CVS_BEGIN")
for scene, qs in cfg["queries"].items():
    slugs = []
    for q in qs:
        try:
            b = get("https://coverr.co/s?q=" + urllib.parse.quote(q))
        except Exception: continue
        for s in re.findall(r"https://cdn\.coverr\.co/videos/(coverr-[a-z0-9-]+)/360p\.mp4", b):
            if s.startswith("coverr-premium-") or s in slugs: continue
            slugs.append(s)
    slugs = slugs[:cfg.get("per_scene", 10)]
    tiles, meta = [], []
    for s in slugs:
        try:
            open("/tmp/c.mp4", "wb").write(get(f"https://cdn.coverr.co/videos/{s}/360p.mp4", True))
            dur, w, h = probe("/tmp/c.mp4")
            fr = [frame("/tmp/c.mp4", (dur or 4) * x) for x in (0.2, 0.5, 0.8)]
            a = [np.asarray(f.resize((64, 64)).convert("L"), dtype=float) for f in fr]
            mot = round(float(np.mean([abs(a[0] - a[1]).mean(), abs(a[1] - a[2]).mean()])), 1)
            meta.append({"slug": s, "dur": dur, "w": w, "h": h, "motion": mot}); tiles.append((s, fr[1], dur, w, h, mot))
        except Exception as e:
            meta.append({"slug": s, "error": repr(e)[:80]})
    cols = 5; tw, th = 180, 200; rows = max(1, (len(tiles) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
    for i, (s, f, dur, w, h, mot) in enumerate(tiles):
        f.thumbnail((tw, 160)); x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(f, (x, y)); dr.text((x + 2, y + 162), f"{i+1} {w}x{h} {dur}s m{mot}", fill=(255, 255, 0)); dr.text((x + 2, y + 175), s[7:30], fill=(200, 200, 200))
    bb = io.BytesIO(); sheet.save(bb, "JPEG", quality=72); sb = base64.b64encode(bb.getvalue()).decode()
    print("VNC_CVS_IMG", scene, len(sb))
    for n in range(0, len(sb), 1800): print("VNC_CVS_B64", scene, n // 1800, sb[n:n + 1800])
    out[scene] = meta
s = json.dumps(out, ensure_ascii=False)
for n in range(0, len(s), 1800): print("VNC_CVS_JSON", n // 1800, s[n:n + 1800])
print("VNC_CVS_END")
