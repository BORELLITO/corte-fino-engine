"""One authorized Agnes S01 attempt, once and only once, price-guarded.

This is a separate single-shot execution from the permanent read-only
preflight. The checked-in main generation contract remains deny-by-default.
Public repository: no API keys, signed media URLs, personal data or media.
"""
from __future__ import annotations

import base64
import copy
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from agents import e01_agnes_flash_transport_v1 as transport

DOCS_URL = "https://wiki.agnes-ai.com/en/docs/pricing.md"
REPO = "BORELLITO/verbo-no-chao-engine"
BRANCH = "verbo-no-chao/agnes-flash-transport-gated-20261119-v1"
LOCK = "operations/agnes_s01_one_shot_lock_20261119.json"
AUTHORIZATION = "VNC-E01V2-S01"
MAX_DOC_BYTES = 250_000
MAX_POLL_SECONDS = 240


def fail(code: str):
    # Fixed public error codes. Neither upstream HTTP error bodies nor secrets.
    print(json.dumps({"status": "BLOCKED", "reason": code,
                      "publication_authorized": False}))
    raise SystemExit(2)


def price_is_zero(markdown: str) -> bool:
    """Strictly match Flash 720P trial column, never the list-price column."""
    if not isinstance(markdown, str) or len(markdown) < 2000:
        return False
    if "Only items priced at zero are free" not in markdown:
        return False
    if "default users (`default`)" not in markdown:
        return False
    if "Agent Plan usage is billed" not in markdown:
        return False
    section = markdown.split("## Video models", 1)
    if len(section) != 2:
        return False
    match = re.search(
        r"<tr>\s*<td>`agnes-video-2\.5-flash`</td>"
        r"\s*<td>720P video duration</td>"
        r"\s*<td>`\$0\.025 / second`</td>"
        r"\s*<td>\*\*`\$0 / second`\*\*</td>\s*</tr>",
        section[1],
    )
    return bool(match and "limited-time free promotion" in section[1])


