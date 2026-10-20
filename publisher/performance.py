from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from publisher.control import validate_ledger
from publisher.core import validate_manifest


PERFORMANCE_LEDGER_VERSION = 1
LEARNING_HISTORY_VERSION = 1
PERFORMANCE_HORIZONS = ("1h", "6h", "24h", "72h")
LEARNING_HORIZONS = {"24h", "72h"}
MIN_DISTRIBUTION_SAMPLE = 100
MIN_CREATOR_FEEDBACK_SAMPLES = 20
MIN_TRIGGER_SAMPLES = 5
MAX_TRIGGER_ADJUSTMENT = 2.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _float(value: Any, *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Métrica numérica inválida: {value!r}") from exc
    if math.isnan(number) or math.isinf(number):
        raise ValueError("Métrica numérica precisa ser finita.")
    if minimum is not None and number < minimum:
        raise ValueError(f"Métrica abaixo do mínimo {minimum}: {number}")
    if maximum is not None and number > maximum:
        raise ValueError(f"Métrica acima do máximo {maximum}: {number}")
    return number


def _integer(value: Any, *, minimum: int = 0) -> int | None:
    number = _float(value, minimum=minimum)
    if number is None:
        return None
    if not float(number).is_integer():
        raise ValueError(f"Métrica inteira inválida: {value!r}")
    return int(number)


def _bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"1", "true", "yes", "sim", "on"}:
        return True
    if normalized in {"0", "false", "no", "nao", "não", "off"}:
        return False
    raise ValueError(f"Métrica booleana inválida: {value!r}")


def _creator_receipt(clip: dict) -> dict:
    raw = clip.get("creator_receipt")
    return dict(raw) if isinstance(raw, dict) else {}


def new_performance_ledger(manifest: dict, control_ledger: dict) -> dict:
    """Create a metrics ledger tied to verified publication receipts."""
    validate_manifest(manifest, require_rights=True)
    validate_ledger(control_ledger)
    if str(control_ledger.get("run_id")) != str(manifest.get("run_id")):
        raise RuntimeError("Control ledger e manifesto pertencem a execuções diferentes.")

    clips = {int(clip["index"]): clip for clip in manifest["clips"]}
    batch_sources = {
        str(batch.get("batch_id", "")).strip().upper(): dict(batch.get("source") or {})
        for batch in manifest.get("batches", [])
        if isinstance(batch, dict)
    }
    entries: dict[str, dict] = {}
    for key, publication in control_ledger["entries"].items():
        clip = clips.get(int(publication["index"]))
        if not clip:
            raise RuntimeError(f"Control ledger aponta para corte inexistente: {key}")
        platform = str(publication["platform"]).casefold()
        source = batch_sources.get(str(clip.get("batch_id", "")).strip().upper(), {})
        publication_state = str(publication.get("state") or "")
        publication_verified = publication_state in {
            "PUBLIC", "VERIFIED", "METRICS_PENDING", "MEASURED", "LEARNED"
        }
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
            "source": source,
            "topic": (clip.get("copy") or {}).get("topic", "geral"),
            "publisher_viral_score": (clip.get("copy") or {}).get("viral_score"),
            "creator_receipt": _creator_receipt(clip),
            "duration_seconds": (clip.get("video_profile") or {}).get("duration"),
            "planned_publish_at": clip["schedule"][f"{platform}_publish_at"],
            "publication_state": publication_state,
            "publication_verified": publication_verified,
            "remote_id": publication.get("remote_id"),
            "remote_url": publication.get("remote_url"),
            "remote_reference": publication.get("remote_reference"),
            "snapshots": {},
            "latest_classification": "PENDING",
            "learning_eligible": False,
            "updated_at": _now(),
        }

    if not entries:
        raise RuntimeError("Performance ledger não pode ser inicializado sem publicações.")

    return {
        "version": PERFORMANCE_LEDGER_VERSION,
        "run_id": manifest["run_id"],
        "engine_commit": manifest.get("engine_commit"),
        "created_at": _now(),
        "minimum_distribution_sample": MIN_DISTRIBUTION_SAMPLE,
        "minimum_creator_feedback_samples": MIN_CREATOR_FEEDBACK_SAMPLES,
        "entries": entries,
    }


def sync_publication_receipts(performance_ledger: dict, control_ledger: dict) -> dict:
    """Refresh publication truth before any metrics can influence learning."""
    validate_performance_ledger(performance_ledger)
    validate_ledger(control_ledger)
    if str(performance_ledger.get("run_id")) != str(control_ledger.get("run_id")):
        raise RuntimeError("Performance ledger e control ledger pertencem a execuções diferentes.")
    for key, entry in performance_ledger["entries"].items():
        publication = control_ledger["entries"].get(key)
        if not publication:
            raise RuntimeError(f"Control ledger perdeu a publicação {key}.")
        state = str(publication.get("state") or "")
        entry.update({
            "publication_state": state,
            "publication_verified": state in {
                "PUBLIC", "VERIFIED", "METRICS_PENDING", "MEASURED", "LEARNED"
            },
            "remote_id": publication.get("remote_id"),
            "remote_url": publication.get("remote_url"),
            "remote_reference": publication.get("remote_reference"),
            "updated_at": _now(),
        })
    return performance_ledger


