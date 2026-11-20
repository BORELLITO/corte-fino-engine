"""Read-only: list Coverr clips (title, ids, orientation, urls) for each scene query from a GitHub runner."""
import json, re, sys, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
cfg = json.load(open(sys.argv[1]))
def walk(o, acc):
    if isinstance(o, dict):
        if "title" in o and ("urls" in o or "mp4" in o or "playback_id" in o or "id" in o) and ("is_vertical" in o or "aspect_ratio" in o or "urls" in o):
            acc.append(o)
        for v in o.values(): walk(v, acc)
    elif isinstance(o, list):
        for v in o: walk(v, acc)
res = {}
for key, qs in cfg["queries"].items():
    res[key] = []
    for q in qs:
        u = "https://coverr.co/s?q=" + urllib.parse.quote(q)
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode("utf8", "ignore")
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', b, re.S)
            acc = []
            if m: walk(json.loads(m[1]), acc)
            seen, items = set(), []
            for o in acc:
                k = o.get("id") or o.get("title")
                if k in seen: continue
                seen.add(k)
                urls = o.get("urls") or {}
                items.append({"id": o.get("id"), "title": o.get("title"), "vertical": o.get("is_vertical"), "ar": o.get("aspect_ratio"), "dur": o.get("duration"), "slug": o.get("slug") or o.get("url"), "mp4": (urls.get("mp4") or urls.get("mp4_download") or urls.get("mp4_preview"))})
            res[key].append({"q": q, "has_next": bool(m), "n": len(items), "items": items[:30], "sample_keys": sorted(acc[0].keys())[:30] if acc else None})
        except Exception as e:
            res[key].append({"q": q, "error": repr(e)[:100]})
s = json.dumps(res, ensure_ascii=False)
print("VNC_CV_BEGIN")
for i in range(0, len(s), 1800): print("VNC_CV", i // 1800, s[i:i + 1800])
print("VNC_CV_END", len(s))
