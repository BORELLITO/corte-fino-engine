from __future__ import annotations

from datetime import datetime, timezone

from publisher.core import TIKTOK_CAPTION_LIMIT, TIMEZONE, truncate_utf8
from publisher.google_io import scheduled_publish_at


class TikTokError(RuntimeError):
    """Erro de validação do pacote TikTok browser-only."""


PUBLIC_TIKTOK_VISIBILITY = "PUBLIC_TO_EVERYONE"


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def choose_privacy_level(creator: dict, desired: str | None = None) -> str:
    """Keep the old pure helper for callers that inspect Studio options."""
    options = [str(option) for option in creator.get("privacy_level_options", [])]
    desired = desired or "PUBLIC_TO_EVERYONE"
    if desired not in options:
        raise TikTokError(
            f"Privacidade TikTok indisponível: {desired}. Opções retornadas: {', '.join(options) or 'nenhuma'}"
        )
    return desired


def validate_browser_visibility(visibility: str) -> str:
    """Require the public audience before any browser scheduling step."""
    normalized = str(visibility or "").strip().upper()
    if normalized != PUBLIC_TIKTOK_VISIBILITY:
        raise TikTokError(
            "TikTok precisa estar com audiência pública: selecione Todos antes de agendar."
        )
    return PUBLIC_TIKTOK_VISIBILITY


def _due_clips(manifest: dict, now: datetime | None = None) -> list[dict]:
    current = now or datetime.now(TIMEZONE)
    current_utc = (
        current.astimezone(timezone.utc)
        if current.tzinfo
        else current.replace(tzinfo=TIMEZONE).astimezone(timezone.utc)
    )
    eligible = [
        clip
        for clip in manifest["clips"]
        if (_parse_utc(scheduled_publish_at(manifest, clip, "tiktok")) or datetime.max.replace(tzinfo=timezone.utc))
        <= current_utc
    ]
    return sorted(eligible, key=lambda item: (scheduled_publish_at(manifest, item, "tiktok"), item["index"]))


def publish_tiktok(
    manifest: dict,
    dry_run: bool = False,
    due_only: bool = False,
    now: datetime | None = None,
    allow_immediate: bool = False,
) -> list[dict]:
    """Return a local preview; real posting is performed in TikTok Studio."""
    del allow_immediate
    if not dry_run:
        raise TikTokError(
            "Publicação TikTok por API removida: o fluxo oficial usa o Cloud Web Browser no TikTok Studio."
        )
    clips = _due_clips(manifest, now) if due_only else sorted(manifest["clips"], key=lambda item: item["index"])
    if due_only:
        clips = clips[:1]
    return [
        {
            "index": clip["index"],
            "status": "dry_run",
            "publish_at": scheduled_publish_at(manifest, clip, "tiktok"),
            "caption": truncate_utf8(clip["copy"]["tiktok_caption"], TIKTOK_CAPTION_LIMIT),
            "visibility": PUBLIC_TIKTOK_VISIBILITY,
            "privacy_check": "required",
        }
        for clip in clips
    ]