def validate_performance_ledger(ledger: dict) -> None:
    if not isinstance(ledger, dict) or ledger.get("version") != PERFORMANCE_LEDGER_VERSION:
        raise RuntimeError("Performance ledger inválido ou incompatível.")
    entries = ledger.get("entries")
    if not isinstance(entries, dict) or not entries:
        raise RuntimeError("Performance ledger sem publicações.")
    for key, entry in entries.items():
        if not isinstance(entry, dict) or entry.get("publication_key") != key:
            raise RuntimeError(f"Entrada de performance inválida: {key}")
        if entry.get("platform") not in {"youtube", "tiktok"}:
            raise RuntimeError(f"Plataforma inválida no performance ledger: {key}")
        snapshots = entry.get("snapshots")
        if not isinstance(snapshots, dict):
            raise RuntimeError(f"Snapshots inválidos: {key}")
        invalid_horizons = set(snapshots) - set(PERFORMANCE_HORIZONS)
        if invalid_horizons:
            raise RuntimeError(f"Horizontes inválidos em {key}: {sorted(invalid_horizons)}")


def _normalized_metrics(platform: str, raw: dict) -> dict:
    common = {
        "views": _integer(raw.get("views")),
        "likes": _integer(raw.get("likes")),
        "comments": _integer(raw.get("comments")),
        "shares": _integer(raw.get("shares")),
    }
    if platform == "youtube":
        metrics = {
            **common,
            "shown_in_feed": _integer(raw.get("shown_in_feed")),
            "viewed_rate": _float(raw.get("viewed_rate"), minimum=0, maximum=100),
            "avg_view_duration_seconds": _float(raw.get("avg_view_duration_seconds"), minimum=0),
            "avg_percentage_viewed": _float(raw.get("avg_percentage_viewed"), minimum=0, maximum=500),
            "subscribers_gained": _integer(raw.get("subscribers_gained")),
            "restrictions": str(raw.get("restrictions") or "").strip(),
        }
    else:
        metrics = {
            **common,
            "reach": _integer(raw.get("reach")),
            "for_you_pct": _float(raw.get("for_you_pct"), minimum=0, maximum=100),
            "avg_watch_time_seconds": _float(raw.get("avg_watch_time_seconds"), minimum=0),
            "full_watch_rate": _float(raw.get("full_watch_rate"), minimum=0, maximum=100),
            "fyp_eligible": _bool(raw.get("fyp_eligible")),
            "originality_notice": str(raw.get("originality_notice") or "").strip(),
            "account_status": str(raw.get("account_status") or "").strip(),
        }
    return {key: value for key, value in metrics.items() if value is not None and value != ""}


def _distribution_exposure(platform: str, metrics: dict) -> int | None:
    if platform == "youtube":
        value = metrics.get("shown_in_feed")
    else:
        value = metrics.get("reach")
        if value is None:
            value = metrics.get("views")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _classification(platform: str, horizon: str, metrics: dict) -> tuple[str, bool]:
    if platform == "youtube" and str(metrics.get("restrictions") or "").strip().casefold() not in {
        "", "none", "nenhuma", "sem restricoes", "sem restrições"
    }:
        return "PLATFORM_RESTRICTED", False
    if platform == "tiktok":
        if metrics.get("fyp_eligible") is False:
            return "FYP_INELIGIBLE", False
        if str(metrics.get("originality_notice") or "").strip():
            return "ORIGINALITY_NOTICE", False

    if horizon not in LEARNING_HORIZONS:
        return "EARLY_SIGNAL", False

    exposure = _distribution_exposure(platform, metrics)
    if exposure is None:
        return "MISSING_DISTRIBUTION_SIGNAL", False
    if exposure < MIN_DISTRIBUTION_SAMPLE:
        return "INSUFFICIENT_DISTRIBUTION", False
    return "LEARNING_ELIGIBLE", True


