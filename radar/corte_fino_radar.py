from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=BR"
STATE_SCHEMA_VERSION = 2
DEFAULT_STATE_FILE = ROOT / "state" / "history.json"
CHAPTER_RE = re.compile(
    r"(?m)^\s*(?:(?P<h>\d{1,2}):)?(?P<m>\d{1,2}):(?P<s>\d{2})"
    r"\s*(?:[-–—:|]\s*)?(?P<title>[^\n]{2,160})$"
)

DEFAULT_THEMES = [
    "bets apostas vício influenciadores",
    "relacionamento traição casamento",
    "feminismo masculinidade red pill relacionamento",
    "religião fé igreja debate",
    "crime segurança facção polícia",
    "dinheiro golpe fraude investimento",
    "inteligência artificial emprego futuro",
    "saúde mental depressão ansiedade",
    "família pais filhos educação",
    "carros elétricos dinheiro desvalorização",
    "celebridades bastidores polêmica",
    "ciência mistério espaço humanidade",
]

SOURCE_QUERIES = [
    "Flow Podcast",
    "Inteligência Ltda",
    "RedCast",
    "Podpah",
    "AchismosTV",
    "Jota Jota Podcast",
]

PREFERRED_SOURCE_PATTERNS = [
    "flow podcast",
    "cortes do flow",
    "inteligência ltda",
    "inteligencia ltda",
    "cortes do inteligência [oficial]",
    "cortes do inteligencia [oficial]",
    "redcast",
    "redcast [oficial]",
    "podpah",
    "podpah tv",
    "pânico",
    "panico",
    "venus podcast",
    "fala ordinário",
    "fala ordinario",
    "achismostv",
    "jota jota podcast",
    "primo cast",
    "primocast",
    "os economistas",
    "cortes do podpah",
]

LONGFORM_MARKERS = {
    "podcast", "entrevista", "debate", "sabatina", "talk show", "talkshow",
    "papo", "conversa", "mesa", "episódio", "episodio", "especial",
    "react", "reação", "reacao", "ao vivo",
}

PORTUGUESE_SIGNAL_WORDS = {
    "que", "não", "nao", "para", "com", "uma", "como", "mais", "isso", "sobre",
    "porque", "por", "dos", "das", "ele", "ela", "você", "voce", "brasil",
    "brasileiro", "brasileira", "hoje", "agora", "aqui", "também", "tambem",
}

CONTROVERSY_TERMS = {
    "absurdo", "polêmica", "polemica", "treta", "briga", "denúncia", "denuncia",
    "acusação", "acusacao", "acusou", "expõe", "expoe", "exposto", "mentira",
    "verdade", "proibido", "censura", "golpe", "fraude", "escândalo", "escandalo",
    "traição", "traicao", "humilhação", "humilhacao", "racismo", "machismo",
    "feminismo", "red pill", "cancelado", "cancelamento", "processo", "justiça",
    "justica", "crime", "facção", "faccao", "vício", "vicio", "aposta", "bets",
    "idolatria", "ateu", "religião", "religiao", "igreja", "sexo", "aborto",
}

EMOTION_TERMS = {
    "medo", "raiva", "vergonha", "choro", "chorou", "chorei", "luto", "morte",
    "morreu", "família", "familia", "filho", "filha", "pai", "mãe", "mae",
    "trauma", "dor", "sofrimento", "depressão", "depressao", "ansiedade", "vício",
    "vicio", "perdi", "perda", "superação", "superacao", "fé", "fe", "amor",
    "ódio", "odio", "humilhação", "humilhacao", "desespero", "destruiu",
}

COMMENT_HEAT_TERMS = {
    "absurdo", "ridículo", "ridiculo", "vergonha", "mentira", "verdade", "concordo",
    "discordo", "errado", "errada", "certo", "correto", "lixo", "genial", "hipócrita",
    "hipocrita", "nojento", "covarde", "brabo", "monstro", "finalmente", "nunca",
    "sempre", "kkkk", "chorei", "medo", "triste", "revoltante", "revoltado",
}

COMMENT_SUPPORT_TERMS = {
    "concordo", "verdade", "correto", "certo", "finalmente", "falou tudo",
    "é isso", "e isso", "perfeito", "brabo",
}

COMMENT_REJECT_TERMS = {
    "discordo", "mentira", "errado", "errada", "absurdo", "ridículo", "ridiculo",
    "vergonha", "hipócrita", "hipocrita", "lixo", "nojento",
}

# Conteúdo político/eleitoral fica numa watchlist factual sem score editorial.
POLITICAL_STRONG_TERMS = {
    "eleição", "eleicoes", "eleições", "segundo turno", "stf", "tse", "lula",
    "bolsonaro", "flávio bolsonaro", "flavio bolsonaro", "nikolas", "mbl",
    "pt", "pl", "psol",
}

POLITICAL_CONTEXT_TERMS = {
    "presidente", "candidato", "candidata", "campanha", "governo", "congresso",
    "senado", "deputado", "deputada", "prefeito", "prefeita", "governador",
    "governadora", "ministro", "ministra",
}

POLITICAL_DOMAIN_TERMS = {
    "política", "politica", "eleitoral", "partido", "partidos", "voto", "votos",
    "urna", "urnas", "mandato", "coalizão", "coalizao",
}

HIGH_RISK_CLAIM_TERMS = {
    "pedófilo", "pedofilo", "estuprador", "assassino", "criminoso", "ladrão", "ladrao",
    "golpista", "corrupto", "fraudou", "roubou", "matou", "abuso", "assédio", "assedio",
}

ISO_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


