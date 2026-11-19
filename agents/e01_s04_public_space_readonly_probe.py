"""VNC E01 S04: read-only Space /config probe, no GPU, no uploads, no tokens.

Never submits a queue event. Checks 5.82s symbolically historical shot eligibility,
then requires separate license and visual QA before any generation.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCENE_ID = "VNC-E01V2-S04"
REQUIRED_DURATION_S = 5.82
CANONICAL_FRAME_RATE = 30
PUBLIC_SPACES = (
    ("Lightricks/LTX-2.5", "https://lightricks-ltx-2-5.hf.space/config"),
    ("Fhwang/wan2-video-generation", "https://fhwang-wan2-video-generation.hf.space/config"),
    ("truetraitor/wan2-video-generation", "https://truetraitor-wan2-video-generation.hf.space/config"),
)


def summarize_config(space_name: str, config: dict) -> dict:
    """Summarize public Gradio metadata. Nothing here certifies render capability."""
    comps = config.get("components") or []
    by_id = {c.get("id"): c for c in comps if isinstance(c, dict)}
    duration_controls = []
    frame_controls = []
    for c in comps:
        if not isinstance(c, dict):
            continue
        props = c.get("props") or {}
        if not isinstance(props, dict):
            continue
        label = str(props.get("label") or "")
        maximum = props.get("maximum", props.get("max"))
        minimum = props.get("minimum", props.get("min"))
        if "duration" in label.lower() or "seconds" in label.lower():
            duration_controls.append({
                "label": label,
                "min": minimum,
                "max": maximum,
                "covers_s04_duration": type(maximum) in (int, float) and maximum >= REQUIRED_DURATION_S,
            })
        if "frame" in label.lower() and type(maximum) in (int, float):
            frame_controls.append({
                "label": label,
                "min": minimum,
                "max": maximum,
                "can_hold_5_82_seconds_at_24fps": maximum >= 141,
                "fps_unverified": True,
            })
    endpoints = []
    for dep in config.get("dependencies") or []:
        if not isinstance(dep, dict):
            continue
        api_name = dep.get("api_name")
        if not isinstance(api_name, str):
            continue
        inputs = []
        for index in dep.get("inputs") or []:
            component = by_id.get(index) or {}
            props = component.get("props") or {}
            inputs.append({
                "label": str(props.get("label") or ""),
                "component_type": str(component.get("type") or ""),
            })
        endpoints.append({"name": api_name, "inputs": inputs})
    appears_generation = any(
        any(token in e["name"].lower() for token in ("generate", "run", "video"))
        for e in endpoints
    )
    covers_s04 = any(c["covers_s04_duration"] for c in duration_controls)
    frame_capacity_possible = any(c["can_hold_5_82_seconds_at_24fps"] for c in frame_controls)
    return {
        "space": space_name,
        "probe_status": "CONFIG_READ_OK",
        "visible_duration_controls": duration_controls,
        "visible_frame_controls": frame_controls,
        "api_endpoints": endpoints[:25],
        "possible_video_generation_endpoint": appears_generation,
        "s04_5_82_seconds_in_visible_slider": covers_s04,
        "s04_possible_by_frame_control": frame_capacity_possible,
        "video_generation_compatible": "UNKNOWN_REQUIRES_EXACT_ENDPOINT_ROLE_DURATION_LICENSE_QA",
        "source_video_generated": False,
        "video_duration_verified": False,
        "cost_authorized": False,
    }


def inspect_space(space_name: str, config_url: str) -> dict:
    record = {"space": space_name, "config_url": config_url,
              "probe_status": "BLOCKED_UNVERIFIED"}
    try:
        req = Request(config_url, headers={
            "User-Agent": "VNC-E01-S04-ReadOnly-Technical-Preflight/1.0",
            "Accept": "application/json",
        }, method="GET")
        with urlopen(req, timeout=12) as response:
            final_url = response.geturl()
            if not final_url.startswith("https://") or ".hf.space/" not in final_url:
                raise ValueError("redirect_outside_hf_space")
            if int(response.headers.get("content-length") or 0) > 2_000_000:
                raise ValueError("oversized_gradio_config")
            body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("oversized_gradio_config")
        cfg = json.loads(body)
        if not isinstance(cfg, dict) or not isinstance(cfg.get("components"), list):
            raise ValueError("not_gradio_config")
        record = summarize_config(space_name, cfg)
        record["config_url"] = config_url
        record["http_status"] = 200
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
        record["probe_status"] = "BLOCKED_CONFIG_UNAVAILABLE"
        record["failure"] = type(exc).__name__
    return record


def audit(output: Path) -> dict:
    report = {
        "schema_version": "1.0.0",
        "project_id": "VERBO_NO_CHAO_EXCLUSIVO",
        "episode_id": "VNC-W01-E1",
        "scene_id": SCENE_ID,
        "required_scene_duration_seconds": REQUIRED_DURATION_S,
        "source_storyboard": "contracts/e01_v2_12_scene_visual_plan_v1.json",
        "assessment": "PUBLIC_ENDPOINT_READ_ONLY_NOT_LICENSE_OR_GENERATION",
        "paid_requests": 0,
        "video_generation_requests": 0,
        "public_media_uploaded": False,
        "private_media_shared": False,
        "allowed_in_master": False,
        "publication_authorized": False,
        "candidates": [inspect_space(name, url) for name,url in PUBLIC_SPACES],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    dst = Path("artifacts/vnc_s04_space_readonly/S04_SPACE_API_PREFLIGHT.json")
    result = audit(dst)
    for candidate in result["candidates"]:
        print(json.dumps({"space":candidate["space"], "status":candidate["probe_status"],
                          "s04_duration_slider":candidate.get("s04_5_82_seconds_in_visible_slider"),
                          "s04_frame_capacity":candidate.get("s04_possible_by_frame_control"),
                          "has_api":candidate.get("possible_video_generation_endpoint")}))
    print("ZERO GPU CALLS. ZERO SECRET/IMAGE UPLOADS. ZERO RIGHTS/MASTER AUTHORIZATION.")
