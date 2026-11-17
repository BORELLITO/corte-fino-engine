"""One isolated short Kokoro Web smoke, using only an original test phrase.

Never reuses the project's approved or draft narration. Never downloads WAV,
publishes, logs secrets, saves binary model files or elevates licensing state.
The Chrome session is disposable. A network/cache hash is not proof of which
asset the inference engine consumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.hosted_browser_probe import (
    SITE, VOICE_ONNX_SHA, VOICE_PT_SHA,
    is_exact_voice_response, safe_resource, verify_voice_payload,
)

PHRASE = "Olá. Esta é uma prova técnica de narração. Nenhum conteúdo será publicado."
PHRASE_SHA = hashlib.sha256(PHRASE.encode("utf-8")).hexdigest()
MAX_WALL_SECONDS = 190
EXPECTED_HOST = "https://kokoroweb.app/"
REQUIRED_BLOCKERS = (
    "effective_hosted_voice_asset_not_proven",
    "model_and_dependency_license_notices_pending",
    "human_theological_review_and_owner_script_approval_pending",
    "master_video_not_created_or_approved",
    "publication_not_authorized",
)


def base_report() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "audit_id": "VNC-KOKORO-CONTROLLED-SMOKE-001",
        "site": EXPECTED_HOST,
        "mode": "ISOLATED_SHORT_ORIGINAL_TEST_NOT_PROJECT_NARRATION",
        "phrase_sha256": PHRASE_SHA,
        "phrase_characters": len(PHRASE),
        "browser": "Chrome headless on GitHub Actions",
        "site_visited": False,
        "pt_br_selected": False,
        "pm_alex_selected": False,
        "generate_clicked": False,
        "test_audio_observed": False,
        "test_audio_duration_seconds": None,
        "output_audio_saved": False,
        "model_files_saved": False,
        "production_audio_generated": False,
        "script_read_or_uploaded": False,
        "voice_network_sha_matches": [],
        "voice_cache_sha_matches": [],
        "model_resource_count": 0,
        "model_resource_host_counts": {},
        "html_audio_nodes": 0,
        "browser_errors": [],
        "status": "BLOCKED_NO_TEST_AUDIO_OBSERVED",
        "hosted_runtime_effective_voice_asset_proven": False,
        "rights_approved": False,
        "license_cleared": False,
        "owner_script_approved": False,
        "publication_authorized": False,
        "blockers": list(REQUIRED_BLOCKERS),
    }


def choose_options(selects: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Extract language and voice from a list of live select properties."""
    check(isinstance(selects, list), "smoke:selects_not_list")
    lang = None
    voice = None
    for sel in selects:
        if not isinstance(sel, dict) or not isinstance(sel.get("options"), list):
            continue
        for option in sel["options"]:
            if not isinstance(option, dict):
                continue
            label = str(option.get("label", ""))
            value = str(option.get("value", ""))
            lower = f"{label} {value}".lower()
            if lang is None and any(t in lower for t in
                                    ("portugu", "brazil", "pt-br", "pt_")):
                lang = {"index": sel.get("index"), "value": value}
            if voice is None and ("pm_alex" in lower or "alex" in lower):
                voice = {"index": sel.get("index"), "value": value}
    return lang, voice


def canonical_audio_nodes(nodes: Any) -> tuple[bool, float | None]:
    """Only a real populated audio element counts as a tentative smoke signal."""
    if not isinstance(nodes, list):
        return False, None
    for n in nodes:
        if not isinstance(n, dict):
            continue
        duration = n.get("duration")
        if (n.get("ready_state", 0) >= 1
                and isinstance(duration, (int, float))
                and 0.15 <= duration <= 40
                and n.get("source_kind") in ("blob", "data", "media")):
            return True, round(float(duration), 3)
    return False, None


def assess(report: dict[str, Any]) -> dict[str, Any]:
    check(report.get("audit_id") == "VNC-KOKORO-CONTROLLED-SMOKE-001",
          "smoke:wrong_identity")
    obs = report.get("test_audio_observed") is True
    report["status"] = (
        "TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED"
        if obs else "BLOCKED_NO_TEST_AUDIO_OBSERVED"
    )
    report["production_audio_generated"] = False
    report["output_audio_saved"] = False
    report["model_files_saved"] = False
    report["script_read_or_uploaded"] = False
    report["hosted_runtime_effective_voice_asset_proven"] = False
    report["rights_approved"] = False
    report["license_cleared"] = False
    report["owner_script_approved"] = False
    report["publication_authorized"] = False
    report["blockers"] = list(REQUIRED_BLOCKERS)
    if not report.get("voice_network_sha_matches") and not report.get("voice_cache_sha_matches"):
        report["blockers"].insert(0, "hosted_voice_bytes_not_observed_or_hashed")
    if not obs:
        report["blockers"].insert(0, "smoke_test_audio_not_confirmed")
    return report


