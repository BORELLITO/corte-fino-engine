"""Read-only browser probe of Kokoro Web runtime asset identity.

No generation, login, upload, API key, output playback, download saving, or
publication. A real Chrome page records *only* public resource metadata.
An upstream SHA256 is not proof about the hosted browser's loaded bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from agents.content_production import ProductionError, check

SITE = "https://kokoroweb.app/#demoContainer"
HOST = "kokoroweb.app"
VOICE_ONNX_SHA = "0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a"
VOICE_PT_SHA = "cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526"
MAX_VOICE_BYTES = 1000000
ALLOWED_VOICE_HOSTS = frozenset({
    "huggingface.co", "cdn-lfs.hf.co", "cdn-lfs-us-1.hf.co", "kokoroweb.app",
    "www.kokoroweb.app", "hf.co", "xethub.hf.co",
})


def safe_resource(url: str, resource_type: str) -> dict[str, str] | None:
    """Record only hostname and truncated pathname, never query, fragments or tokens."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    if len(host) > 120:
        return None
    return {
        "host": host,
        "path": re.sub(r"[^\w./%+\-]", "_", parsed.path)[:180],
        "resource_type": (resource_type or "unknown")[:24],
    }


def is_exact_voice_response(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").lower() in ALLOWED_VOICE_HOSTS
        and parsed.path.rsplit("/", 1)[-1] in {"pm_alex.bin", "pm_alex.pt"}
    )


def verify_voice_payload(url: str, body: bytes) -> dict[str, Any]:
    check(is_exact_voice_response(url), "hosted_probe:voice_response_not_pinned")
    check(isinstance(body, bytes) and 450000 <= len(body) <= MAX_VOICE_BYTES,
          "hosted_probe:voice_payload_size_invalid")
    filename = urlsplit(url).path.rsplit("/", 1)[-1]
    digest = hashlib.sha256(body).hexdigest()
    upstream = VOICE_ONNX_SHA if filename.endswith(".bin") else VOICE_PT_SHA
    return {
        "voice_filename": filename,
        "sha256": digest,
        "bytes": len(body),
        "matches_known_upstream_sha256": digest == upstream,
        "upstream_sha256_expected": upstream,
        "source": safe_resource(url, "voice_bin"),
    }


def evaluate_probe(report: dict[str, Any]) -> dict[str, Any]:
    """Pure, fail-closed assessment; no resource observation can grant commercial use."""
    matches = report.get("voice_payload_observations")
    check(isinstance(matches, list), "hosted_probe:observations_missing")
    valid = [
        record for record in matches
        if isinstance(record, dict)
        and record.get("voice_filename") in {"pm_alex.bin", "pm_alex.pt"}
        and isinstance(record.get("sha256"), str)
        and record.get("sha256") in {VOICE_ONNX_SHA, VOICE_PT_SHA}
        and record.get("matches_known_upstream_sha256") is True
        and isinstance(record.get("bytes"), int)
        and 450000 <= record["bytes"] <= MAX_VOICE_BYTES
    ]
    report["hosted_voice_response_sha256_matched"] = bool(valid)
    report["status"] = (
        "OBSERVED_VOICE_NETWORK_BYTES_MATCH_UPSTREAM_HOSTED_IDENTITY_UNCONFIRMED"
        if valid else "BLOCKED_NO_MATCHED_HOSTED_VOICE_RESPONSE"
    )
    report["hosted_site_runtime_confirmed"] = False
    report["hosted_voice_pack_bytes_verified"] = False
    report["rights_approved"] = False
    report["license_cleared"] = False
    report["script_approved"] = False
    report["audio_generated"] = False
    report["publication_authorized"] = False
    report["blockers"] = [
        "hosted_runtime_effective_voice_asset_not_proven",
        "browser_cache_or_service_worker_identity_not_proven",
        "runtime_dependency_rights_not_audited",
        "independent_biblical_review_and_owner_approval_pending",
    ]
    if not valid:
        report["blockers"].insert(0, "no_verified_pm_alex_voice_bytes_in_observed_network")
    return report


