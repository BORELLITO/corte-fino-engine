"""Read-only: can a GitHub runner read search pages of free stock banks? Prints status and signals only."""
import json, re, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0", "Accept-Language": "en"}
urls = {
 "pexels": "https://www.pexels.com/search/videos/woman%20praying%20window/?orientation=portrait",
 "pixabay": "https://pixabay.com/videos/search/praying%20hands/?orientation=vertical",
 "coverr": "https://coverr.co/s?q=prayer&orientation=vertical",
 "coverr_videos": "https://coverr.co/stock-video-footage/prayer",
 "pexels_api_nokey": "https://api.pexels.com/videos/search?query=prayer&orientation=portrait&per_page=3",
}
out = {}
for k, u in urls.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40)
        b = r.read().decode("utf8", "ignore")
        out[k] = {"status": r.status, "len": len(b), "mp4": len(re.findall(r"\.mp4", b)), "video_links": sorted(set(re.findall(r'/(?:video|videos)/[a-z0-9-]*?(\d{5,})', b)))[:8], "cf": "cloudflare" in b.lower()[:3000]}
    except Exception as e:
        out[k] = {"error": repr(e)[:160]}
print("VNC_PROBE", json.dumps(out, ensure_ascii=False))