def validate_report(v: Any) -> None:
    check(isinstance(v, dict)
          and v.get("project") == "verbo-no-chao"
          and v.get("audit_id") == "VNC-KOKORO-CONTROLLED-SMOKE-001"
          and v.get("site") == EXPECTED_HOST
          and v.get("mode") == "ISOLATED_SHORT_ORIGINAL_TEST_NOT_PROJECT_NARRATION"
          and v.get("phrase_sha256") == PHRASE_SHA
          and v.get("phrase_characters") == len(PHRASE),
          "smoke:report_identity_or_text_changed")
    for flag in ("output_audio_saved", "model_files_saved",
                 "production_audio_generated", "script_read_or_uploaded",
                 "hosted_runtime_effective_voice_asset_proven",
                 "rights_approved", "license_cleared", "owner_script_approved",
                 "publication_authorized"):
        check(v.get(flag) is False, f"smoke:forged_or_unsafe:{flag}")
    check(v.get("status") in (
        "BLOCKED_NO_TEST_AUDIO_OBSERVED",
        "TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED"
    ), "smoke:invalid_status")
    check(v.get("test_audio_observed") is (v["status"] ==
           "TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED"),
          "smoke:audio_status_inconsistent")
    check(isinstance(v.get("blockers"), list)
          and set(REQUIRED_BLOCKERS).issubset(set(v["blockers"])),
          "smoke:required_blocker_missing")
    for field in ("voice_network_sha_matches", "voice_cache_sha_matches"):
        records = v.get(field)
        check(isinstance(records, list) and len(records) <= 5,
              f"smoke:bad_{field}")
        for record in records:
            check(isinstance(record, dict)
                  and record.get("sha256") in (VOICE_ONNX_SHA, VOICE_PT_SHA)
                  and record.get("matches_known_upstream_sha256") is True,
                  "smoke:unverified_voice_sha_record")
    check(isinstance(v.get("model_resource_count"), int)
          and 0 <= v["model_resource_count"] <= 20000,
          "smoke:invalid_network_count")