def record_performance_snapshot(
    ledger: dict,
    key: str,
    *,
    horizon: str,
    metrics: dict,
) -> dict:
    validate_performance_ledger(ledger)
    horizon = str(horizon or "").strip().casefold()
    if horizon not in PERFORMANCE_HORIZONS:
        raise ValueError(f"Horizonte inválido: {horizon!r}. Use 1h, 6h, 24h ou 72h.")
    entry = ledger["entries"].get(key)
    if not entry:
        raise KeyError(f"Publicação desconhecida: {key}")
    if not entry.get("publication_verified"):
        raise RuntimeError(
            "Métricas não podem treinar o Creator antes da publicação estar PUBLIC/VERIFIED."
        )
    normalized = _normalized_metrics(str(entry["platform"]), dict(metrics or {}))
    classification, learning_eligible = _classification(
        str(entry["platform"]), horizon, normalized
    )
    entry["snapshots"][horizon] = {
        "horizon": horizon,
        "captured_at": _now(),
        "metrics": normalized,
        "classification": classification,
        "learning_eligible": learning_eligible,
    }
    entry["latest_classification"] = classification
    if horizon in LEARNING_HORIZONS:
        entry["learning_eligible"] = learning_eligible
    entry["updated_at"] = _now()
    return ledger


def _best_learning_snapshot(entry: dict) -> dict | None:
    snapshots = entry.get("snapshots") or {}
    # The newest mature snapshot is authoritative. A later restriction,
    # originality notice or distribution failure must invalidate an earlier
    # eligible 24h snapshot instead of silently falling back to it.
    for horizon in ("72h", "24h"):
        snapshot = snapshots.get(horizon)
        if isinstance(snapshot, dict):
            return snapshot if snapshot.get("learning_eligible") else None
    return None


def _ratio_per_1000(numerator: Any, denominator: Any) -> float | None:
    try:
        num = float(numerator)
        den = float(denominator)
    except (TypeError, ValueError):
        return None
    if den <= 0:
        return None
    return num / den * 1000.0


def _youtube_outcome(entry: dict, snapshot: dict) -> dict | None:
    metrics = snapshot.get("metrics") or {}
    viewed = _float(metrics.get("viewed_rate"), minimum=0, maximum=100)
    retention = _float(metrics.get("avg_percentage_viewed"), minimum=0, maximum=500)
    duration = _float(entry.get("duration_seconds"), minimum=0)
    if retention is None and duration and metrics.get("avg_view_duration_seconds") is not None:
        avd = _float(metrics.get("avg_view_duration_seconds"), minimum=0)
        if avd is not None:
            retention = avd / duration * 100.0
    if viewed is None and retention is None:
        return None
    views = metrics.get("views")
    return {
        "viewed_rate": viewed,
        "retention": retention,
        "shares_per_1k": _ratio_per_1000(metrics.get("shares"), views),
        "comments_per_1k": _ratio_per_1000(metrics.get("comments"), views),
    }


