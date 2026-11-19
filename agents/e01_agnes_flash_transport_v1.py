"""Agnes Video Flash API transport for VERBO NO CHÃO, E01 S01.

Dry-run and authenticated catalog checks are available now. A video POST is
intentionally impossible with the checked-in, deny-by-default runtime gate.
Never store private API keys, video URLs, or account details in this public repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from agents.e01_agnes_flash_free_only import MODEL, payload, validate as validate_baseline
from agents.e01_stock_candidates import ROOT

BASE = "https://apihub.agnes-ai.com"
MODELS_URL = BASE + "/v1/models"
CREATE_URL = BASE + "/v1/videos"
POLL_URL = BASE + "/agnesapi"
GATE = Path("contracts/e01_agnes_flash_runtime_gate_v1.json")
SCENE = "VNC-E01V2-S01"
MAX_BODY = 1024 * 1024
MAX_POSTS = 1


class AgnesTransportError(RuntimeError):
    """Intentionally redact upstream error bodies, which may contain secrets."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AgnesTransportError("unexpected_provider_redirect")


def gate_config(root: Path = ROOT) -> dict:
    doc = json.loads((root / GATE).read_text(encoding="utf-8"))
    if (doc.get("project") != "verbo-no-chao"
            or doc.get("scene_id") != SCENE
            or doc.get("model") != MODEL
            or doc.get("endpoint") != CREATE_URL
            or doc.get("price_ceiling_usd") != 0
            or type(doc.get("price_ceiling_usd")) not in (int, float)
            or doc.get("max_post_attempts") != MAX_POSTS
            or doc.get("publication_authorized") is not False):
        raise AgnesTransportError("invalid_or_untrusted_runtime_gate")
    return doc


def _http_json(method: str, url: str, key: str, body: dict | None = None) -> dict:
    if method not in {"GET", "POST"}:
        raise AgnesTransportError("unsupported_http_method")
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname != "apihub.agnes-ai.com"
            or parsed.port is not None or parsed.username or parsed.password
            or parsed.fragment or parsed.path not in {"/v1/models", "/v1/videos", "/agnesapi"}):
        raise AgnesTransportError("endpoint_not_allowlisted")
    if method == "POST" and (url != CREATE_URL or not isinstance(body, dict)):
        raise AgnesTransportError("post_not_allowlisted")
    if method == "GET" and body is not None:
        raise AgnesTransportError("get_with_body_forbidden")
    if not isinstance(key, str) or len(key.strip()) < 8:
        raise AgnesTransportError("missing_api_key")
    data = json.dumps(body).encode("utf-8") if method == "POST" else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "vnc-agnes-gated/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
            data = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        # Provider can echo auth/inputs in response bodies. Do not include them.
        if exc.code in (429, 503):
            raise AgnesTransportError("provider_quota_or_queue_unavailable") from None
        if exc.code in (401, 403):
            raise AgnesTransportError("api_key_or_plan_rejected") from None
        raise AgnesTransportError("provider_http_" + str(exc.code)) from None
    except urllib.error.URLError:
        raise AgnesTransportError("provider_network_unavailable") from None
    if len(data) > MAX_BODY:
        raise AgnesTransportError("provider_response_too_large")
    try:
        obj = json.loads(data)
    except (ValueError, UnicodeError):
        raise AgnesTransportError("provider_non_json_response") from None
    if not isinstance(obj, dict):
        raise AgnesTransportError("provider_response_not_object")
    return obj


def plan(root: Path = ROOT) -> dict:
    baseline = validate_baseline(root)
    gate = gate_config(root)
    request = payload()
    if request != payload() or request["model"] != MODEL or request["size"] != "720P":
        raise AgnesTransportError("request_spec_changed")
    return {
        "project": "verbo-no-chao", "scene_id": SCENE, "model": MODEL,
        "status": "PLAN_ONLY_NO_PROVIDER_REQUEST",
        "request": request, "api_key_included": False,
        "baseline_dry_run": baseline["request_not_sent"],
        "account_specific_zero_price_verified": gate.get("account_specific_zero_price_verified") is True,
        "submit_enabled": gate.get("enable_submission") is True,
        "generation_started": False, "publication_authorized": False,
    }