def run(max_seconds: int = 180) -> dict[str, Any]:
    check(20 <= max_seconds <= MAX_WALL_SECONDS, "smoke:unreasonable_timeout")
    result = base_report()
    start = time.monotonic()
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome", headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"]
            )
            try:
                context = browser.new_context(
                    accept_downloads=False,
                    service_workers="allow",
                    java_script_enabled=True,
                )
                page = context.new_page()
                observed_voice_urls: set[str] = set()

                def on_response(response: Any) -> None:
                    url = response.url
                    # Never retain query strings, raw CDN URLs, tokens or response bodies.
                    metadata = safe_resource(url, response.request.resource_type)
                    if metadata:
                        path = metadata["path"].lower()
                        if any(token in path for token in
                               (".onnx", ".bin", ".wasm", "model", "kokoro")):
                            result["model_resource_count"] += 1
                            counts = result["model_resource_host_counts"]
                            host = metadata["host"]
                            if len(counts) < 20 or host in counts:
                                counts[host] = counts.get(host, 0) + 1
                    if not is_exact_voice_response(url):
                        return
                    if url in observed_voice_urls:
                        return
                    observed_voice_urls.add(url)
                    try:
                        header = response.headers.get("content-length")
                        if header is not None and int(header) > 1000000:
                            return
                        payload = response.body()
                        if len(payload) > 1000000:
                            return
                        record = verify_voice_payload(url, payload)
                        if (record["matches_known_upstream_sha256"]
                                and len(result["voice_network_sha_matches"]) < 5):
                            result["voice_network_sha_matches"].append({
                                "voice_filename": record["voice_filename"],
                                "sha256": record["sha256"],
                                "bytes": record["bytes"],
                                "matches_known_upstream_sha256": True,
                                "source_host": record["source"]["host"],
                            })
                        del payload
                    except Exception:
                        # One failed fetch is a missing observation, never a positive match.
                        result["browser_errors"].append("voice_response_not_hashable")

                context.on("response", on_response)
                page.goto(SITE, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2000)
                result["site_visited"] = page.url.startswith(EXPECTED_HOST)

                selector_js = """xs => xs.map((s,i) => ({
                  index:i, options:[...s.options].map(o => ({
                  label:o.label.slice(0,60), value:o.value.slice(0,60)
                }))}))"""
                selects = page.eval_on_selector_all("select", selector_js)
                language, _ = choose_options(selects)
                if language and language["index"] is not None:
                    page.locator("select").nth(language["index"]).select_option(
                        value=language["value"])
                    result["pt_br_selected"] = True
                    page.wait_for_timeout(2000)

                selects = page.eval_on_selector_all("select", selector_js)
                _, voice = choose_options(selects)
                if voice and voice["index"] is not None:
                    page.locator("select").nth(voice["index"]).select_option(
                        value=voice["value"])
                    result["pm_alex_selected"] = True
                    page.wait_for_timeout(1000)

                # Never enter draft or user content. Require exact chosen voice.
                if result["pt_br_selected"] and result["pm_alex_selected"]:
                    textarea = page.locator("textarea")
                    result["textarea_count"] = textarea.count()
                    if textarea.count() == 1:
                        textarea.fill(PHRASE)
                        button = page.get_by_role(
                            "button", name=re.compile(r"^Generate(?: speech)?$", re.I)
                        )
                        result["generate_button_count"] = button.count()
                        if button.count() == 1 and button.is_enabled():
                            button.click(timeout=10000)
                            result["generate_clicked"] = True

                audio_probe_js = """() => [...document.querySelectorAll('audio')]
                    .map(a => ({
                       ready_state:a.readyState,
                       duration:Number.isFinite(a.duration) ? a.duration : null,
                       source_kind:(a.currentSrc || a.src || '').startsWith('blob:')
                         ? 'blob'
                         : (a.currentSrc || a.src || '').startsWith('data:')
                         ? 'data'
                         : (a.currentSrc || a.src || '').startsWith('mediastream:')
                         ? 'media' : 'other'
                    }))"""
                if result["generate_clicked"]:
                    while time.monotonic() - start < max_seconds:
                        nodes = page.evaluate(audio_probe_js)
                        result["html_audio_nodes"] = len(nodes)
                        ok, duration = canonical_audio_nodes(nodes)
                        if ok:
                            result["test_audio_observed"] = True
                            result["test_audio_duration_seconds"] = duration
                            break
                        page.wait_for_timeout(2400)

                # Read only exact pm_alex bin/pt cache entries. Do not inspect
                # general cache contents, browser local storage, or private data.
                cache_js = """async () => {
                  const out=[];
                  if (!('caches' in window)) return out;
                  for(const key of (await caches.keys()).slice(0,10)){
                    const c=await caches.open(key);
                    for(const req of (await c.keys()).slice(0,150)){
                      let u;
                      try{u=new URL(req.url);}catch{continue;}
                      const name=u.pathname.split('/').pop();
                      if (!['pm_alex.bin','pm_alex.pt'].includes(name))continue;
                      if (!['huggingface.co','kokoroweb.app','www.kokoroweb.app']
                          .includes(u.hostname))continue;
                      const resp=await c.match(req);
                      if (!resp)continue;
                      const size=Number(resp.headers.get('content-length')||0);
                      if(size>1000000)continue;
                      const buf=await resp.clone().arrayBuffer();
                      if(buf.byteLength<450000 || buf.byteLength>1000000)continue;
                      const h=new Uint8Array(await crypto.subtle.digest('SHA-256',buf));
                      out.push({filename:name,sha256:[...h].map(x=>x.toString(16)
                          .padStart(2,'0')).join(''),bytes:buf.byteLength});
                      if(out.length>=5)return out;
                    }
                  }
                  return out;
                }"""
                try:
                    cached = page.evaluate(cache_js)
                    for x in cached:
                        expected = VOICE_ONNX_SHA if x["filename"].endswith(".bin") else VOICE_PT_SHA
                        if x["sha256"] == expected:
                            result["voice_cache_sha_matches"].append({
                                "voice_filename": x["filename"],
                                "sha256": x["sha256"],
                                "bytes": x["bytes"],
                                "matches_known_upstream_sha256": True,
                            })
                except Exception:
                    result["browser_errors"].append("exact_voice_cache_unreadable")
                context.close()
            finally:
                browser.close()
    except Exception as exc:
        result["browser_errors"].append("controlled_smoke:" + type(exc).__name__)
    return assess(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="One short isolated technical smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=180)
    args = parser.parse_args()
    report = run(args.max_seconds)
    validate_report(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"],
        "site_visited": report["site_visited"],
        "pt_br_selected": report["pt_br_selected"],
        "pm_alex_selected": report["pm_alex_selected"],
        "generate_clicked": report["generate_clicked"],
        "test_audio_observed": report["test_audio_observed"],
        "test_audio_duration_seconds": report["test_audio_duration_seconds"],
        "voice_network_sha_matches": len(report["voice_network_sha_matches"]),
        "voice_cache_sha_matches": len(report["voice_cache_sha_matches"]),
        "model_resource_count": report["model_resource_count"],
        "errors": report["browser_errors"],
        "publication_authorized": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