def audit_browser() -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "audit_id": "VNC-HOSTED-KOKORO-RUNTIME-001",
        "site": "https://kokoroweb.app/",
        "requested_url": SITE,
        "mode": "REAL_BROWSER_PASSIVE_PUBLIC_SITE_READ_ONLY",
        "browser": "Chrome via Playwright in GitHub runner",
        "visit_succeeded": False,
        "url_after_visit": None,
        "page_title": None,
        "languages_seen": [],
        "voice_choices_seen": [],
        "selected_portuguese": False,
        "selected_alex": False,
        "generate_clicked": False,
        "model_download_started_intentionally": False,
        "tts_run": False,
        "voice_payload_observations": [],
        "resource_observations": [],
        "errors": [],
    }
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True,
                                         args=["--disable-dev-shm-usage", "--no-sandbox"])
            try:
                ctx = browser.new_context(accept_downloads=False, service_workers="allow",
                                          java_script_enabled=True)
                page = ctx.new_page()

                def record_response(response: Any) -> None:
                    metadata = safe_resource(response.url, response.request.resource_type)
                    if metadata and len(result["resource_observations"]) < 80:
                        # Only public pathname/host and resource type. Never log query or contents.
                        result["resource_observations"].append(metadata)
                    if not is_exact_voice_response(response.url):
                        return
                    try:
                        length_text = response.headers.get("content-length")
                        if length_text and int(length_text) > MAX_VOICE_BYTES:
                            return
                        body = response.body()
                        if len(body) <= MAX_VOICE_BYTES:
                            v = verify_voice_payload(response.url, body)
                            result["voice_payload_observations"].append(v)
                    except Exception as exc:
                        # Do not log URL/query or response bytes.
                        result["errors"].append("voice_response_capture:" + type(exc).__name__)

                page.on("response", record_response)
                page.goto(SITE, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2500)
                result["visit_succeeded"] = page.url.startswith("https://kokoroweb.app/")
                result["url_after_visit"] = "https://kokoroweb.app/" if result["visit_succeeded"] else None
                result["page_title"] = (page.title() or "")[:140]

                def capture_selects() -> list[dict[str, Any]]:
                    return page.eval_on_selector_all("select", """xs => xs.map((s,i)=>({
                      index:i, options:[...s.options].map(o=>({label:o.label.slice(0,60),
                      value:o.value.slice(0,60)})), selected:s.value.slice(0,60)
                    }))""")
                selects = capture_selects()
                result["languages_seen"] = sorted(set(
                    opt["label"] for sel in selects for opt in sel["options"]
                    if any(t in (opt["label"] + opt["value"]).lower()
                           for t in ("portugu", "brazil", "pt-br", "pt_"))
                ))[:10]

                # Only change dropdown selection on this public page; never press Generate.
                for sel in selects:
                    options = sel["options"]
                    choice = next((o for o in options
                                   if any(x in (o["label"] + " " + o["value"]).lower()
                                          for x in ("portugu", "brazil", "pt-br", "pt_"))), None)
                    if choice:
                        page.locator("select").nth(sel["index"]).select_option(value=choice["value"])
                        result["selected_portuguese"] = True
                        break
                if result["selected_portuguese"]:
                    page.wait_for_timeout(3500)
                choices = capture_selects()
                result["voice_choices_seen"] = sorted(set(
                    o["label"][:60] for sel in choices for o in sel["options"]
                    if "alex" in (o["label"] + o["value"]).lower()
                ))[:10]
                for sel in choices:
                    voice = next((o for o in sel["options"]
                                  if "alex" in (o["label"] + o["value"]).lower()), None)
                    if voice:
                        page.locator("select").nth(sel["index"]).select_option(value=voice["value"])
                        result["selected_alex"] = True
                        page.wait_for_timeout(5000)
                        break
                ctx.close()
            finally:
                browser.close()
    except Exception as exc:
        # No uncontrolled external error text, stack trace, cookies or network URLs.
        result["errors"].append("browser_probe:" + type(exc).__name__)
    return evaluate_probe(result)


def validate_report(payload: Any) -> None:
    check(isinstance(payload, dict)
          and payload.get("project") == "verbo-no-chao"
          and payload.get("audit_id") == "VNC-HOSTED-KOKORO-RUNTIME-001"
          and payload.get("requested_url") == SITE
          and payload.get("mode") == "REAL_BROWSER_PASSIVE_PUBLIC_SITE_READ_ONLY",
          "hosted_probe:wrong_report_identity")
    check(payload.get("generate_clicked") is False
          and payload.get("model_download_started_intentionally") is False
          and payload.get("tts_run") is False
          and payload.get("hosted_site_runtime_confirmed") is False
          and payload.get("hosted_voice_pack_bytes_verified") is False
          and payload.get("rights_approved") is False
          and payload.get("license_cleared") is False
          and payload.get("script_approved") is False
          and payload.get("audio_generated") is False
          and payload.get("publication_authorized") is False,
          "hosted_probe:unsafe_or_unproven_claim")
    check(payload.get("status") in {
        "BLOCKED_NO_MATCHED_HOSTED_VOICE_RESPONSE",
        "OBSERVED_VOICE_NETWORK_BYTES_MATCH_UPSTREAM_HOSTED_IDENTITY_UNCONFIRMED",
    }, "hosted_probe:status")
    check(isinstance(payload.get("blockers"), list) and
          "hosted_runtime_effective_voice_asset_not_proven" in payload["blockers"],
          "hosted_probe:required_blocker_missing")
    check(isinstance(payload.get("voice_payload_observations"), list)
          and isinstance(payload.get("resource_observations"), list)
          and len(payload["resource_observations"]) <= 80,
          "hosted_probe:malformed_resources")
    for record in payload["resource_observations"]:
        check(isinstance(record, dict) and all(k in record for k in ("host", "path", "resource_type"))
              and not any(token in record["path"] for token in ("?", "#", "@")),
              "hosted_probe:unsafe_resource_path")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Kokoro Web without generating audio")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = audit_browser()
    validate_report(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": data["status"],
        "visit_succeeded": data["visit_succeeded"],
        "selected_portuguese": data["selected_portuguese"],
        "selected_alex": data["selected_alex"],
        "matched_voice_response": data["hosted_voice_response_sha256_matched"],
        "rights_approved": False,
        "audio_generated": False,
        "errors": data["errors"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
