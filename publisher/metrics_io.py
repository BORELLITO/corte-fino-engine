from __future__ import annotations

import io
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from publisher.control import validate_ledger
from publisher.core import normalize_account_identity, validate_manifest
from publisher.google_io import drive_service
from publisher.performance import (
    PERFORMANCE_HORIZONS,
    record_performance_snapshot,
    sync_publication_receipts,
    validate_performance_ledger,
)


RUN_STATE_VERSION = 1
METRICS_PACKAGE_VERSION = 1
METRICS_RESULT_VERSION = 1
STATE_FOLDER_NAME = "_corte_fino_publisher_state"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _batch_parent_from_folder(drive, folder_id: str) -> str:
    item = drive.files().get(
        fileId=str(folder_id).strip(),
        fields="id,parents,trashed,mimeType",
    ).execute(num_retries=4)
    if item.get("trashed"):
        raise RuntimeError("Pasta do lote está na lixeira.")
    parents = item.get("parents") or []
    if len(parents) != 1:
        raise RuntimeError("Pasta do lote precisa ter exatamente um parent.")
    return str(parents[0])


def _shared_batch_parent(drive, manifest: dict) -> str:
    folder_ids = [str(value).strip() for value in manifest.get("drive_folder_ids", []) if str(value).strip()]
    if not folder_ids:
        raise RuntimeError("Manifesto sem drive_folder_ids.")
    parents = [_batch_parent_from_folder(drive, folder_id) for folder_id in folder_ids]
    if len(set(parents)) != 1:
        raise RuntimeError("Os lotes não compartilham o mesmo diretório raiz.")
    return parents[0]


def _state_folder(drive, parent_id: str, *, create: bool) -> dict | None:
    escaped = STATE_FOLDER_NAME.replace("'", "\\'")
    matches = drive.files().list(
        q=(
            f"'{parent_id}' in parents and trashed = false and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"name = '{escaped}'"
        ),
        pageSize=10,
        fields="files(id,name,mimeType,parents,trashed)",
    ).execute(num_retries=4).get("files", [])
    if len(matches) > 1:
        raise RuntimeError("Mais de uma pasta de estado do Publisher foi encontrada.")
    if matches:
        return matches[0]
    if not create:
        return None
    return drive.files().create(
        body={
            "name": STATE_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id,name,mimeType,parents",
    ).execute(num_retries=4)


def _state_filename(run_id: str) -> str:
    run_id = str(run_id or "").strip()
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in run_id):
        raise ValueError("run_id inválido para persistência.")
    return f"run-{run_id}.json"


def _read_drive_json(drive, file_id: str) -> dict:
    from googleapiclient.http import MediaIoBaseDownload

    buffer = io.BytesIO()
    request = drive.files().get_media(fileId=file_id)
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk(num_retries=4)
    try:
        data = json.loads(buffer.getvalue().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Estado persistido contém JSON inválido.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Estado persistido precisa ser um objeto JSON.")
    return data


def _upsert_drive_json(drive, parent_id: str, name: str, payload: dict) -> dict:
    from googleapiclient.http import MediaIoBaseUpload

    escaped = name.replace("'", "\\'")
    matches = drive.files().list(
        q=f"'{parent_id}' in parents and trashed = false and name = '{escaped}'",
        pageSize=10,
        fields="files(id,name,mimeType,parents,modifiedTime)",
    ).execute(num_retries=4).get("files", [])
    if len(matches) > 1:
        raise RuntimeError(f"Duplicidade detectada no Drive para {name}.")
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(raw), mimetype="application/json", resumable=False)
    if matches:
        item = drive.files().update(
            fileId=matches[0]["id"],
            body={"name": name},
            media_body=media,
            fields="id,name,mimeType,webViewLink,modifiedTime,parents",
        ).execute(num_retries=4)
    else:
        item = drive.files().create(
            body={"name": name, "parents": [parent_id], "mimeType": "application/json"},
            media_body=media,
            fields="id,name,mimeType,webViewLink,modifiedTime,parents",
        ).execute(num_retries=4)
    return item