def model_preflight(key: str, root: Path = ROOT) -> dict:
    gate_config(root)
    if not key:
        return {"status": "BLOCKED_NO_AGNES_API_KEY", "network_requested": False,
                "generation_started": False}
    obj = _http_json("GET", MODELS_URL, key)
    entries = obj.get("data")
    found = (isinstance(entries, list) and any(
        isinstance(item, dict) and item.get("id") == MODEL for item in entries
    ))
    return {
        "status": "MODEL_LISTED_PRICE_UNVERIFIED" if found else "MODEL_NOT_LISTED",
        "model_available_in_catalog": found,
        "account_eligible_for_free_promo_verified": False,
        "account_specific_zero_price_verified": False,
        "network_requested": True, "generation_started": False,
    }


def _can_submit(gate: dict, auth: str) -> None:
    required = ("api_access_verified", "account_default_plan_verified",
                "account_specific_zero_price_verified",
                "zero_price_reverified_before_generation",
                "scene_generation_authorized", "enable_submission")
    if not all(gate.get(field) is True for field in required):
        raise AgnesTransportError("submit_blocked_unverified_free_entitlement_or_approval")
    if auth != SCENE:
        raise AgnesTransportError("submit_blocked_missing_scene_specific_authorization")
    if gate.get("price_ceiling_usd") != 0 or gate.get("max_post_attempts") != 1:
        raise AgnesTransportError("submit_blocked_unbounded_cost_or_retries")


def submit_once(key: str, auth: str, root: Path = ROOT) -> dict:
    # No automatic retries. Re-submission can create a second billable task.
    gate = gate_config(root)
    _can_submit(gate, auth)
    if not key:
        raise AgnesTransportError("missing_api_key")
    request = payload()
    if (request.get("model") != MODEL or request.get("mode") != "text"
            or request.get("size") != "720P" or request.get("seconds") != "6"
            or request.get("n") != 1 or request.get("aspect_ratio") != "9:16"):
        raise AgnesTransportError("unexpected_paid_or_unscoped_payload")
    obj = _http_json("POST", CREATE_URL, key, request)
    ident = obj.get("video_id")
    if ident is None and isinstance(obj.get("data"), dict):
        ident = obj["data"].get("video_id")
    if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9._-]{6,128}", ident):
        raise AgnesTransportError("submission_ambiguous_no_safe_video_id_no_retry")
    return {"status": "JOB_SUBMITTED_NOT_APPROVED", "video_id": ident,
            "scene_id": SCENE, "generation_started": True,
            "publication_authorized": False}


def poll_once(key: str, video_id: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9._-]{6,128}", video_id or ""):
        raise AgnesTransportError("invalid_video_id")
    query = urllib.parse.urlencode({"video_id": video_id, "model_name": MODEL})
    obj = _http_json("GET", POLL_URL + "?" + query, key)
    status = obj.get("status")
    if status not in {"completed", "failed", "pending", "processing", "queued", "running"}:
        raise AgnesTransportError("unrecognized_provider_job_status")
    media = obj.get("url")
    if status == "completed" and not (
        isinstance(media, str) and media.startswith("https://")
    ):
        raise AgnesTransportError("completed_without_https_media")
    # Never log or publish a private provider output URL in this public repo.
    return {"status": status, "scene_id": SCENE, "video_id": video_id,
            "media_url_sha256": hashlib.sha256(media.encode()).hexdigest()
            if status == "completed" else None,
            "media_downloaded": False, "rights_cleared": False,
            "master_allowed": False, "publication_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("plan", "preflight", "poll", "submit"),
                        default="plan")
    parser.add_argument("--video-id", default="")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    try:
        if args.mode == "plan":
            result = plan()
        elif args.mode == "preflight":
            result = model_preflight(os.environ.get("AGNES_API_KEY", ""))
        elif args.mode == "poll":
            result = poll_once(os.environ.get("AGNES_API_KEY", ""), args.video_id)
        else:
            result = submit_once(os.environ.get("AGNES_API_KEY", ""),
                                 os.environ.get("AGNES_SCENE_AUTHORIZATION", ""))
    except (AgnesTransportError, ValueError, KeyError) as exc:
        result = {"status": "BLOCKED", "reason": str(exc),
                  "generation_started": False, "publication_authorized": False}
        exit_code = 2
    else:
        exit_code = 0
    safe = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        dest = Path(args.report)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(safe + "\n", encoding="utf-8")
    print(safe)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
