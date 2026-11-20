"""Read-only scrape of free stock listing pages from a GitHub runner: titles, ids, links and preview mp4
URLs for each scene theme. No downloads of footage, no commit, no spend, no publish."""
import json, re, sys, urllib.request, html as H

cfg = json.load(open(sys.argv[1]))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) vnc-stock-scan"}
res = {}
for key, urls in cfg["queries"].items():
    res[key] = []
    for u in urls:
        try:
            body = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode("utf8", "ignore")
        except Exception as e:
            res[key].append({"url": u, "error": repr(e)[:120]}); continue
        items = {}
        for m in re.finditer(r'href="(/free-stock-video/([a-z0-9-]+-(\d+))/)"', body):
            items.setdefault(m[3], {"id": m[3], "link": "https://mixkit.co" + m[1], "slug": m[2]})
        for m in re.finditer(r'(https://assets\.mixkit\.co/[^"\'\s]+?\.mp4)', body):
            pass
        mp4 = sorted(set(re.findall(r'https://assets\.mixkit\.co/[^"\'\s<>]+?\.mp4', body)))
        for i, v in enumerate(mp4):
            idm = re.search(r'/(\d+)/', v)
            if idm and idm[1] in items:
                items[idm[1]]["preview"] = v
        res[key].append({"url": u, "n": len(items), "items": list(items.values())[:40], "mp4_found": len(mp4)})
print("VNC_SCRAPE_BEGIN")
s = json.dumps(res, ensure_ascii=False)
for i in range(0, len(s), 1800):
    print("VNC_SCRAPE", i // 1800, s[i:i + 1800])
print("VNC_SCRAPE_END", len(s))
