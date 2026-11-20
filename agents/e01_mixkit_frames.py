"""Read-only: for each shortlisted free Mixkit clip, fetch its detail page, download the preview mp4 on the
runner, probe it, sample 5 frames and print a contact sheet (base64 JPEG) in chunks. Also scans extra
listing queries. Nothing is committed, uploaded, spent or published."""
import base64, io, json, re, subprocess, sys, time, urllib.request
import imageio_ffmpeg
import numpy as np
from PIL import Image

FF = imageio_ffmpeg.get_ffmpeg_exe()
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) vnc-mixkit-review"}
cfg = json.load(open(sys.argv[1]))


def get(u, binary=False, tries=4):
    for k in range(tries):
        try:
            d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
            return d if binary else d.decode("utf8", "ignore")
        except Exception as e:
            if "429" in repr(e): time.sleep(6 * (k + 1)); continue
            raise
    raise RuntimeError("429")


def probe(p):
    err = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    d = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", err)
    v = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", err)
    return {"seconds": round(int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]), 2) if d else None,
            "w": int(v[1]) if v else None, "h": int(v[2]) if v else None, "audio": "Audio:" in err}


def frames(p, secs):
    out = []
    for i in range(5):
        t = secs * (i + 0.5) / 5
        png = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        out.append(Image.open(io.BytesIO(png)).convert("RGB"))
    return out


res = []
print("VNC_MK_BEGIN")
for c in cfg["clips"]:
    r = {"scene": c["scene"], "id": c["id"], "link": c["link"]}
    try:
        page = get(c["link"])
        mp4 = sorted(set(re.findall(r'https://assets\.mixkit\.co/[^"\'\s<>]+?\.mp4', page)))
        if not mp4:
            mp4 = sorted(set(re.findall(r'https://assets\.mixkit\.co/[a-z0-9]{20,}', page)))
        r["mp4_variants"] = [m.split("/")[-1] for m in mp4]
        lic = re.search(r"(Mixkit[^<]{0,60}License)", page)
        r["license_text"] = lic[1] if lic else None
        dur = re.search(r"Duration</?[^>]*>\s*([0-9:]+)", page)
        r["page_duration"] = dur[1] if dur else None
        pick = next((m for m in mp4 if "-360" in m), mp4[0] if mp4 else None)
        if not pick: raise RuntimeError("no video url on page")
        r["video_url"] = pick
        data = get(pick, binary=True)
        open("/tmp/c.mp4", "wb").write(data)
        r.update(probe("/tmp/c.mp4"))
        fs = frames("/tmp/c.mp4", r["seconds"] or 5)
        arr = [np.asarray(f.resize((90, 160)).convert("L"), dtype=float) for f in fs]
        r["motion"] = round(float(np.mean([np.abs(arr[i + 1] - arr[i]).mean() for i in range(4)])), 2)
        r["luma"] = round(float(np.mean(arr)), 1)
        sheet = Image.new("RGB", (5 * 126, 224))
        for i, f in enumerate(fs): sheet.paste(f.resize((126, 224)), (i * 126, 0))
        b = io.BytesIO(); sheet.save(b, "JPEG", quality=70)
        s = base64.b64encode(b.getvalue()).decode()
        print("VNC_MK_IMG", c["scene"], c["id"], len(s))
        for n in range(0, len(s), 1800): print("VNC_MK_B64", c["id"], n // 1800, s[n:n + 1800])
    except Exception as e:
        r["error"] = repr(e)[:200]
    res.append(r)
    time.sleep(2)
extra = {}
for key, tags in cfg.get("retry_queries", {}).items():
    extra[key] = []
    for t in tags:
        u = f"https://mixkit.co/free-stock-video/discover/{t}/?orientation=vertical"
        try:
            body = get(u)
            items = {}
            for m in re.finditer(r'href="/free-stock-video/([a-z0-9-]+-(\d+))/"', body): items.setdefault(m[2], m[1])
            extra[key].append({"tag": t, "items": list(items.values())[:24]})
        except Exception as e:
            extra[key].append({"tag": t, "error": repr(e)[:80]})
        time.sleep(3)
s = json.dumps({"clips": res, "extra": extra}, ensure_ascii=False)
for n in range(0, len(s), 1800): print("VNC_MK_JSON", n // 1800, s[n:n + 1800])
print("VNC_MK_END")