def _median(values: list[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return round(statistics.median(valid), 3) if valid else None


def _bounded_delta(group: dict, baseline: dict) -> float:
    adjustment = 0.0
    if group.get("viewed_rate") is not None and baseline.get("viewed_rate") is not None:
        adjustment += max(-0.8, min(0.8, (group["viewed_rate"] - baseline["viewed_rate"]) / 12.0))
    if group.get("retention") is not None and baseline.get("retention") is not None:
        adjustment += max(-0.9, min(0.9, (group["retention"] - baseline["retention"]) / 18.0))
    if group.get("shares_per_1k") is not None and baseline.get("shares_per_1k") is not None:
        adjustment += max(-0.3, min(0.3, (group["shares_per_1k"] - baseline["shares_per_1k"]) / 8.0))
    return round(max(-MAX_TRIGGER_ADJUSTMENT, min(MAX_TRIGGER_ADJUSTMENT, adjustment)), 2)


def new_learning_history() -> dict:
    return {
        "version": LEARNING_HISTORY_VERSION,
        "updated_at": _now(),
        "entries": {},
    }


def validate_learning_history(history: dict) -> None:
    if not isinstance(history, dict) or history.get("version") != LEARNING_HISTORY_VERSION:
        raise RuntimeError("Histórico de aprendizado inválido ou incompatível.")
    entries = history.get("entries")
    if not isinstance(entries, dict):
        raise RuntimeError("Histórico de aprendizado sem mapa de entradas.")


def merge_performance_into_history(history: dict, ledger: dict) -> dict:
    """Accumulate mature YouTube outcomes across runs without duplicate training."""
    validate_learning_history(history)
    validate_performance_ledger(ledger)
    for entry in ledger["entries"].values():
        if entry.get("platform") != "youtube":
            continue
        snapshots = entry.get("snapshots") or {}
        mature = None
        for horizon in ("72h", "24h"):
            candidate = snapshots.get(horizon)
            if isinstance(candidate, dict):
                mature = candidate
                break
        if mature is None:
            continue
        outcome = _youtube_outcome(entry, mature) if mature.get("learning_eligible") else None
        history["entries"][entry["publication_key"]] = {
            "publication_key": entry["publication_key"],
            "run_id": entry.get("run_id"),
            "source": dict(entry.get("source") or {}),
            "topic": entry.get("topic", "geral"),
            "duration_seconds": entry.get("duration_seconds"),
            "creator_receipt": dict(entry.get("creator_receipt") or {}),
            "snapshot_horizon": mature.get("horizon"),
            "captured_at": mature.get("captured_at"),
            "classification": mature.get("classification"),
            "learning_eligible": bool(mature.get("learning_eligible")),
            "outcome": outcome,
        }
    history["updated_at"] = _now()
    return history


def _feedback_rows_from_history(history: dict) -> list[dict]:
    validate_learning_history(history)
    rows: list[dict] = []
    for entry in history["entries"].values():
        if not entry.get("learning_eligible"):
            continue
        outcome = entry.get("outcome")
        if not isinstance(outcome, dict):
            continue
        creator = entry.get("creator_receipt") or {}
        rows.append({
            "publication_key": entry["publication_key"],
            "trigger": str(creator.get("trigger") or "").strip(),
            "source": (entry.get("source") or {}).get("name", ""),
            "topic": entry.get("topic", "geral"),
            "duration_seconds": entry.get("duration_seconds"),
            **outcome,
        })
    return rows


def creator_feedback(source: dict) -> dict:
    """Summarize verified YouTube outcomes into conservative Creator priors.

    Accepts either a single-run performance ledger or the cumulative private
    learning history. The profile is advisory until enough learning-eligible
    YouTube publications exist across runs.
    """
    if source.get("version") == LEARNING_HISTORY_VERSION and all(
        isinstance(item, dict) and "snapshots" not in item
        for item in (source.get("entries") or {}).values()
    ):
        rows = _feedback_rows_from_history(source)
    else:
        validate_performance_ledger(source)
        rows = []
        for entry in source["entries"].values():
            if entry.get("platform") != "youtube":
                continue
            snapshot = _best_learning_snapshot(entry)
            if not snapshot:
                continue
            outcome = _youtube_outcome(entry, snapshot)
            if not outcome:
                continue
            creator = entry.get("creator_receipt") or {}
            trigger = str(creator.get("trigger") or "").strip()
            rows.append({
                "publication_key": entry["publication_key"],
                "trigger": trigger,
                "source": (entry.get("source") or {}).get("name", ""),
                "topic": entry.get("topic", "geral"),
                "duration_seconds": entry.get("duration_seconds"),
                **outcome,
            })

    baseline = {
        "viewed_rate": _median([row["viewed_rate"] for row in rows]),
        "retention": _median([row["retention"] for row in rows]),
        "shares_per_1k": _median([row["shares_per_1k"] for row in rows]),
        "comments_per_1k": _median([row["comments_per_1k"] for row in rows]),
    }
    trigger_groups: dict[str, list[dict]] = {}
    for row in rows:
        if row["trigger"]:
            trigger_groups.setdefault(row["trigger"], []).append(row)

    trigger_priors = {}
    ready = len(rows) >= MIN_CREATOR_FEEDBACK_SAMPLES
    for trigger, group_rows in sorted(trigger_groups.items()):
        summary = {
            "sample_count": len(group_rows),
            "viewed_rate": _median([row["viewed_rate"] for row in group_rows]),
            "retention": _median([row["retention"] for row in group_rows]),
            "shares_per_1k": _median([row["shares_per_1k"] for row in group_rows]),
            "comments_per_1k": _median([row["comments_per_1k"] for row in group_rows]),
        }
        usable = ready and len(group_rows) >= MIN_TRIGGER_SAMPLES
        summary["score_adjustment"] = _bounded_delta(summary, baseline) if usable else 0.0
        summary["active"] = usable
        trigger_priors[trigger] = summary

    return {
        "version": 1,
        "generated_at": _now(),
        "source": "publisher_performance_ledger",
        "status": "READY" if ready else "INSUFFICIENT_DATA",
        "advisory_until_samples": MIN_CREATOR_FEEDBACK_SAMPLES,
        "eligible_youtube_samples": len(rows),
        "minimum_trigger_samples": MIN_TRIGGER_SAMPLES,
        "max_trigger_adjustment": MAX_TRIGGER_ADJUSTMENT,
        "baseline": baseline,
        "trigger_priors": trigger_priors,
        "guardrails": {
            "distribution_failures_excluded": True,
            "restricted_posts_excluded": True,
            "minimum_distribution_sample": MIN_DISTRIBUTION_SAMPLE,
            "auto_adjustment_is_bounded_tiebreaker": True,
        },
    }


def load_performance_ledger(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_performance_ledger(data)
    return data


def save_performance_ledger(path: Path, ledger: dict) -> None:
    validate_performance_ledger(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
