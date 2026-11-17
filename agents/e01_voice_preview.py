"""Generate exactly one quarantined, non-publishable E01 WAV preview in Chrome.

Reads the exact AI-reviewed draft; never considers a preview a licensed master.
No app credentials, paid service, automated publication, or re-render of Salmo 13.
Browser audio is measured as real PCM bytes; no quality/listening PASS is forged.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import struct
import time
import wave
from pathlib import Path
from typing import Any

from agents.autonomous_editorial_gate import verify_ai_editorial_review
from agents.content_production import ProductionError, check
from agents.onnx_byte_audit import EXPECTED_SHA256 as ONNX_VOICE_SHA

SITE = "https://kokoroweb.app/#demoContainer"
SITE_ORIGIN = "https://kokoroweb.app/"
TARGET_ID = "VNC-W01-E1"
VOICE_ID = "pm_alex"
MAX_TEXT_CHARS = 2000
MAX_WAV_BYTES = 18_000_000
MAX_WAIT_SECONDS = 480
MIN_DURATION = 25.0
MAX_DURATION = 150.0
VOICE_BIN_BYTES = 522240


def read_json(root: Path, rel: str) -> Any:
    file = (root / rel).resolve()
    check(file.is_relative_to(root.resolve()) and file.is_file()
          and file.stat().st_size < 140000, "voice_preview:missing_or_oversize_source:" + rel)
    return json.loads(file.read_text(encoding="utf-8"))


def approved_source(root: Path) -> tuple[str, dict[str, Any]]:
    seed = read_json(root, "agents/first_batch_seed.json")
    policy = read_json(root, "contracts/autonomous_editorial_policy_v1.json")
    decision = read_json(root, "contracts/e01_ai_editorial_review_v1.json")
    license_packet = read_json(root, "contracts/kokoro_voice_research_v1.json")
    check(isinstance(seed, dict) and isinstance(seed.get("episodes"), list)
          and len(seed["episodes"]) >= 1, "voice_preview:missing_episode")
    episode = seed["episodes"][0]
    ai = verify_ai_editorial_review(policy, decision, episode)
    check(ai["episode_id"] == TARGET_ID
          and ai["status"] == "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION"
          and ai["publication_authorized"] is False
          and ai["voice_audio_generation_authorized"] is False,
          "voice_preview:script_not_protected")
    check(license_packet["project"] == "verbo-no-chao"
          and license_packet["model_license"] == "Apache-2.0"
          and license_packet["upstream_voice_name"] == VOICE_ID
          and license_packet["runtime_terms_url"] == "https://kokoroweb.app/terms"
          and license_packet["runtime_terms_checked"] is True
          and license_packet["runtime_license_status"] ==
          "HOST_COMMERCIAL_NARRATION_CONDITIONALLY_ALLOWED"
          and license_packet["publication_authorized"] is False
          and license_packet["final_approval"] is False,
          "voice_preview:license_evidence_wrong")
    pieces = episode["blocks"]
    check(isinstance(pieces, list) and len(pieces) == 6
          and all(isinstance(x, dict) and isinstance(x.get("text"), str)
                  and x["text"].strip() for x in pieces),
          "voice_preview:segments_invalid")
    full = "\n".join(x["text"].strip() for x in pieces)
    check(0 < len(full) <= MAX_TEXT_CHARS and not re.search(r"<script|<ssml", full, re.I),
          "voice_preview:text_size_or_markup")
    digest = hashlib.sha256(
        re.sub(r"\s+", " ", " ".join(x["text"] for x in pieces).casefold())
        .encode("utf-8")
    ).hexdigest()
    check(digest == ai["script_sha256"],
          "voice_preview:text_sha256_mismatch")
    return full, ai


def inspect_pcm_wav(raw: bytes) -> dict[str, Any]:
    check(isinstance(raw, bytes) and 250000 <= len(raw) <= MAX_WAV_BYTES
          and raw[:4] == b"RIFF" and raw[8:12] == b"WAVE",
          "voice_preview:wrong_or_oversized_audio")
    try:
        with wave.open(io.BytesIO(raw), "rb") as f:
            channels, width, rate = f.getnchannels(), f.getsampwidth(), f.getframerate()
            frames, compression = f.getnframes(), f.getcomptype()
            check(compression == "NONE" and channels in (1, 2)
                  and width == 2 and rate in (22050, 24000, 44100, 48000)
                  and frames > 0, "voice_preview:unsupported_pcm")
            duration = frames / rate
            check(MIN_DURATION <= duration <= MAX_DURATION,
                  "voice_preview:duration_out_of_range")
            data = f.readframes(frames)
    except (wave.Error, EOFError, ValueError, OSError) as e:
        raise ProductionError("voice_preview:invalid_wav_container") from e
    check(len(data) == frames * channels * width,
          "voice_preview:pcm_truncated")
    samples_count = len(data) // 2
    check(samples_count > 0, "voice_preview:empty_pcm")
    # Sample-by-sample integer PCM gate; cannot replace a listening or transcript QA.
    import array
    pcm = array.array("h")
    pcm.frombytes(data)
    peak = max(abs(x) for x in pcm)
    rms = math.sqrt(sum(int(x) * int(x) for x in pcm) / samples_count)
    check(peak >= 350 and rms >= 80,
          "voice_preview:silent_or_near_silent_audio")
    check(peak <= 32767, "voice_preview:pcm_peak_invalid")
    return {
        "container": "RIFF_WAVE_PCM16",
        "sample_rate_hz": rate,
        "channels": channels,
        "frames": frames,
        "duration_seconds": round(duration, 3),
        "bytes": len(raw),
        "pcm_peak": peak,
        "pcm_rms": round(rms, 2),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "listening_qa": "NOT_PERFORMED",
        "transcript_alignment_qa": "NOT_PERFORMED",
        "rights_cleared": False,
        "master_approved": False,
    }


def analyze_browser_cache(page: Any) -> dict[str, Any]:
    # Inspect only the known tiny voice pack, never download the model outside the
    # browser or read arbitrary cache entries, auth tokens, page storage or cookies.
    result = page.evaluate("""async () => {
      if (!('caches' in window)) return [];
      const out=[];
      for(const key of (await caches.keys()).slice(0,10)){
        const cache = await caches.open(key);
        for(const req of (await cache.keys()).slice(0,150)){
          let url;
          try{url=new URL(req.url);}catch{continue;}
          if(url.protocol!=='https:')continue;
          if(!['huggingface.co','kokoroweb.app','www.kokoroweb.app']
            .includes(url.hostname))continue;
          if(url.pathname.split('/').pop()!=='pm_alex.bin')continue;
          const response=await cache.match(req);
          if(!response)continue;
          const contentLength=Number(response.headers.get('content-length')||0);
          if(contentLength>1000000)continue;
          const bytes=await response.clone().arrayBuffer();
          if(bytes.byteLength<450000||bytes.byteLength>1000000)continue;
          const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
          out.push({
            bytes:bytes.byteLength,
            sha256:[...digest].map(x=>x.toString(16).padStart(2,'0')).join(''),
          });
          if(out.length>=5)return out;
        }
      }
      return out;
    }""")
    check(isinstance(result, list), "voice_preview:cache_probe_invalid")
    known = [x for x in result
             if isinstance(x, dict) and x.get("sha256") == ONNX_VOICE_SHA
             and x.get("bytes") == VOICE_BIN_BYTES]
    check(bool(known), "voice_preview:known_voice_not_present_in_same_session")
    return {
        "voice_cache_filename": "pm_alex.bin",
        "voice_cache_sha256": ONNX_VOICE_SHA,
        "voice_cache_bytes": VOICE_BIN_BYTES,
        "observed_in_same_browser_session": True,
        "effective_inference_consumption_proven": False,
    }


def extract_blob_wav(page: Any) -> bytes:
    item = page.evaluate("""async () => {
       const voices=[...document.querySelectorAll('audio')];
       const a=voices.find(x=>x.readyState>=1 &&
         Number.isFinite(x.duration) && x.duration>25 &&
         (x.currentSrc||x.src||'').startsWith('blob:'));
       if (!a) return {error:'NO_VALID_BLOB_PLAYER'};
       const blob=await fetch(a.currentSrc || a.src).then(r=>r.blob());
       if(blob.size>18000000||blob.size<250000) return {error:'AUDIO_SIZE_OUT_OF_RANGE'};
       const bytes=new Uint8Array(await blob.arrayBuffer());
       let binary='';
       for(let i=0;i<bytes.length;i+=32768)
         binary+=String.fromCharCode(...bytes.slice(i,i+32768));
       return {size:bytes.length,b64:btoa(binary)};
    }""")
    check(isinstance(item, dict) and isinstance(item.get("b64"), str)
          and isinstance(item.get("size"), int)
          and 250000 <= item["size"] <= MAX_WAV_BYTES,
          "voice_preview:audio_blob_not_available")
    try:
        wav = base64.b64decode(item["b64"], validate=True)
    except ValueError as e:
        raise ProductionError("voice_preview:invalid_blob_base64") from e
    check(len(wav) == item["size"], "voice_preview:blob_length_mismatch")
    return wav


def synthesize_browser(full_text: str, *, max_seconds: int) -> tuple[bytes, dict[str, Any]]:
    check(MIN_DURATION <= max_seconds <= MAX_WAIT_SECONDS,
          "voice_preview:invalid_execution_budget")
    from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
    start = time.monotonic()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome", headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        try:
            ctx = browser.new_context(accept_downloads=False, service_workers="allow")
            page = ctx.new_page()
            page.set_default_timeout(25000)
            page.goto(SITE, wait_until="domcontentloaded", timeout=40000)
            check(page.url.startswith(SITE_ORIGIN),
                  "voice_preview:unexpected_site_origin")
            page.wait_for_timeout(2000)
            selector_js = """xs => xs.map((s,i)=>({
              index:i,
              options:[...s.options].map(o=>({value:o.value,label:o.label}))
            }))"""
            lists = page.eval_on_selector_all("select", selector_js)
            lang = next(
                ((s["index"], o["value"]) for s in lists for o in s["options"]
                 if any(k in (o["label"]+" "+o["value"]).lower()
                        for k in ("portugu", "brazil", "pt-br", "pt_"))),
                None,
            )
            check(lang is not None, "voice_preview:pt_br_not_available")
            page.locator("select").nth(lang[0]).select_option(value=lang[1])
            page.wait_for_timeout(1600)
            lists = page.eval_on_selector_all("select", selector_js)
            voice = next(
                ((s["index"], o["value"]) for s in lists for o in s["options"]
                 if o["value"].lower() == VOICE_ID),
                None,
            )
            check(voice is not None, "voice_preview:exact_voice_not_available")
            page.locator("select").nth(voice[0]).select_option(value=voice[1])
            check(page.locator("textarea").count() == 1,
                  "voice_preview:unverified_input")
            page.locator("textarea").fill(full_text)
            check(page.url.startswith(SITE_ORIGIN),
                  "voice_preview:redirect_after_input")
            btn = page.get_by_role(
                "button", name=re.compile(r"^Generate(?: speech)?$", re.I)
            )
            check(btn.count() == 1 and btn.is_enabled(),
                  "voice_preview:generate_button_missing")
            btn.click(timeout=25000)
            # Generate exactly once and wait for the WAV-backed audio element.
            while time.monotonic() - start < max_seconds:
                ready = page.evaluate("""() => [...document.querySelectorAll('audio')]
                  .some(a => a.readyState>=1 && Number.isFinite(a.duration)
                    && a.duration>25 && (a.currentSrc||a.src||'').startsWith('blob:'))""")
                if ready:
                    wav = extract_blob_wav(page)
                    cache = analyze_browser_cache(page)
                    return wav, cache
                page.wait_for_timeout(2600)
            raise ProductionError("voice_preview:audio_generation_timeout")
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Internal E01 preview WAV; never release")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=440)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output_dir.resolve()
    check(not out.is_relative_to(root / "contracts")
          and not out.is_relative_to(root / "agents")
          and not out.is_relative_to(root / "docs"),
          "voice_preview:protected_output_root")
    out.mkdir(parents=True, exist_ok=True)
    preview = out / "e01-preview-only.wav"
    preview.unlink(missing_ok=True)
    report: dict[str, Any] = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "episode_id": TARGET_ID, "status": "BLOCKED_TECHNICAL_PREVIEW_NOT_GENERATED",
        "runtime": "KOKORO_WEB_CHROME_ISOLATED",
        "voice_id": VOICE_ID, "language": "pt-BR",
        "source_script_sha256": None,
        "audio_preview_saved": False,
        "production_wav_generated": False,
        "audio_master_approved": False,
        "rights_cleared": False,
        "human_listening_qa_completed": False,
        "transcription_qa_completed": False,
        "video_rendered": False,
        "publication_authorized": False,
        "blockers": [
            "full_voice_runtime_licenses_pending",
            "listening_and_transcription_qa_pending",
            "visual_music_captions_and_master_pending",
            "explicit_publication_permission_required",
        ],
    }
    try:
        text, decision = approved_source(root)
        report["source_script_sha256"] = decision["script_sha256"]
        report["script_character_count"] = len(text)
        wav, cache = synthesize_browser(text, max_seconds=args.max_seconds)
        metrics = inspect_pcm_wav(wav)
        preview.write_bytes(wav)
        report.update({
            "status": "QUARANTINED_WAV_PREVIEW_GENERATED_NOT_RELEASE_CLEARED",
            "audio_preview_saved": True,
            "audio_preview_file": preview.name,
            "physical_wav_metrics": metrics,
            "browser_voice_cache": cache,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        })
    except Exception as exc:
        # Any failed condition must not leave a WAV in an artifact.
        preview.unlink(missing_ok=True)
        report["status"] = "BLOCKED_TECHNICAL_PREVIEW_NOT_GENERATED"
        report["error_code"] = str(exc) if isinstance(exc, ProductionError) else type(exc).__name__
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
    print(json.dumps({
        k: report.get(k) for k in (
            "status", "episode_id", "source_script_sha256",
            "audio_preview_saved", "production_wav_generated",
            "rights_cleared", "publication_authorized", "error_code"
        )
    }, ensure_ascii=False))
    return 0 if report["audio_preview_saved"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