def _sanitized_manifest(manifest: dict) -> dict:
    cleaned = deepcopy(manifest)
    for clip in cleaned.get("clips", []):
        if isinstance(clip, dict):
            clip.pop("transcript", None)
    cleaned["transcripts"] = "redacted"
    return cleaned


def validate_run_state(state: dict) -> None:
    if not isinstance(state, dict) or state.get("version") != RUN_STATE_VERSION:
        raise RuntimeError("Run state inválido ou incompatível.")
    if state.get("kind") != "publisher_run_state":
        raise RuntimeError("Run state com kind inválido.")
    manifest = state.get("manifest")
    control = state.get("control_ledger")
    performance = state.get("performance_ledger")
    validate_manifest(manifest)
    validate_ledger(control)
    validate_performance_ledger(performance)
    run_ids = {
        str(state.get("run_id") or ""),
        str(manifest.get("run_id") or ""),
        str(control.get("run_id") or ""),
        str(performance.get("run_id") or ""),
    }
    if len(run_ids) != 1 or "" in run_ids:
        raise RuntimeError("Run state mistura execuções diferentes.")


def build_run_state(manifest: dict, control_ledger: dict, performance_ledger: dict) -> dict:
    validate_manifest(manifest)
    validate_ledger(control_ledger)
    validate_performance_ledger(performance_ledger)
    run_id = str(manifest.get("run_id") or "")
    if run_id != str(control_ledger.get("run_id") or "") or run_id != str(performance_ledger.get("run_id") or ""):
        raise RuntimeError("Manifesto, control ledger e performance ledger pertencem a execuções diferentes.")
    state = {
        "version": RUN_STATE_VERSION,
        "kind": "publisher_run_state",
        "run_id": run_id,
        "saved_at": _now(),
        "engine_commit": manifest.get("engine_commit"),
        "manifest": _sanitized_manifest(manifest),
        "control_ledger": deepcopy(control_ledger),
        "performance_ledger": deepcopy(performance_ledger),
    }
    validate_run_state(state)
    return state


def save_run_state_to_drive(manifest: dict, control_ledger: dict, performance_ledger: dict) -> dict:
    drive = drive_service()
    parent_id = _shared_batch_parent(drive, manifest)
    folder = _state_folder(drive, parent_id, create=True)
    assert folder is not None
    state = build_run_state(manifest, control_ledger, performance_ledger)
    item = _upsert_drive_json(drive, folder["id"], _state_filename(state["run_id"]), state)
    return {
        "run_id": state["run_id"],
        "file_id": item.get("id"),
        "file_name": item.get("name"),
        "modified_time": item.get("modifiedTime"),
        "state_folder_id": folder["id"],
        "state_folder_name": folder.get("name"),
    }


def load_run_state_from_drive(batch_folder_id: str, run_id: str) -> dict:
    drive = drive_service()
    parent_id = _batch_parent_from_folder(drive, str(batch_folder_id).strip())
    folder = _state_folder(drive, parent_id, create=False)
    if not folder:
        raise RuntimeError("Pasta de estado persistente ainda não existe.")
    name = _state_filename(run_id)
    escaped = name.replace("'", "\\'")
    matches = drive.files().list(
        q=f"'{folder['id']}' in parents and trashed = false and name = '{escaped}'",
        pageSize=10,
        fields="files(id,name,mimeType,parents,modifiedTime)",
    ).execute(num_retries=4).get("files", [])
    if len(matches) != 1:
        raise RuntimeError(f"Estado da execução {run_id} não encontrado de forma única.")
    state = _read_drive_json(drive, matches[0]["id"])
    validate_run_state(state)
    return state