def fetch_price_proof():
    req = urllib.request.Request(DOCS_URL, headers={"User-Agent": "vnc-one-shot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=16) as res:
            if res.status != 200:
                fail("price_document_not_http_200")
            raw = res.read(MAX_DOC_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        fail("price_document_unavailable")
    if len(raw) > MAX_DOC_BYTES:
        fail("price_document_too_large")
    try:
        document = raw.decode("utf-8")
    except UnicodeError:
        fail("price_document_not_utf8")
    if not price_is_zero(document):
        fail("official_flash_zero_price_not_reverified")
    return True


def commit_lock_once(token: str, sha: str):
    if not token or len(token) < 16:
        fail("github_token_missing")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail("invalid_checkout_sha")
    url = f"https://api.github.com/repos/{REPO}/contents/{LOCK}"
    body = {
        "message": "audit(vnc): record one-time Agnes S01 API attempt before POST",
        "content": base64.b64encode(
            json.dumps({"project": "VERBO_NO_CHAO_EXCLUSIVO",
                        "scene_id": AUTHORIZATION,
                        "status": "ATTEMPT_CONSUMED_BEFORE_EXTERNAL_REQUEST",
                        "source_sha": sha,
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                        "max_provider_posts": 1,
                        "price_ceiling_usd": 0,
                        "publication_authorized": False}).encode()
        ).decode(),
        "branch": BRANCH,
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="PUT",
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "vnc-once-only/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=16) as res:
            if res.status != 201:
                fail("github_lock_not_created")
    except urllib.error.HTTPError as error:
        if error.code == 422:  # existing lock: no retries, even for queue failures
            fail("one_shot_already_consumed")
        fail("github_lock_unavailable_http_" + str(error.code))
    except (urllib.error.URLError, TimeoutError, OSError):
        fail("github_lock_network_unknown_no_post")
    print("DURABLE_LOCK_CREATED_BEFORE_PROVIDER_POST")


def submit_with_ephemeral_proven_gate(key: str):
    """Keep canonical gate on disk permanently false; use runtime-only proof."""
    canonical = transport.gate_config()
    proof = copy.deepcopy(canonical)
    for field in ("api_access_verified", "account_default_plan_verified",
                  "account_specific_zero_price_verified",
                  "zero_price_reverified_before_generation",
                  "scene_generation_authorized", "enable_submission"):
        proof[field] = True
    proof["publication_authorized"] = False
    proof["master_allowed"] = False
    proof["rights_cleared"] = False
    proof["reference_upload_authorized"] = False
    with tempfile.TemporaryDirectory(prefix="vnc-s01-once-") as temp:
        root = Path(temp)
        target = root / transport.GATE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(proof), encoding="utf-8")
        return transport.submit_once(key, AUTHORIZATION, root=root)


def main():
    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        fail("must_run_on_authenticated_branch_push")
    if os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH:
        fail("unexpected_branch")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        fail("reruns_never_repeat_provider_posts")
    key = os.environ.get("AGNES_API_KEY", "")
    if len(key) < 8:
        fail("secret_missing")
    if os.environ.get("VNC_S01_AUTHORIZATION") != AUTHORIZATION:
        fail("specific_scene_not_authorized")
    # Existing baseline and immutable approved cinematic prompt must still pass.
    baseline = transport.plan()
    if baseline["submit_enabled"] or baseline["scene_id"] != AUTHORIZATION:
        fail("canonical_runtime_gate_not_closed")

    fetch_price_proof()
    print("OFFICIAL_DEFAULT_FLASH_720P_ZERO_USD_PRICE_CONFIRMED")
    # Authenticated GET. Never treat model catalog alone as price evidence.
    info = transport.model_preflight(key)
    if info.get("status") != "MODEL_LISTED_PRICE_UNVERIFIED":
        fail("authenticated_model_not_available")
    print("AUTHENTICATED_MODEL_CATALOG_CONFIRMED")
    # User account's default plan and $0 eligibility were supported by their
    # billing screenshots and Live Chat on Nov 19; no live account-quote
    # endpoint is documented. This is a known residual, not a guarantee.
    commit_lock_once(os.environ.get("GITHUB_TOKEN", ""), os.environ.get("GITHUB_SHA", ""))
    try:
        result = submit_with_ephemeral_proven_gate(key)
    except transport.AgnesTransportError as error:
        allowed = {"provider_quota_or_queue_unavailable",
                   "provider_http_400", "provider_http_402",
                   "provider_http_429", "provider_http_500",
                   "provider_network_unavailable",
                   "submission_ambiguous_no_safe_video_id_no_retry",
                   "api_key_or_plan_rejected"}
        reason = str(error)
        fail(reason if reason in allowed else "provider_submit_failed_no_retry")
    video_id = result["video_id"]
    print(json.dumps({"status": "JOB_SUBMITTED_NOT_APPROVED",
                      "scene": AUTHORIZATION, "video_id": video_id,
                      "publication_authorized": False}))
    started = time.monotonic()
    while time.monotonic() - started < MAX_POLL_SECONDS:
        time.sleep(12)
        try:
            state = transport.poll_once(key, video_id)
        except transport.AgnesTransportError:
            print("POLL_UNAVAILABLE_JOB_EXISTS_NO_RESUBMIT")
            return
        if state["status"] in {"completed", "failed"}:
            print(json.dumps({"status": state["status"], "video_id": video_id,
                              "media_url_sha256": state.get("media_url_sha256"),
                              "media_downloaded": False, "rights_cleared": False,
                              "master_allowed": False, "publication_authorized": False}))
            return
    print(json.dumps({"status": "POLL_TIMEOUT_JOB_MAY_CONTINUE",
                      "video_id": video_id,
                      "generation_started": True,
                      "publication_authorized": False}))


if __name__ == "__main__":
    main()