@dataclass
class Trend:
    topic: str
    rank: int
    approx_traffic: int = 0


@dataclass
class QuerySignal:
    query: str
    source: str
    trend_rank: int | None = None
    approx_traffic: int = 0
    youtube_total_results: int = 0
    gap_score: float = 0.0


@dataclass
class Chapter:
    seconds: int
    title: str
    heat_score: float = 0.0


@dataclass
class VideoCandidate:
    video_id: str
    title: str
    channel_title: str
    channel_id: str
    category_id: str
    made_for_kids: bool
    published_at: str
    description: str
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    youtube_license: str
    source_queries: list[str] = field(default_factory=list)
    query_signals: list[QuerySignal] = field(default_factory=list)
    preferred_source: bool = False
    political_or_electoral: bool = False
    risk_flags: list[str] = field(default_factory=list)
    sampled_comments: int = 0
    sampled_replies: int = 0
    comment_heat_score: float = 0.0
    relevant_comment_heat: float = 0.0
    recent_comment_heat: float = 0.0
    comment_divergence: bool = False
    chapters: list[Chapter] = field(default_factory=list)
    chapter_heat_score: float = 0.0
    best_chapter: str = ""
    cutability_score: float = 0.0
    views_per_hour: float = 0.0
    recent_views_per_hour: float = 0.0
    recent_comments_per_hour: float = 0.0
    momentum_score: float = 50.0
    momentum_state: str = "NEW"
    momentum_ratio: float = 1.0
    acceleration_ratio: float = 1.0
    history_points: int = 0
    channel_baseline_vph: float = 0.0
    breakout_ratio: float = 1.0
    breakout_score: float = 50.0
    comment_rate_per_1k: float = 0.0
    like_rate_per_1k: float = 0.0
    freshness_score: float = 0.0
    velocity_score: float = 0.0
    engagement_score: float = 0.0
    controversy_score: float = 0.0
    emotion_score: float = 0.0
    search_gap_score: float = 0.0
    source_score: float = 0.0
    confidence_score: float = 0.0
    rank_status: str = "DROP"
    radar_score: float | None = None
    rights_status: str = "manual_review"
    rights_note: str = "Licença/autorização de reutilização precisa ser verificada antes de usar o vídeo."

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip().lower()


def term_hits(text: str, terms: Iterable[str]) -> int:
    norm = normalize(text)
    hits = 0
    for term in terms:
        if " " in term or len(term) >= 4:
            matched = term in norm
        else:
            matched = bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", norm))
        hits += int(matched)
    return hits


def parse_iso8601_duration(value: str) -> int:
    match = ISO_DURATION_RE.match(value or "")
    if not match:
        return 0
    parts = {k: int(v or 0) for k, v in match.groupdict().items()}
    return (
        parts["days"] * 86400
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )


def parse_traffic(value: str) -> int:
    text = (value or "").upper().replace("+", "").replace(",", "").strip()
    if not text:
        return 0
    multiplier = 1
    if text.endswith("K"):
        multiplier, text = 1_000, text[:-1]
    elif text.endswith("M"):
        multiplier, text = 1_000_000, text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        digits = re.sub(r"\D", "", text)
        return int(digits or 0)


