"""Verify upstream ONNX voice bytes without executing, loading, or retaining models.

Cloud CI downloads a bounded binary into a streaming hash and records only
cryptographic evidence. This never establishes what kokoroweb.app actually loads.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, BinaryIO

from agents.content_production import ProductionError, check, read

VOICE_ID = "pm_alex"
EXPECTED_URL = (
    "https://huggingface.co/onnx-community/"
    "Kokoro-82M-v1.0-ONNX/resolve/4685882/voices/pm_alex.bin"
)
EXPECTED_SHA256 = "0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a"
ORIGINAL_PT_SHA256 = "cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526"
MIN_BYTES = 450000
MAX_BYTES = 1000000


def check_manifest(m: Any) -> None:
    check(isinstance(m, dict) and m.get("project") == "verbo-no-chao"
          and m.get("audit_id") == "VNC-ONNX-PM-ALEX-001", "onnx_manifest:project")
    check(m.get("voice_id") == VOICE_ID and m.get("language") == "pt-BR"
          and m.get("format") == "onnx_voice_bin"
          and m.get("model_provider") == "onnx-community"
          and m.get("model_id") == "Kokoro-82M-v1.0-ONNX"
          and m.get("upstream_revision") == "4685882",
          "onnx_manifest:wrong_asset")
    check(m.get("source_url") == EXPECTED_URL
          and m.get("source_file") == "voices/pm_alex.bin"
          and m.get("expected_sha256") == EXPECTED_SHA256
          and m.get("min_bytes") == MIN_BYTES
          and m.get("max_bytes") == MAX_BYTES,
          "onnx_manifest:source_or_digest_modified")
    check(m.get("upstream_file_byte_verification") == "PENDING_CI_DOWNLOAD_AND_SHA256"
          and m.get("hosted_site_asset_identity") == "NOT_ESTABLISHED"
          and m.get("hosted_site_asset_sha256") is None
          and m.get("raw_voice_pack_execution_authorized") is False
          and m.get("rights_approved") is False
          and m.get("publication_authorized") is False,
          "onnx_manifest:forged_verification_or_rights")
    check(m.get("upstream_license_declaration") == "Apache-2.0"
          and m.get("hosted_site") == "https://kokoroweb.app/",
          "onnx_manifest:license_or_host_changed")


def digest_stream(stream: BinaryIO, *, expected: str, min_bytes: int,
                  max_bytes: int) -> tuple[str, int]:
    check(isinstance(expected, str) and len(expected) == 64
          and all(c in "0123456789abcdef" for c in expected),
          "onnx_bytes:invalid_expected_sha")
    check(0 < min_bytes <= max_bytes <= MAX_BYTES, "onnx_bytes:invalid_size_limits")
    count = 0
    sha = hashlib.sha256()
    while True:
        chunk = stream.read(32768)
        check(isinstance(chunk, bytes), "onnx_bytes:not_binary_stream")
        if not chunk:
            break
        count += len(chunk)
        check(count <= max_bytes, "onnx_bytes:size_limit_exceeded")
        sha.update(chunk)
    check(count >= min_bytes, "onnx_bytes:truncated_or_empty")
    actual = sha.hexdigest()
    check(actual == expected, "onnx_bytes:sha256_mismatch")
    return actual, count


def verify_upstream(root: Path, *, stream: BinaryIO | None = None) -> dict[str, Any]:
    evidence: dict[str, str] = {}
    m = read(root.resolve(), "contracts/onnx_voice_asset_v1.json", evidence)
    check_manifest(m)
    result = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "audit_id": "VNC-ONNX-PM-ALEX-001", "voice_id": VOICE_ID,
        "format": "onnx_voice_bin",
        "source_url": EXPECTED_URL,
        "expected_sha256": EXPECTED_SHA256,
        "actual_sha256": None, "bytes_read": 0,
        "upstream_bytes_verified": False,
        "hosted_voice_bytes_verified": False,
        "hosted_voice_sha256": None,
        "license_cleared": False,
        "rights_approved": False,
        "owner_approval": False,
        "audio_generated": False,
        "publication_authorized": False,
        "status": "BLOCKED_UPSTREAM_BYTES_NOT_VERIFIED",
        "blockers": [
            "upstream_onnx_file_unverified",
            "hosted_asset_identity_unverified",
            "runtime_dependency_notices_unverified",
            "script_approval_pending",
        ],
        "evidence_sha256": evidence,
        "limitations": [
            "A successful SHA256 check proves exact upstream ONNX bytes only.",
            "A file downloaded from ONNX Community is not evidence of what a hosted browser session actually loaded.",
            "No binary content is saved, unpickled, imported, used for inference or uploaded as an artifact.",
            "An upstream hash does not release commercial rights, approve the script or authorize publication.",
        ],
    }

    try:
        if stream is not None:
            actual, size = digest_stream(
                stream, expected=EXPECTED_SHA256,
                min_bytes=MIN_BYTES, max_bytes=MAX_BYTES)
        else:
            req = urllib.request.Request(
                EXPECTED_URL, headers={
                    "User-Agent": "verbo-no-chao-asset-integrity/1.0",
                    "Accept": "application/octet-stream",
                })
            # The source URL is constant and HTTPS; urllib verifies TLS by default.
            # HTTPS redirects may be needed for Hugging Face Xet-backed storage.
            with urllib.request.urlopen(req, timeout=35) as response:
                check(response.status == 200, "onnx_bytes:bad_http_status")
                final_url = response.geturl()
                check(final_url.startswith("https://"),
                      "onnx_bytes:insecure_redirect")
                length = response.headers.get("Content-Length")
                if length is not None:
                    check(int(length) <= MAX_BYTES, "onnx_bytes:content_length_exceeds_limit")
                actual, size = digest_stream(
                    response, expected=EXPECTED_SHA256,
                    min_bytes=MIN_BYTES, max_bytes=MAX_BYTES)
    except (ProductionError, OSError, TimeoutError, ValueError,
            urllib.error.URLError) as exc:
        # Do not make a remote availability failure green or forge evidence.
        # Record only a short error code, never a temporary CDN URL or token.
        result["error_type"] = type(exc).__name__
        if isinstance(exc, ProductionError):
            result["error_code"] = str(exc)
        return result

    result.update({
        "actual_sha256": actual,
        "bytes_read": size,
        "upstream_bytes_verified": True,
        "status": "VERIFIED_UPSTREAM_ONNX_BYTES_HOSTED_UNPROVEN",
        "blockers": [
            "hosted_asset_identity_unverified",
            "runtime_dependency_notices_unverified",
            "script_approval_pending",
        ],
    })
    return result


def validate_report(report: Any) -> None:
    check(isinstance(report, dict) and report.get("project") == "verbo-no-chao"
          and report.get("audit_id") == "VNC-ONNX-PM-ALEX-001"
          and report.get("voice_id") == VOICE_ID
          and report.get("format") == "onnx_voice_bin"
          and report.get("source_url") == EXPECTED_URL
          and report.get("expected_sha256") == EXPECTED_SHA256,
          "onnx_report:wrong_source")
    check(report.get("hosted_voice_bytes_verified") is False
          and report.get("hosted_voice_sha256") is None
          and report.get("rights_approved") is False
          and report.get("license_cleared") is False
          and report.get("owner_approval") is False
          and report.get("publication_authorized") is False
          and report.get("audio_generated") is False,
          "onnx_report:forged_clearance")
    verified = report.get("upstream_bytes_verified")
    if verified is True:
        check(report.get("status") == "VERIFIED_UPSTREAM_ONNX_BYTES_HOSTED_UNPROVEN"
              and report.get("actual_sha256") == EXPECTED_SHA256
              and isinstance(report.get("bytes_read"), int)
              and MIN_BYTES <= report["bytes_read"] <= MAX_BYTES
              and "hosted_asset_identity_unverified" in report.get("blockers", []),
              "onnx_report:inconsistent_verified_claim")
    else:
        check(verified is False
              and report.get("status") == "BLOCKED_UPSTREAM_BYTES_NOT_VERIFIED"
              and report.get("actual_sha256") is None
              and "upstream_onnx_file_unverified" in report.get("blockers", []),
              "onnx_report:inconsistent_blocked_claim")


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash-only upstream ONNX asset validation")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = verify_upstream(args.root)
        validate_report(data)
    except (ProductionError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"FATAL CONTRACT ERROR: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "voice_id": data["voice_id"],
        "status": data["status"],
        "upstream_bytes_verified": data["upstream_bytes_verified"],
        "hosted_voice_bytes_verified": False,
        "audio_generated": False,
    }))
    # CI succeeds with a recorded BLOCKED network state: downstream retains blockers.
    # This is not a source authenticity claim when bytes could not be downloaded.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