def restore_run_state_files(state: dict, *, manifest_path: Path, control_path: Path, performance_path: Path) -> None:
    validate_run_state(state)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    control_path.parent.mkdir(parents=True, exist_ok=True)
    performance_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(state["manifest"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    control_path.write_text(json.dumps(state["control_ledger"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    performance_path.write_text(json.dumps(state["performance_ledger"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _horizon_delta(horizon: str) -> timedelta:
    normalized = str(horizon or "").strip().casefold()
    if normalized not in PERFORMANCE_HORIZONS:
        raise ValueError("Horizonte inválido; use 1h, 6h, 24h ou 72h.")
    return timedelta(hours=int(normalized[:-1]))


def build_metrics_package(control_ledger: dict, performance_ledger: dict, *, horizon: str, now: datetime | None = None) -> dict:
    validate_ledger(control_ledger)
    validate_performance_ledger(performance_ledger)
    if str(control_ledger.get("run_id")) != str(performance_ledger.get("run_id")):
        raise RuntimeError("Ledgers pertencem a execuções diferentes.")
    sync_publication_receipts(performance_ledger, control_ledger)
    delta = _horizon_delta(horizon)
    normalized_horizon = str(horizon).casefold()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    items = []
    for key, entry in sorted(performance_ledger["entries"].items()):
        if not entry.get("publication_verified"):
            continue
        if normalized_horizon in (entry.get("snapshots") or {}):
            continue
        planned = _parse_utc(entry["planned_publish_at"])
        due_at = planned + delta
        if due_at > current:
            continue
        receipt = control_ledger["entries"][key]
        platform = entry["platform"]
        fields = (
            [
                "views", "shown_in_feed", "viewed_rate", "avg_view_duration_seconds",
                "avg_percentage_viewed", "likes", "comments", "shares",
                "subscribers_gained", "restrictions",
            ]
            if platform == "youtube"
            else [
                "views", "reach", "for_you_pct", "avg_watch_time_seconds",
                "full_watch_rate", "likes", "comments", "shares", "fyp_eligible",
                "originality_notice", "account_status",
            ]
        )
        items.append({
            "publication_key": key,
            "platform": platform,
            "horizon": normalized_horizon,
            "due_at": due_at.isoformat().replace("+00:00", "Z"),
            "planned_publish_at": entry["planned_publish_at"],
            "expected_account": receipt.get("expected_account"),
            "remote_id": receipt.get("remote_id"),
            "remote_url": receipt.get("remote_url"),
            "remote_reference": receipt.get("remote_reference"),
            "file_name": entry.get("file_name"),
            "source": entry.get("source"),
            "topic": entry.get("topic"),
            "required_fields": fields,
            "studio_checks": (
                ["public_status", "restrictions", "shown_in_feed", "viewed_vs_swiped"]
                if platform == "youtube"
                else ["public_status", "fyp_eligibility", "originality_or_reuse_notice", "account_status"]
            ),
        })

    return {
        "version": METRICS_PACKAGE_VERSION,
        "kind": "studio_metrics_collection",
        "run_id": performance_ledger["run_id"],
        "generated_at": _now(),
        "horizon": normalized_horizon,
        "items": items,
        "result_contract": {
            "version": METRICS_RESULT_VERSION,
            "kind": "studio_metrics_result",
            "run_id": performance_ledger["run_id"],
            "horizon": normalized_horizon,
            "items": [
                {
                    "publication_key": "COPY_FROM_ITEM",
                    "platform": "youtube|tiktok",
                    "observed_account": "ACCOUNT_VISIBLE_IN_STUDIO",
                    "metrics": {"FIELD": "VALUE"},
                    "evidence": "optional short Studio reference",
                }
            ],
        },
    }


def _metrics_package_filename(run_id: str, horizon: str) -> str:
    return f"metrics-{_state_filename(run_id)[4:-5]}-{str(horizon).casefold()}.json"


def metrics_result_filename(run_id: str, horizon: str) -> str:
    return f"metrics-result-{_state_filename(run_id)[4:-5]}-{str(horizon).casefold()}.json"


def save_metrics_package_to_drive(manifest: dict, package: dict) -> dict:
    drive = drive_service()
    parent_id = _shared_batch_parent(drive, manifest)
    folder = _state_folder(drive, parent_id, create=True)
    assert folder is not None
    name = _metrics_package_filename(package["run_id"], package["horizon"])
    item = _upsert_drive_json(drive, folder["id"], name, package)
    return {
        "file_id": item.get("id"),
        "file_name": item.get("name"),
        "modified_time": item.get("modifiedTime"),
        "state_folder_id": folder["id"],
        "expected_result_file": metrics_result_filename(package["run_id"], package["horizon"]),
    }


def load_metrics_result_from_drive(manifest: dict, run_id: str, horizon: str) -> dict:
    drive = drive_service()
    parent_id = _shared_batch_parent(drive, manifest)
    folder = _state_folder(drive, parent_id, create=False)
    if not folder:
        raise RuntimeError("Pasta de estado persistente não existe.")
    name = metrics_result_filename(run_id, horizon)
    escaped = name.replace("'", "\\'")
    matches = drive.files().list(
        q=f"'{folder['id']}' in parents and trashed = false and name = '{escaped}'",
        pageSize=10,
        fields="files(id,name,mimeType,parents,modifiedTime)",
    ).execute(num_retries=4).get("files", [])
    if len(matches) != 1:
        raise RuntimeError(
            f"Resultado do Work não encontrado de forma única: {name}. "
            "O Work deve salvar exatamente esse arquivo no cofre do Publisher."
        )
    return _read_drive_json(drive, matches[0]["id"])


def validate_metrics_result(result: dict, package: dict, control_ledger: dict) -> None:
    if not isinstance(result, dict) or result.get("version") != METRICS_RESULT_VERSION:
        raise RuntimeError("Resultado de métricas inválido.")
    if result.get("kind") != "studio_metrics_result":
        raise RuntimeError("Resultado de métricas com kind inválido.")
    if str(result.get("run_id")) != str(package.get("run_id")):
        raise RuntimeError("Resultado pertence a outra execução.")
    if str(result.get("horizon")).casefold() != str(package.get("horizon")).casefold():
        raise RuntimeError("Resultado pertence a outro horizonte.")
    expected = {item["publication_key"]: item for item in package.get("items", [])}
    rows = result.get("items")
    if not isinstance(rows, list):
        raise RuntimeError("Resultado sem lista de itens.")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Item de resultado inválido.")
        key = str(row.get("publication_key") or "")
        if key not in expected:
            raise RuntimeError(f"Resultado contém publication_key inesperada: {key}")
        if key in seen:
            raise RuntimeError(f"Resultado duplicado para {key}")
        seen.add(key)
        if str(row.get("platform") or "").casefold() != str(expected[key]["platform"]).casefold():
            raise RuntimeError(f"Plataforma divergente para {key}")
        observed = normalize_account_identity(row.get("observed_account"))
        expected_account = normalize_account_identity(control_ledger["entries"][key].get("expected_account"))
        if not observed or observed != expected_account:
            raise RuntimeError(f"Conta observada divergente para {key}")
        if not isinstance(row.get("metrics"), dict) or not row["metrics"]:
            raise RuntimeError(f"Métricas ausentes para {key}")


def apply_metrics_result(
    control_ledger: dict,
    performance_ledger: dict,
    package: dict,
    result: dict,
) -> dict:
    validate_ledger(control_ledger)
    validate_performance_ledger(performance_ledger)
    validate_metrics_result(result, package, control_ledger)
    sync_publication_receipts(performance_ledger, control_ledger)
    for row in result["items"]:
        record_performance_snapshot(
            performance_ledger,
            row["publication_key"],
            horizon=result["horizon"],
            metrics=row["metrics"],
        )
    return performance_ledger
