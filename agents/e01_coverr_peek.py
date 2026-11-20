import re, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
b = urllib.request.urlopen(urllib.request.Request("https://coverr.co/s?q=praying", headers=UA), timeout=40).read().decode("utf8", "ignore")
print("VNC_PEEK_LEN", len(b), "scripts", re.findall(r'<script[^>]*id="([^"]+)"', b)[:10])
for m in list(re.finditer(r"\.mp4", b))[:2]:
    print("VNC_PEEK_CTX", b[max(0, m.start() - 500): m.end() + 200].replace("\n", " "))
print("VNC_PEEK_HREF", re.findall(r'href="(/(?:stock-video-footage|videos?)/[^"]+)"', b)[:8])
print("VNC_PEEK_ALL_MP4", sorted(set(re.findall(r'https?://[^"\'\s<>\\]+\.mp4', b)))[:6])
