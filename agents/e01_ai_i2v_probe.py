"""Read-only probe: download the AI reference frames on the runner, verify them, and list the API of
each candidate free Hugging Face Space (anonymous). No generation, no spend, no publish."""
import hashlib, json, struct, sys, urllib.request
from pathlib import Path

cfg = json.load(open(sys.argv[1]))
out = {"images": {}, "spaces": {}}
Path("/tmp/refs").mkdir(exist_ok=True)
for k, u in cfg["images"].items():
    try:
        d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "vnc-probe"}), timeout=60).read()
        w, h = struct.unpack(">II", d[16:24]) if d[:8] == b"\x89PNG\r\n\x1a\n" else (None, None)
        Path(f"/tmp/refs/{k}.png").write_bytes(d)
        out["images"][k] = {"bytes": len(d), "w": w, "h": h, "sha256": hashlib.sha256(d).hexdigest()}
    except Exception as e:
        out["images"][k] = {"error": repr(e)[:200]}
from gradio_client import Client
for s in cfg["spaces"]:
    try:
        c = Client(s, verbose=False)
        api = c.view_api(return_format="dict")
        out["spaces"][s] = {"ok": True, "endpoints": {n: [p["parameter_name"] for p in e["parameters"]] for n, e in api["named_endpoints"].items()}}
    except Exception as e:
        out["spaces"][s] = {"ok": False, "error": repr(e)[:300]}
print("VNC_I2V_PROBE_BEGIN")
print(json.dumps(out, ensure_ascii=False))
print("VNC_I2V_PROBE_END")