def parse_datetime(value: str) -> datetime:
    text = (value or "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc) - timedelta(days=3650)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def safe_url_label(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return "<endpoint>"


def fetch_bytes(url: str, *, timeout: int = 20, retries: int = 3) -> bytes:
    last_error_type = "network_error"
    headers = {
        "User-Agent": "CorteFinoRadar/2.0",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error_type = type(exc).__name__
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(
        f"Falha ao acessar {safe_url_label(url)} ({last_error_type})"
    )


def fetch_json(base_url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return json.loads(fetch_bytes(f"{base_url}?{query}").decode("utf-8"))


def fetch_google_trends(limit: int) -> list[Trend]:
    try:
        root = ET.fromstring(fetch_bytes(GOOGLE_TRENDS_RSS))
    except Exception as exc:
        print(f"[WARN] Google Trends indisponível: {exc}", file=sys.stderr)
        return []

    trends: list[Trend] = []
    for rank, item in enumerate(root.findall(".//item"), 1):
        title = (item.findtext("title") or "").strip()
        traffic = 0
        for child in list(item):
            if child.tag.lower().endswith("approx_traffic"):
                traffic = parse_traffic(child.text or "")
                break
        if title:
            trends.append(Trend(topic=title, rank=rank, approx_traffic=traffic))
        if len(trends) >= limit:
            break
    return trends


def youtube_search(
    api_key: str,
    query: str,
    published_after: str,
    max_results: int = 25,
    order: str = "relevance",
) -> tuple[list[str], int]:
    payload = fetch_json(
        f"{YOUTUBE_API}/search",
        {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "order": order,
            "regionCode": "BR",
            "relevanceLanguage": "pt",
            "safeSearch": "moderate",
            "videoDuration": "long",
            "publishedAfter": published_after,
            "key": api_key,
        },
    )
    ids = [
        item.get("id", {}).get("videoId", "")
        for item in payload.get("items", [])
        if item.get("id", {}).get("videoId")
    ]
    return ids, int(payload.get("pageInfo", {}).get("totalResults") or 0)


def youtube_video_details(
    api_key: str,
    video_ids: list[str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(video_ids), 50):
        payload = fetch_json(
            f"{YOUTUBE_API}/videos",
            {
                "part": "snippet,statistics,contentDetails,status",
                "id": ",".join(video_ids[start:start + 50]),
                "key": api_key,
            },
        )
        for item in payload.get("items", []):
            result[item["id"]] = item
    return result


def youtube_comments(
    api_key: str,
    video_id: str,
    max_results: int = 25,
    order: str = "relevance",
) -> tuple[list[str], int]:
    try:
        payload = fetch_json(
            f"{YOUTUBE_API}/commentThreads",
            {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": max_results,
                "order": order,
                "textFormat": "plainText",
                "key": api_key,
            },
        )
    except Exception as exc:
        print(
            f"[WARN] Comentários indisponíveis para {video_id} ({order}): {exc}",
            file=sys.stderr,
        )
        return [], 0

    comments: list[str] = []
    replies = 0
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        top = snippet.get("topLevelComment", {}).get("snippet", {})
        text = top.get("textDisplay") or top.get("textOriginal") or ""
        if text:
            comments.append(str(text))
        replies += int(snippet.get("totalReplyCount") or 0)
    return comments, replies


def preferred_source(channel_title: str) -> bool:
    return normalize(channel_title) in PREFERRED_SOURCE_PATTERNS


def term_present(norm: str, term: str) -> bool:
    if " " in term or len(term) >= 4:
        return term in norm
    return bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", norm))


def is_political(
    title: str,
    description: str = "",
    channel_title: str = "",
) -> bool:
    headline = normalize(f"{title} {channel_title}")
    body = normalize(description)

    if any(term_present(headline, term) for term in POLITICAL_STRONG_TERMS):
        return True
    if any(
        term_present(body, term)
        for term in POLITICAL_STRONG_TERMS
        if len(term) > 3 or " " in term
    ):
        return True

    headline_context = sum(
        term_present(headline, term)
        for term in POLITICAL_CONTEXT_TERMS
    )
    body_context = sum(
        term_present(body, term)
        for term in POLITICAL_CONTEXT_TERMS
    )
    body_domain = any(
        term_present(body, term)
        for term in POLITICAL_DOMAIN_TERMS
    )
    return headline_context >= 1 or (
        body_context >= 2 and body_domain
    )


def likely_portuguese(text: str) -> bool:
    norm = normalize(text)
    tokens = re.findall(r"[a-záàâãéêíóôõúç]+", norm)
    if not tokens:
        return False
    hits = sum(token in PORTUGUESE_SIGNAL_WORDS for token in tokens[:120])
    accented = sum(
        any(char in token for char in "áàâãéêíóôõúç")
        for token in tokens[:120]
    )
    return hits >= 2 or accented >= 2


def editorial_format_fit(
    title: str,
    description: str,
    channel_title: str,
) -> bool:
    if preferred_source(channel_title):
        return True
    surface = normalize(f"{title} {channel_title}")
    if any(marker in surface for marker in LONGFORM_MARKERS):
        return True
    # Descrição é evidência mais fraca: exige dois marcadores para evitar
    # orações, novelas narradas e compilações que só citam "podcast".
    body = normalize(description[:1200])
    marker_hits = sum(marker in body for marker in LONGFORM_MARKERS)
    return marker_hits >= 2


def parse_chapters(description: str) -> list[Chapter]:
    chapters: list[Chapter] = []
    last_seconds = -1
    for match in CHAPTER_RE.finditer(description or ""):
        hours = int(match.group("h") or 0)
        minutes = int(match.group("m") or 0)
        seconds = int(match.group("s") or 0)
        total = hours * 3600 + minutes * 60 + seconds
        if minutes >= 60 or seconds >= 60 or total <= last_seconds:
            continue
        title = match.group("title").strip(" -–—:|")
        heat = clamp(
            term_hits(title, CONTROVERSY_TERMS) * 28
            + term_hits(title, EMOTION_TERMS) * 24
        )
        chapters.append(Chapter(total, title, heat))
        last_seconds = total
    return chapters if len(chapters) >= 2 else []


def base_cutability(candidate: VideoCandidate) -> float:
    score = 22.0
    if candidate.preferred_source:
        score += 18
    if candidate.duration_seconds >= 30 * 60:
        score += 8
    if candidate.duration_seconds >= 60 * 60:
        score += 4
    if candidate.chapters:
        score += min(24, len(candidate.chapters) * 3)
        score += candidate.chapter_heat_score * 0.20
    title_norm = normalize(candidate.title)
    if any(
        marker in title_norm
        for marker in {"debate", "entrevista", "podcast", "papo", "conversa", "especial"}
    ):
        score += 8
    if candidate.made_for_kids or any(
        term in title_norm for term in {" kids", "infantil", "para crianças", "para criancas"}
    ):
        score -= 45
    return clamp(score)


def load_state(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {"schema_version": STATE_SCHEMA_VERSION, "videos": {}}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("estado inválido")
        data.setdefault("videos", {})
        return data
    except Exception as exc:
        print(f"[WARN] Histórico ignorado: {type(exc).__name__}", file=sys.stderr)
        return {"schema_version": STATE_SCHEMA_VERSION, "videos": {}}


def apply_momentum(
    candidates: list[VideoCandidate],
    state: dict[str, Any],
    now: datetime,
) -> None:
    videos = state.get("videos", {})
    for candidate in candidates:
        points = list(videos.get(candidate.video_id, []))[-12:]
        candidate.history_points = len(points)
        if not points:
            candidate.momentum_state = "NEW"
            candidate.momentum_score = 50.0
            continue

        last = points[-1]
        last_ts = parse_datetime(str(last.get("ts") or ""))
        delta_hours = (now - last_ts).total_seconds() / 3600
        if delta_hours < 0.20 or delta_hours > 72:
            candidate.momentum_state = "STALE"
            candidate.momentum_score = 50.0
            continue

        delta_views = max(0, candidate.view_count - int(last.get("views") or 0))
        delta_comments = max(
            0,
            candidate.comment_count - int(last.get("comments") or 0),
        )
        candidate.recent_views_per_hour = delta_views / max(delta_hours, 0.01)
        candidate.recent_comments_per_hour = delta_comments / max(delta_hours, 0.01)
        candidate.momentum_ratio = (
            candidate.recent_views_per_hour / max(candidate.views_per_hour, 1.0)
        )

        acceleration = 1.0
        if len(points) >= 2:
            prev = points[-2]
            prev_ts = parse_datetime(str(prev.get("ts") or ""))
            prev_hours = (last_ts - prev_ts).total_seconds() / 3600
            if prev_hours >= 0.20:
                prev_vph = (
                    max(0, int(last.get("views") or 0) - int(prev.get("views") or 0))
                    / prev_hours
                )
                acceleration = (
                    candidate.recent_views_per_hour / max(prev_vph, 1.0)
                )
        candidate.acceleration_ratio = acceleration

        ratio_component = clamp(
            50 + 24 * math.log2(max(0.20, candidate.momentum_ratio)),
            15,
            90,
        )
        acceleration_component = clamp(
            50 + 18 * math.log2(max(0.25, acceleration)),
            20,
            90,
        )
        comment_component = clamp(
            20 + 18 * math.log1p(candidate.recent_comments_per_hour),
            20,
            90,
        )
        candidate.momentum_score = clamp(
            ratio_component * 0.50
            + acceleration_component * 0.30
            + comment_component * 0.20
        )

        if acceleration >= 1.35 or candidate.momentum_ratio >= 1.55:
            candidate.momentum_state = "ACCELERATING"
        elif candidate.momentum_ratio >= 1.15:
            candidate.momentum_state = "RISING"
        elif candidate.momentum_ratio <= 0.65:
            candidate.momentum_state = "COOLING"
        else:
            candidate.momentum_state = "STEADY"


def apply_channel_baselines(candidates: list[VideoCandidate]) -> None:
    groups: dict[str, list[VideoCandidate]] = {}
    for candidate in candidates:
        key = candidate.channel_id or normalize(candidate.channel_title)
        groups.setdefault(key, []).append(candidate)

    for group in groups.values():
        for candidate in group:
            peers = [
                peer.views_per_hour
                for peer in group
                if peer.video_id != candidate.video_id and peer.views_per_hour > 0
            ]
            if len(peers) < 2:
                candidate.breakout_score = 50.0
                candidate.breakout_ratio = 1.0
                continue
            baseline = statistics.median(peers)
            candidate.channel_baseline_vph = baseline
            candidate.breakout_ratio = candidate.views_per_hour / max(baseline, 1.0)
            candidate.breakout_score = clamp(
                50 + 28 * math.log2(max(0.20, candidate.breakout_ratio)),
                10,
                100,
            )


def update_state(
    path: Path,
    state: dict[str, Any],
    candidates: list[VideoCandidate],
    now: datetime,
) -> None:
    videos = state.setdefault("videos", {})
    now_iso = now.isoformat()
    seen_ids: set[str] = set()
    for candidate in candidates:
        seen_ids.add(candidate.video_id)
        points = list(videos.get(candidate.video_id, []))
        points.append(
            {
                "ts": now_iso,
                "views": candidate.view_count,
                "comments": candidate.comment_count,
                "likes": candidate.like_count,
            }
        )
        videos[candidate.video_id] = points[-12:]

    cutoff = now - timedelta(days=30)
    for video_id in list(videos):
        points = videos.get(video_id) or []
        if not points:
            videos.pop(video_id, None)
            continue
        if parse_datetime(str(points[-1].get("ts") or "")) < cutoff:
            videos.pop(video_id, None)

    state["schema_version"] = STATE_SCHEMA_VERSION
    state["updated_at"] = now_iso
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def risk_flags(text: str) -> list[str]:
    norm = normalize(text)
    flags: list[str] = []
    if any(term in norm for term in HIGH_RISK_CLAIM_TERMS):
        flags.append("allegation_or_serious_claim")
    if any(
        term in norm
        for term in {"suicídio", "suicidio", "morte", "assassinato", "estupro"}
    ):
        flags.append("sensitive_harm_or_death")
    if any(
        term in norm
        for term in {"criança", "crianca", "menor", "adolescente", " kids", "infantil"}
    ):
        flags.append("minor_related")
    return flags


def query_gap_score(signal: QuerySignal) -> float:
    if signal.approx_traffic > 0:
        demand = clamp(20 + 18 * math.log10(max(10, signal.approx_traffic)))
    elif signal.trend_rank:
        demand = clamp(105 - signal.trend_rank * 5)
    elif signal.source == "preferred_source":
        demand = 45.0
    else:
        demand = 35.0

    supply = max(0, signal.youtube_total_results)
    saturation = (
        0.0
        if supply <= 0
        else clamp(100 * math.log1p(supply) / math.log1p(1_000_000))
    )
    return clamp(demand - saturation * 0.55)


def comment_analysis(
    comments: list[str],
    reply_count: int,
) -> tuple[float, bool]:
    if not comments:
        return 0.0, False

    hot = support = reject = 0
    for comment in comments:
        norm = normalize(comment)
        hot += int(any(term in norm for term in COMMENT_HEAT_TERMS))
        support += int(any(term in norm for term in COMMENT_SUPPORT_TERMS))
        reject += int(any(term in norm for term in COMMENT_REJECT_TERMS))

    hot_ratio = hot / len(comments)
    reply_component = clamp(
        (reply_count / max(1, len(comments))) * 25,
        0,
        35,
    )
    heat = clamp(hot_ratio * 75 + reply_component)
    divergence = support > 0 and reject > 0
    if divergence:
        heat = clamp(heat + 10)
    return heat, divergence


def compute_base_metrics(
    candidate: VideoCandidate,
    now: datetime,
) -> None:
    age_hours = max(
        1.0,
        (now - parse_datetime(candidate.published_at)).total_seconds() / 3600,
    )
    candidate.views_per_hour = candidate.view_count / age_hours
    candidate.comment_rate_per_1k = (
        candidate.comment_count / max(1, candidate.view_count)
    ) * 1000
    candidate.like_rate_per_1k = (
        candidate.like_count / max(1, candidate.view_count)
    ) * 1000

    candidate.freshness_score = clamp(
        100 * math.exp(-age_hours / (24 * 4.5))
    )
    candidate.velocity_score = clamp(
        100
        * math.log1p(candidate.views_per_hour)
        / math.log1p(20_000)
    )
    comment_density = clamp(candidate.comment_rate_per_1k / 18 * 100)
    like_density = clamp(candidate.like_rate_per_1k / 80 * 100)
    candidate.engagement_score = clamp(
        comment_density * 0.65 + like_density * 0.35
    )

    text = f"{candidate.title} {candidate.description}"
    candidate.controversy_score = clamp(
        term_hits(text, CONTROVERSY_TERMS) * 18
    )
    candidate.emotion_score = clamp(
        term_hits(text, EMOTION_TERMS) * 16
    )
    candidate.search_gap_score = max(
        [
            signal.gap_score
            for signal in candidate.query_signals
            if signal.source != "preferred_source"
        ]
        or [0.0]
    )
    candidate.source_score = 100.0 if candidate.preferred_source else 25.0

    candidate.chapters = parse_chapters(candidate.description)
    candidate.chapter_heat_score = max(
        [chapter.heat_score for chapter in candidate.chapters] or [0.0]
    )
    if candidate.chapters and candidate.chapter_heat_score > 0:
        best = max(candidate.chapters, key=lambda chapter: chapter.heat_score)
        candidate.best_chapter = (
            f"{fmt_duration(best.seconds)} — {best.title}"
        )
    candidate.cutability_score = base_cutability(candidate)

    if candidate.youtube_license == "creativeCommon":
        candidate.rights_status = "youtube_creative_commons"
        candidate.rights_note = (
            "O vídeo está marcado pela API do YouTube como Creative Commons; "
            "cumpra os termos e a atribuição aplicáveis."
        )


def score_contributions(candidate: VideoCandidate) -> dict[str, float]:
    return {
        "momentum": candidate.momentum_score * 0.18,
        "velocidade": candidate.velocity_score * 0.12,
        "breakout": candidate.breakout_score * 0.12,
        "engajamento": candidate.engagement_score * 0.10,
        "comentários": candidate.comment_heat_score * 0.14,
        "polêmica": candidate.controversy_score * 0.09,
        "emoção": candidate.emotion_score * 0.08,
        "cutability": candidate.cutability_score * 0.10,
        "search gap": candidate.search_gap_score * 0.03,
        "freshness": candidate.freshness_score * 0.02,
        "fonte": candidate.source_score * 0.02,
    }


def compute_confidence(candidate: VideoCandidate) -> float:
    score = 15.0
    if candidate.history_points >= 1:
        score += 20
    if candidate.channel_baseline_vph > 0:
        score += 15
    if candidate.sampled_comments >= 20:
        score += 20
    if candidate.chapters:
        score += 15
    if candidate.preferred_source:
        score += 10
    age_hours = (
        datetime.now(timezone.utc) - parse_datetime(candidate.published_at)
    ).total_seconds() / 3600
    if age_hours >= 3:
        score += 5
    return clamp(score)


def finalize_score(candidate: VideoCandidate) -> None:
    if candidate.political_or_electoral:
        candidate.radar_score = None
        candidate.rank_status = "POLITICAL_WATCHLIST"
        return
    if candidate.made_for_kids:
        candidate.radar_score = None
        candidate.rank_status = "DROP"
        return

    editorial_signal = max(
        candidate.controversy_score,
        candidate.emotion_score,
        candidate.comment_heat_score,
        candidate.chapter_heat_score,
    )
    if editorial_signal < 20:
        candidate.radar_score = None
        candidate.rank_status = "DROP"
        return

    if candidate.comment_divergence:
        candidate.cutability_score = clamp(candidate.cutability_score + 8)

    contributions = score_contributions(candidate)
    score = sum(contributions.values())
    if len(candidate.source_queries) >= 2:
        score += min(4.0, 1.25 * (len(candidate.source_queries) - 1))
    candidate.radar_score = round(clamp(score), 2)
    candidate.confidence_score = round(compute_confidence(candidate), 2)

    if candidate.radar_score >= 68:
        candidate.rank_status = "HOT"
    elif candidate.radar_score >= 57:
        candidate.rank_status = "PROMISING"
    elif candidate.radar_score >= 47:
        candidate.rank_status = "WATCH"
    else:
        candidate.rank_status = "DROP"


def candidate_from_item(
    video_id: str,
    item: dict[str, Any],
    signals: list[QuerySignal],
) -> VideoCandidate:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})
    status = item.get("status", {})

    title = str(snippet.get("title") or "")
    description = str(snippet.get("description") or "")
    channel = str(snippet.get("channelTitle") or "")
    combined = f"{title} {description} {channel}"

    return VideoCandidate(
        video_id=video_id,
        title=title,
        channel_title=channel,
        channel_id=str(snippet.get("channelId") or ""),
        category_id=str(snippet.get("categoryId") or ""),
        made_for_kids=bool(status.get("madeForKids") or False),
        published_at=str(snippet.get("publishedAt") or ""),
        description=description,
        duration_seconds=parse_iso8601_duration(
            str(details.get("duration") or "")
        ),
        view_count=int(stats.get("viewCount") or 0),
        like_count=int(stats.get("likeCount") or 0),
        comment_count=int(stats.get("commentCount") or 0),
        youtube_license=str(status.get("license") or "youtube"),
        source_queries=sorted({s.query for s in signals}),
        query_signals=signals,
        preferred_source=preferred_source(channel),
        political_or_electoral=is_political(
            title,
            description,
            channel,
        ),
        risk_flags=risk_flags(combined),
    )


def build_queries(
    trends: list[Trend],
    extra_topics: list[str],
    max_queries: int,
    theme_offset: int = 0,
) -> list[tuple[str, str, Trend | None]]:
    queries: list[tuple[str, str, Trend | None]] = []
    queries.extend(
        (trend.topic, "google_trends", trend)
        for trend in trends
    )
    queries.extend(
        (source, "preferred_source", None)
        for source in SOURCE_QUERIES
    )
    queries.extend(
        (topic.strip(), "manual_extra", None)
        for topic in extra_topics[:3]
        if topic.strip()
    )
    if DEFAULT_THEMES:
        offset = theme_offset % len(DEFAULT_THEMES)
        rotated_themes = DEFAULT_THEMES[offset:] + DEFAULT_THEMES[:offset]
    else:
        rotated_themes = []
    queries.extend(
        (theme, "editorial_theme", None)
        for theme in rotated_themes
    )

    deduped: list[tuple[str, str, Trend | None]] = []
    seen: set[str] = set()
    for query in queries:
        key = normalize(query[0])
        if key and key not in seen:
            deduped.append(query)
            seen.add(key)
        if len(deduped) >= max_queries:
            break
    return deduped


def collect_candidates(
    api_key: str,
    *,
    days: int,
    trend_limit: int,
    max_queries: int,
    extra_topics: list[str],
    state_file: Path,
) -> tuple[list[VideoCandidate], list[Trend], list[QuerySignal]]:
    now = datetime.now(timezone.utc)
    published_after = (
        now - timedelta(days=days)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

    trends = fetch_google_trends(trend_limit)
    state = load_state(state_file)
    theme_offset = int(now.timestamp() // (6 * 3600)) % max(1, len(DEFAULT_THEMES))
    queries = build_queries(
        trends,
        extra_topics,
        max_queries,
        theme_offset=theme_offset,
    )

    video_signals: dict[str, list[QuerySignal]] = {}
    all_signals: list[QuerySignal] = []

    for index, (query, source, trend) in enumerate(queries, 1):
        print(f"[RADAR] Busca {index}/{len(queries)} ({source})")
        try:
            ids, total = youtube_search(
                api_key,
                query,
                published_after,
                order="date" if source == "preferred_source" else "relevance",
            )
        except Exception as exc:
            print(
                f"[WARN] Busca {index}/{len(queries)} ({source}) falhou: {exc}",
                file=sys.stderr,
            )
            continue

        signal = QuerySignal(
            query=query,
            source=source,
            trend_rank=trend.rank if trend else None,
            approx_traffic=trend.approx_traffic if trend else 0,
            youtube_total_results=total,
        )
        signal.gap_score = round(query_gap_score(signal), 2)
        all_signals.append(signal)

        for video_id in ids:
            video_signals.setdefault(video_id, []).append(signal)

    if not video_signals:
        return [], trends, all_signals

    details = youtube_video_details(
        api_key,
        list(video_signals),
    )

    candidates: list[VideoCandidate] = []
    for video_id, signals in video_signals.items():
        item = details.get(video_id)
        if not item:
            continue

        candidate = candidate_from_item(
            video_id,
            item,
            signals,
        )
        if candidate.duration_seconds < 20 * 60:
            continue

        compute_base_metrics(candidate, now)

        language_text = (
            f"{candidate.title} {candidate.description[:500]}"
        )
        if (
            not candidate.preferred_source
            and not likely_portuguese(language_text)
        ):
            continue
        if not editorial_format_fit(
            candidate.title,
            candidate.description,
            candidate.channel_title,
        ):
            continue

        title_norm = normalize(candidate.title)
        if candidate.made_for_kids or any(
            term in title_norm
            for term in {" kids", "infantil", "para crianças", "para criancas"}
        ):
            continue

        candidates.append(candidate)

    apply_channel_baselines(candidates)
    apply_momentum(candidates, state, now)

    pre_ranked = sorted(
        [
            c
            for c in candidates
            if not c.political_or_electoral
        ],
        key=lambda c: (
            c.momentum_score * 0.24
            + c.breakout_score * 0.18
            + c.velocity_score * 0.18
            + c.engagement_score * 0.12
            + c.controversy_score * 0.10
            + c.emotion_score * 0.08
            + c.cutability_score * 0.10
        ),
        reverse=True,
    )

    for candidate in pre_ranked[:min(24, len(pre_ranked))]:
        relevant, relevant_replies = youtube_comments(
            api_key,
            candidate.video_id,
            25,
            order="relevance",
        )
        recent, recent_replies = youtube_comments(
            api_key,
            candidate.video_id,
            25,
            order="time",
        )
        relevant_heat, relevant_divergence = comment_analysis(
            relevant,
            relevant_replies,
        )
        recent_heat, recent_divergence = comment_analysis(
            recent,
            recent_replies,
        )
        unique_comments = {
            normalize(comment)
            for comment in relevant + recent
            if normalize(comment)
        }
        candidate.sampled_comments = len(unique_comments)
        candidate.sampled_replies = relevant_replies + recent_replies
        candidate.relevant_comment_heat = relevant_heat
        candidate.recent_comment_heat = recent_heat
        candidate.comment_heat_score = clamp(
            recent_heat * 0.60 + relevant_heat * 0.40
        )
        candidate.comment_divergence = (
            recent_divergence or relevant_divergence
        )

    for candidate in candidates:
        finalize_score(candidate)

    update_state(state_file, state, candidates, now)
    return candidates, trends, all_signals


def fmt_int(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_duration(seconds: int) -> str:
    h, rem = divmod(max(0, seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def explain(candidate: VideoCandidate) -> list[str]:
    contributions = score_contributions(candidate)
    labels = {
        "momentum": f"momentum {candidate.momentum_state.lower()}",
        "velocidade": f"velocidade média {candidate.views_per_hour:,.0f}/h".replace(",", "."),
        "breakout": f"breakout {candidate.breakout_ratio:.1f}× vs. canal",
        "engajamento": "densidade de comentários/likes",
        "comentários": "comentários com reação/divergência",
        "polêmica": "conflito/polêmica",
        "emoção": "carga emocional",
        "cutability": "boa estrutura para cortes",
        "search gap": "demanda/saturação favorável",
        "freshness": "publicação recente",
        "fonte": "fonte editorial reconhecida",
    }
    return [
        labels[name]
        for name, contribution in sorted(
            contributions.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
        if contribution > 0
    ]


def write_outputs(
    candidates: list[VideoCandidate],
    trends: list[Trend],
    query_signals: list[QuerySignal],
    *,
    top_n: int,
    generated_at: datetime,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = sorted(
        [
            c
            for c in candidates
            if c.radar_score is not None and c.rank_status != "DROP"
        ],
        key=lambda c: c.radar_score or 0,
        reverse=True,
    )[:top_n]

    political = sorted(
        [
            c
            for c in candidates
            if c.political_or_electoral
        ],
        key=lambda c: parse_datetime(c.published_at),
        reverse=True,
    )[:top_n]

    qualified_queries = {
        query
        for candidate in candidates
        if candidate.radar_score is not None and candidate.rank_status != "DROP"
        for query in candidate.source_queries
    }
    gap_signals = sorted(
        [
            signal
            for signal in query_signals
            if (
                signal.source != "preferred_source"
                and signal.query in qualified_queries
            )
        ],
        key=lambda s: s.gap_score,
        reverse=True,
    )[:top_n]

    payload = {
        "schema_version": 2,
        "generated_at_utc": generated_at.isoformat(),
        "method": {
            "ranking_scope": "non-political content only",
            "political_content": (
                "raw factual watchlist without editorial score "
                "or recommendation"
            ),
            "rights": (
                "YouTube license metadata is recorded; reuse authorization "
                "is never inferred from channel identity."
            ),
        },
        "trends": [
            asdict(t)
            for t in trends
        ],
        "search_gaps": [
            asdict(s)
            for s in gap_signals
        ],
        "ranked_nonpolitical": [
            asdict(c)
            | {
                "url": c.url,
                "reasons": explain(c),
            }
            for c in ranked
        ],
        "political_watchlist_raw": [
            asdict(c)
            | {
                "url": c.url,
            }
            for c in political
        ],
    }

    (
        OUTPUT_DIR / "radar_latest.json"
    ).write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with (
        OUTPUT_DIR / "radar_latest.csv"
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "score",
            "title",
            "channel",
            "url",
            "published_at",
            "duration",
            "views",
            "views_per_hour",
            "recent_views_per_hour",
            "momentum_state",
            "momentum_score",
            "breakout_ratio",
            "breakout_score",
            "cutability_score",
            "confidence_score",
            "rank_status",
            "comments",
            "comment_rate_per_1k",
            "comment_heat",
            "recent_comment_heat",
            "relevant_comment_heat",
            "search_gap",
            "preferred_source",
            "youtube_license",
            "rights_status",
            "risk_flags",
        ])
        for c in ranked:
            writer.writerow([
                c.radar_score,
                c.title,
                c.channel_title,
                c.url,
                c.published_at,
                fmt_duration(c.duration_seconds),
                c.view_count,
                round(c.views_per_hour, 2),
                round(c.recent_views_per_hour, 2),
                c.momentum_state,
                round(c.momentum_score, 2),
                round(c.breakout_ratio, 3),
                round(c.breakout_score, 2),
                round(c.cutability_score, 2),
                round(c.confidence_score, 2),
                c.rank_status,
                c.comment_count,
                round(c.comment_rate_per_1k, 3),
                round(c.comment_heat_score, 2),
                round(c.recent_comment_heat, 2),
                round(c.relevant_comment_heat, 2),
                round(c.search_gap_score, 2),
                c.preferred_source,
                c.youtube_license,
                c.rights_status,
                ",".join(c.risk_flags),
            ])

    lines = [
        "# 🎯 Corte Fino — Radar Viral V2",
        "",
        (
            "Atualizado em "
            f"**{generated_at.strftime('%d/%m/%Y %H:%M UTC')}**."
        ),
        "",
        (
            "Ranking técnico/editorial apenas para "
            "**conteúdo não político**."
        ),
        "",
        "## 🔥 Oportunidades priorizadas",
        "",
    ]

    if not ranked:
        lines.append(
            "_Nenhuma oportunidade não política nesta rodada._"
        )

    for index, c in enumerate(ranked, 1):
        reason = (
            "; ".join(explain(c))
            or "sinais combinados de desempenho"
        )
        risk = (
            f" | ⚠️ {', '.join(c.risk_flags)}"
            if c.risk_flags
            else ""
        )
        license_note = (
            "CC"
            if c.youtube_license == "creativeCommon"
            else "licença padrão"
        )
        lines.extend([
            (
                f"{index}. **{c.title}** — "
                f"{c.channel_title}  "
            ),
            (
                f"   **{c.rank_status}** | Score **{c.radar_score:.1f}/100** | "
                f"confiança {c.confidence_score:.0f}/100 | "
                f"{fmt_int(c.view_count)} views | "
                f"{c.views_per_hour:,.0f} views/h médio | "
                f"momentum {c.momentum_state} ({c.momentum_score:.0f}) | "
                f"breakout {c.breakout_ratio:.1f}× | "
                f"cutability {c.cutability_score:.0f} | "
                f"{fmt_int(c.comment_count)} comentários | "
                f"{fmt_duration(c.duration_seconds)} | "
                f"{license_note}{risk}  "
            ),
            f"   Por quê: {reason}.  ",
            (
                f"   Melhor capítulo: {c.best_chapter}  "
                if c.best_chapter else ""
            ),
            f"   {c.url}",
            "",
        ])

    lines.extend([
        "## 🔎 Hipóteses de Search Gap",
        "",
    ])

    for signal in gap_signals[:8]:
        trend = (
            f" | tendência #{signal.trend_rank}"
            if signal.trend_rank
            else ""
        )
        traffic = (
            f" | tráfego ~{fmt_int(signal.approx_traffic)}"
            if signal.approx_traffic
            else ""
        )
        lines.append(
            f"- **{signal.query}** — "
            f"gap {signal.gap_score:.1f}/100"
            f"{trend}{traffic} | "
            "oferta YouTube "
            f"~{fmt_int(signal.youtube_total_results)} resultados."
        )

    lines.extend([
        "",
        "## 🗳️ Watchlist política/eleitoral — métricas brutas",
        "",
        (
            "Sem score e sem recomendação comparativa "
            "de candidatos ou políticos."
        ),
        "",
    ])

    if not political:
        lines.append(
            "_Nenhum item político/eleitoral nesta rodada._"
        )

    for c in political:
        lines.extend([
            (
                f"- **{c.title}** — {c.channel_title} | "
                f"{fmt_int(c.view_count)} views | "
                f"{fmt_int(c.comment_count)} comentários | "
                f"publicado {c.published_at[:10]}  "
            ),
            f"  {c.url}",
        ])

    lines.extend([
        "",
        "## ⚠️ Regras de uso",
        "",
        (
            "- O radar **não baixa, corta nem publica** nada; "
            "Motor 1 e Publisher continuam independentes."
        ),
        (
            "- Canal preferido não significa autorização. "
            "Verifique licença/autorização antes de reutilizar."
        ),
        (
            "- Alegações graves e temas sensíveis recebem flag "
            "para exigir contexto e atribuição."
        ),
        (
            "- Search Gap automático usa Google Trends + oferta recente "
            "do YouTube como proxy; Creator Search Insights do TikTok "
            "não é consumido diretamente."
        ),
        (
            "- Momentum usa snapshots entre rodadas; na primeira aparição "
            "o vídeo recebe estado NEW e confiança menor."
        ),
        (
            "- O score considera breakout relativo ao próprio canal quando "
            "há amostra suficiente de vídeos recentes."
        ),
    ])

    (
        OUTPUT_DIR / "radar_latest.md"
    ).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corte Fino Radar Viral"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.environ.get("RADAR_DAYS", "7")),
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=int(os.environ.get("RADAR_TOP_N", "12")),
    )
    parser.add_argument(
        "--trend-limit",
        type=int,
        default=int(os.environ.get("RADAR_TREND_LIMIT", "8")),
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=int(os.environ.get("RADAR_MAX_QUERIES", "24")),
    )
    parser.add_argument(
        "--extra-topics",
        default=os.environ.get("RADAR_EXTRA_TOPICS", ""),
    )
    parser.add_argument(
        "--state-file",
        default=os.environ.get(
            "RADAR_STATE_FILE",
            str(DEFAULT_STATE_FILE),
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.environ.get(
        "YOUTUBE_API_KEY",
        "",
    ).strip()
    if not api_key:
        print(
            (
                "YOUTUBE_API_KEY ausente. Crie uma API key do "
                "YouTube Data API v3 e salve como secret "
                "YOUTUBE_API_KEY."
            ),
            file=sys.stderr,
        )
        return 2

    extra_topics = [
        item.strip()
        for item in re.split(
            r"[,;\n]+",
            args.extra_topics,
        )
        if item.strip()
    ]

    generated_at = datetime.now(timezone.utc)

    candidates, trends, signals = collect_candidates(
        api_key,
        days=max(
            1,
            min(args.days, 14),
        ),
        trend_limit=max(
            0,
            min(args.trend_limit, 20),
        ),
        max_queries=max(
            1,
            min(args.max_queries, 30),
        ),
        extra_topics=extra_topics,
        state_file=Path(args.state_file),
    )

    write_outputs(
        candidates,
        trends,
        signals,
        top_n=max(
            1,
            min(args.top_n, 25),
        ),
        generated_at=generated_at,
    )

    print(
        f"[RADAR] {len(candidates)} vídeos qualificados."
    )
    print(
        f"[RADAR] Relatório: {OUTPUT_DIR / 'radar_latest.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
