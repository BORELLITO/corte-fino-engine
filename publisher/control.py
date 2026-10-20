from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from publisher.core import normalize_account_identity, validate_manifest


LEDGER_VERSION = 1
SUCCESS_STATES = {"SCHEDULED", "PUBLIC", "VERIFIED", "METRICS_PENDING", "MEASURED", "LEARNED"}
AMBIGUOUS_STATES = {"UPLOAD_STARTED", "UPLOADED", "RECONCILIATION_REQUIRED"}
FAILURE_STATES = {
    "BLOCKED_WRONG_ACCOUNT",
    "STALE_MEDIA",
    "UPLOAD_FAILED",
    "SCHEDULE_FAILED",
    "WRONG_VISIBILITY",
    "MISSED_SLOT",
    "POST_NOT_FOUND",
    "PLATFORM_RESTRICTED",
    "FYP_INELIGIBLE",
}
ALLOWED_STATES = {
    "BROWSER_READY",
    "ACCOUNT_VERIFIED",
    "UPLOAD_STARTED",
    "UPLOADED",
    *SUCCESS_STATES,
    *AMBIGUOUS_STATES,
    *FAILURE_STATES,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def publication_key(run_id: str, index: int, platform: str) -> str:
    platform = str(platform).strip().casefold()
    if platform not in {"youtube", "tiktok"}:
        raise ValueError("Plataforma inválida; use youtube ou tiktok.")
    return f"{run_id}:{int(index):02d}:{platform}"


def new_ledger(manifest: dict) -> dict:
    validate_manifest(manifest, require_rights=True)
    targets = manifest["target_accounts"]
    entries = {}
    for clip in manifest["clips"]:
        for platform in ("youtube", "tiktok"):
            key = publication_key(manifest["run_id"], clip["index"], platform)
            entries[key] = {
                "publication_key": key,
                "run_id": manifest["run_id"],
                "index": clip["index"],
                "batch_id": clip["batch_id"],
                "batch_index": clip["batch_index"],
                "platform": platform,
                "file_name": clip["name"],
                "drive_id": clip["drive_id"],
                "md5_checksum": clip["md5_checksum"],
                "planned_publish_at": clip["schedule"][f"{platform}_publish_at"],
                "expected_account": targets[platform],
                "observed_account": None,
                "account_verified": False,
                "state": "BROWSER_READY",
                "remote_id": None,
                "remote_url": None,
                "updated_at": _now(),
                "history": [{"state": "BROWSER_READY", "at": _now()}],
            }
    return {
        "version": LEDGER_VERSION,
        "run_id": manifest["run_id"],
        "engine_commit": manifest.get("engine_commit"),
        "target_accounts": dict(targets),
        "created_at": _now(),
        "entries": entries,
    }


def validate_ledger(ledger: dict) -> None:
    if not isinstance(ledger, dict) or ledger.get("version") != LEDGER_VERSION:
        raise RuntimeError("Ledger inválido ou incompatível.")
    entries = ledger.get("entries")
    if not isinstance(entries, dict) or not entries:
        raise RuntimeError("Ledger sem publicações.")
    seen_remote = set()
    for key, entry in entries.items():
        if key != entry.get("publication_key"):
            raise RuntimeError(f"Ledger inconsistente em {key}.")
        if entry.get("state") not in ALLOWED_STATES:
            raise RuntimeError(f"Estado inválido em {key}: {entry.get('state')}")
        for field in ("remote_id", "remote_url"):
            value = str(entry.get(field) or "").strip()
            if value:
                token = (field, value)
                if token in seen_remote:
                    raise RuntimeError(f"Identificador remoto duplicado no ledger: {value}")
                seen_remote.add(token)


def record_receipt(
    ledger: dict,
    key: str,
    *,
    observed_account: str,
    state: str,
    remote_id: str = "",
    remote_url: str = "",
    note: str = "",
) -> dict:
    validate_ledger(ledger)
    entry = ledger["entries"].get(key)
    if not entry:
        raise KeyError(f"Publicação desconhecida: {key}")
    state = str(state or "").strip().upper()
    if state not in ALLOWED_STATES - {"BROWSER_READY"}:
        raise ValueError(f"Estado de receipt inválido: {state}")

    expected = normalize_account_identity(entry.get("expected_account"))
    observed = normalize_account_identity(observed_account)
    if not observed:
        raise RuntimeError("Receipt sem identidade observada da conta.")
    if observed != expected:
        entry.update({
            "observed_account": observed_account,
            "account_verified": False,
            "state": "BLOCKED_WRONG_ACCOUNT",
            "updated_at": _now(),
        })
        entry["history"].append({
            "state": "BLOCKED_WRONG_ACCOUNT",
            "at": _now(),
            "note": f"esperado={entry.get('expected_account')} observado={observed_account}",
        })
        return ledger

    rid = str(remote_id or "").strip()
    rurl = str(remote_url or "").strip()
    for other_key, other in ledger["entries"].items():
        if other_key == key:
            continue
        if rid and rid == str(other.get("remote_id") or "").strip():
            raise RuntimeError(f"remote_id já usado por {other_key}")
        if rurl and rurl == str(other.get("remote_url") or "").strip():
            raise RuntimeError(f"remote_url já usada por {other_key}")

    if state in {"SCHEDULED", "PUBLIC", "VERIFIED", "METRICS_PENDING", "MEASURED", "LEARNED"} and not (rid or rurl):
        raise RuntimeError(f"Estado {state} exige remote_id ou remote_url.")

    entry.update({
        "observed_account": observed_account,
        "account_verified": True,
        "state": state,
        "remote_id": rid or entry.get("remote_id"),
        "remote_url": rurl or entry.get("remote_url"),
        "updated_at": _now(),
    })
    event = {"state": state, "at": _now()}
    if note:
        event["note"] = str(note)
    entry["history"].append(event)
    return ledger


def reconciliation_summary(ledger: dict) -> dict:
    validate_ledger(ledger)
    entries = list(ledger["entries"].values())
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["state"]] = counts.get(entry["state"], 0) + 1
    ambiguous = [e["publication_key"] for e in entries if e["state"] in AMBIGUOUS_STATES]
    failures = [e["publication_key"] for e in entries if e["state"] in FAILURE_STATES]
    not_confirmed = [
        e["publication_key"]
        for e in entries
        if e["state"] not in SUCCESS_STATES and e["state"] not in FAILURE_STATES and e["state"] not in AMBIGUOUS_STATES
    ]
    return {
        "total": len(entries),
        "counts": counts,
        "ambiguous": ambiguous,
        "failures": failures,
        "not_confirmed": not_confirmed,
        "safe_to_retry": len(ambiguous) == 0,
        "fully_reconciled": len(ambiguous) == 0 and len(not_confirmed) == 0,
    }


def load_ledger(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_ledger(data)
    return data


def save_ledger(path: Path, ledger: dict) -> None:
    validate_ledger(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
