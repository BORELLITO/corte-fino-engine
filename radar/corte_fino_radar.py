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
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=BR"
STATE_SCHEMA_VERSION = 3
REPORT_TOP_N = 5
RADAR_VERSION = "V2.5"
TRANSCRIPT_PROBE_LIMIT = 12
REPEAT_COOLDOWN_HOURS = 48
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
    "react", "reação", "reacao",
}

NON_EDITORIAL_CATEGORY_IDS = {"10", "17", "20"}
NON_CONVERSATIONAL_TERMS = {
    "novela", "novelas", "noveleiro", "capítulo de novela", "capitulo de novela",
    "resumo da novela", "trama da novela", "fofoca de novela",
}
SPANISH_SIGNAL_WORDS = {
    "el", "la", "los", "las", "y", "ya", "mujer", "mujeres",
    "matrimonio", "infidelidad", "relaciones", "moderna", "modernas",
    "funciona", "casan", "casarse", "conveniencia", "sin", "rodeo",
}
ENGLISH_SIGNAL_WORDS = {
    "the", "and", "with", "from", "this", "that", "live", "watch",
    "party", "teaching", "apostolic", "followed", "man", "video",
}
EDITORIAL_TENSION_TERMS = {
    "debate", "briga", "treta", "muito sério", "muito seria", "sem reação",
    "intervenção", "exorcista", "terra plana", "demitido", "demitida",
    "escândalo", "escandalo", "traição", "traicao", "denúncia", "denuncia",
    "humilhação", "humilhacao", "revoltante", "catastrófico", "catastrofico",
}
FOREIGN_SIGNAL_WORDS = {
    "las", "los", "una", "uno", "del", "the", "and", "with",
    "from", "this", "that", "muerte", "fuera", "dice", "ilusión",
    "ilusion", "calles", "salvador", "lo",
}
SPORTS_TERMS = {
    "futebol", "futebol", "brasileirão", "brasileirao", "flamengo",
    "corinthians", "palmeiras", "vasco", "grêmio", "gremio", "nba",
    "nfl", "champions", "liga", "rodada", "jogo", "partida", "gol",
    "torino", "udinese",
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

RELEVANCE_TERMS = {
    "bets", "aposta", "vício", "vicio", "relacionamento", "traição",
    "traicao", "casamento", "divórcio", "divorcio", "família", "familia",
    "filho", "filha", "pai", "mãe", "mae", "medo", "morte", "luto",
    "trauma", "dor", "sofrimento", "fé", "fe", "religião", "religiao",
    "igreja", "crime", "segurança", "seguranca", "dinheiro", "golpe",
    "fraude", "polêmica", "polemica", "debate", "feminismo", "masculinidade",
    "red pill", "saúde mental", "saude mental", "inteligência artificial",
    "inteligencia artificial", "emprego", "futuro", "aborto", "sexo",
    "humilhação", "humilhacao", "superação", "superacao", "revolta",
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
    transcript_status: str = "not_checked"
    transcript_language: str = ""
    transcript_chars: int = 0
    transcript_word_count: int = 0
    transcript_heat_score: float = 0.0
    transcript_segment_score: float = 0.0
    best_segment_start: int | None = None
    best_segment_end: int | None = None
    best_segment_excerpt: str = ""
    recently_seen: bool = False
    topic_fit_score: float = 0.0
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
    review_priority_score: float = 0.0
    previous_score: float | None = None
    score_delta: float | None = None
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


def fetch_transcript_rows(
    video_id: str,
) -> tuple[str, str, list[dict[str, Any]]]:
    """Busca legendas públicas em português sem tornar a legenda obrigatória."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except Exception:
        return "dependency_missing", "", []

    try:
        fetched = YouTubeTranscriptApi().fetch(
            video_id,
            languages=["pt-BR", "pt", "pt-PT"],
        )
        language = str(getattr(fetched, "language_code", "") or "")
        raw_rows = getattr(fetched, "snippets", None)
        if raw_rows is None:
            raw_rows = fetched

        rows: list[dict[str, Any]] = []
        for item in raw_rows:
            if isinstance(item, dict):
                text = str(item.get("text") or "")
                start = float(item.get("start") or 0)
                duration = float(item.get("duration") or 0)
            else:
                text = str(getattr(item, "text", "") or "")
                start = float(getattr(item, "start", 0) or 0)
                duration = float(getattr(item, "duration", 0) or 0)
            if text.strip():
                rows.append({
                    "text": text.strip(),
                    "start": max(0.0, start),
                    "duration": max(0.0, duration),
                })

        if not rows:
            return "empty", language, []
        return "available", language, rows
    except Exception:
        return "unavailable", "", []


def analyze_transcript(
    candidate: VideoCandidate,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        return

    full_text = " ".join(str(row["text"]) for row in rows)
    candidate.transcript_chars = len(full_text)
    candidate.transcript_word_count = len(
        re.findall(r"\b[\wÀ-ÿ']+\b", full_text)
    )
    candidate.transcript_heat_score = clamp(
        term_hits(full_text, CONTROVERSY_TERMS) * 8
        + term_hits(full_text, EMOTION_TERMS) * 9
        + term_hits(full_text, COMMENT_HEAT_TERMS) * 2
    )

    best: tuple[float, int, int, str] | None = None
    for start_index in range(len(rows)):
        start = float(rows[start_index]["start"])
        parts: list[str] = []
        end = start
        for end_index in range(start_index, min(len(rows), start_index + 90)):
            row = rows[end_index]
            parts.append(str(row["text"]))
            end = max(
                end,
                float(row["start"]) + float(row["duration"]),
            )
            window_seconds = end - start
            if window_seconds > 105:
                break
            if window_seconds < 60:
                continue

            text = " ".join(parts)
            sentence_count = len(re.findall(r"[.!?](?:\s|$)", text))
            connective_count = term_hits(
                text,
                {
                    "mas", "porém", "porque", "então", "aí",
                    "só que", "por isso", "no final", "a verdade",
                },
            )
            score = clamp(
                term_hits(text, CONTROVERSY_TERMS) * 14
                + term_hits(text, EMOTION_TERMS) * 13
                + min(18, sentence_count * 3)
                + min(14, connective_count * 3)
            )
            if sentence_count >= 3:
                score = clamp(score + 8)
            if any(
                marker in normalize(text[-260:])
                for marker in {"por isso", "no final", "a verdade", "é isso"}
            ):
                score = clamp(score + 8)

            candidate_window = (
                score,
                int(start),
                int(end),
                normalize(text)[:280],
            )
            if best is None or candidate_window[0] > best[0]:
                best = candidate_window

    if best is not None:
        score, start, end, excerpt = best
        candidate.transcript_segment_score = round(score, 2)
        candidate.best_segment_start = start
        candidate.best_segment_end = end
        candidate.best_segment_excerpt = excerpt


def probe_transcripts(candidates: list[VideoCandidate]) -> None:
    for candidate in candidates[:TRANSCRIPT_PROBE_LIMIT]:
        status, language, rows = fetch_transcript_rows(candidate.video_id)
        candidate.transcript_status = status
        candidate.transcript_language = language
        if rows:
            analyze_transcript(candidate, rows)


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
    headline_domain = any(
        term_present(headline, term)
        for term in POLITICAL_DOMAIN_TERMS
    )
    return (
        headline_context >= 2
        or (
            headline_context >= 1
            and (body_domain or headline_domain)
        )
        or (body_context >= 2 and body_domain)
    )


def likely_portuguese(text: str) -> bool:
    norm = normalize(text)
    tokens = re.findall(r"[a-záàâãéêíóôõúç]+", norm)
    if not tokens:
        return False
    sample = tokens[:120]
    hits = sum(token in PORTUGUESE_SIGNAL_WORDS for token in sample)
    foreign_hits = sum(token in FOREIGN_SIGNAL_WORDS for token in sample)
    spanish_hits = sum(token in SPANISH_SIGNAL_WORDS for token in sample)
    english_hits = sum(token in ENGLISH_SIGNAL_WORDS for token in sample)
    accented = sum(
        any(char in token for char in "áàâãéêíóôõúç")
        for token in sample
    )
    # Dois sinais estrangeiros já bastam quando não há acentuação portuguesa.
    # Para espanhol/inglês, múltiplos marcadores próprios e pouca evidência
    # de português bloqueiam ruído de idioma sem penalizar um debate brasileiro
    # cujo título cita um termo estrangeiro.
    if foreign_hits >= 2 and accented < 2:
        return False
    if spanish_hits >= 3 and hits <= 1:
        return False
    if english_hits >= 3 and hits <= 1 and accented == 0:
        return False
    return hits >= 2 or accented >= 2


def editorial_format_fit(
    title: str,
    description: str,
    channel_title: str,
    category_id: str = "",
) -> bool:
    if category_id in NON_EDITORIAL_CATEGORY_IDS:
        return False
    surface = normalize(f"{title} {channel_title}")
    if any(term in surface for term in NON_CONVERSATIONAL_TERMS):
        return False
    if preferred_source(channel_title):
        return True
    if "ao vivo" in surface and not any(
        marker in surface
        for marker in {
            "podcast", "entrevista", "debate", "sabatina",
            "conversa", "papo", "mesa",
        }
    ):
        return False
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


def mark_recent_repeats(
    candidates: list[VideoCandidate],
    state: dict[str, Any],
    now: datetime,
) -> None:
    videos = state.get("videos", {})
    for candidate in candidates:
        points = list(videos.get(candidate.video_id, []))
        if not points:
            continue
        last_ts = parse_datetime(str(points[-1].get("ts") or ""))
        age_hours = (now - last_ts).total_seconds() / 3600
        if 0 <= age_hours <= REPEAT_COOLDOWN_HOURS:
            candidate.recently_seen = True
            if "repeat_cooldown" not in candidate.risk_flags:
                candidate.risk_flags.append("repeat_cooldown")


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
        if last.get("score") is not None:
            try:
                candidate.previous_score = float(last.get("score"))
            except (TypeError, ValueError):
                candidate.previous_score = None
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
                "score": candidate.radar_score,
                "status": candidate.rank_status,
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
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


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
    candidate.topic_fit_score = clamp(
        term_hits(text, RELEVANCE_TERMS) * 14
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
        "momentum": candidate.momentum_score * 0.16,
        "velocidade": candidate.velocity_score * 0.10,
        "breakout": candidate.breakout_score * 0.10,
        "engajamento": candidate.engagement_score * 0.08,
        "comentários": candidate.comment_heat_score * 0.12,
        "polêmica": candidate.controversy_score * 0.08,
        "emoção": candidate.emotion_score * 0.08,
        "cutability": candidate.cutability_score * 0.10,
        "segmento": candidate.transcript_segment_score * 0.10,
        "search gap": candidate.search_gap_score * 0.03,
        "freshness": candidate.freshness_score * 0.02,
        "fonte": candidate.source_score * 0.03,
    }


def fallback_score(candidate: VideoCandidate) -> float:
    """Score observacional usado apenas para preencher o Top 5."""
    contributions = score_contributions(candidate)
    score = sum(contributions.values())
    if len(candidate.source_queries) >= 2:
        score += min(4.0, 1.25 * (len(candidate.source_queries) - 1))
    score += min(8.0, candidate.topic_fit_score * 0.08)
    return round(clamp(score), 2)


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
    if candidate.transcript_status == "available":
        score += 10
    if candidate.transcript_segment_score >= 35:
        score += 10
    age_hours = (
        datetime.now(timezone.utc) - parse_datetime(candidate.published_at)
    ).total_seconds() / 3600
    if age_hours >= 3:
        score += 5
    return clamp(score)


def compute_review_priority(candidate: VideoCandidate) -> float:
    """Prioridade operacional de revisão; não é recomendação editorial."""
    return round(clamp(
        candidate.velocity_score * 0.35
        + candidate.engagement_score * 0.15
        + candidate.comment_heat_score * 0.20
        + candidate.freshness_score * 0.15
        + candidate.confidence_score * 0.15
    ), 2)


def finalize_score(candidate: VideoCandidate) -> None:
    if candidate.made_for_kids:
        candidate.radar_score = None
        candidate.rank_status = "DROP"
        return

    if candidate.political_or_electoral:
        candidate.confidence_score = round(compute_confidence(candidate), 2)
        candidate.review_priority_score = compute_review_priority(candidate)
        candidate.radar_score = None
        candidate.rank_status = "POLITICAL_REVIEW"
        return

    semantic_signal = max(
        candidate.controversy_score,
        candidate.emotion_score,
        candidate.chapter_heat_score,
        candidate.transcript_heat_score,
        candidate.transcript_segment_score,
    )
    organic_conflict = (
        candidate.comment_heat_score >= 35
        and candidate.comment_divergence
    )
    tension_hits = term_hits(candidate.title, EDITORIAL_TENSION_TERMS)
    performance_signal = (
        candidate.breakout_ratio >= 2.0
        or candidate.momentum_score >= 65
        or candidate.comment_rate_per_1k >= 10
    )
    editorial_breakout = tension_hits >= 1 and performance_signal
    if (
        semantic_signal < 16
        and candidate.topic_fit_score < 28
        and not organic_conflict
        and not editorial_breakout
    ):
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
    if candidate.previous_score is not None:
        candidate.score_delta = round(
            candidate.radar_score - candidate.previous_score,
            2,
        )

    if candidate.political_or_electoral:
        candidate.rank_status = "POLITICAL_REVIEW"
    elif candidate.radar_score >= 68:
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
    diagnostics: dict[str, Any] = {
        "queries_requested": len(queries),
        "queries_attempted": 0,
        "queries_succeeded": 0,
        "queries_failed": 0,
        "failed_queries": [],
    }

    for index, (query, source, trend) in enumerate(queries, 1):
        diagnostics["queries_attempted"] += 1
        print(f"[RADAR] Busca {index}/{len(queries)} ({source})")
        try:
            ids, total = youtube_search(
                api_key,
                query,
                published_after,
                order="date",
            )
        except Exception as exc:
            diagnostics["queries_failed"] += 1
            diagnostics["failed_queries"].append({
                "query": query,
                "source": source,
                "error": type(exc).__name__,
            })
            print(
                f"[WARN] Busca {index}/{len(queries)} ({source}) falhou: {exc}",
                file=sys.stderr,
            )
            continue

        diagnostics["queries_succeeded"] += 1
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

    diagnostics["raw_video_ids"] = len(video_signals)
    if not video_signals:
        diagnostics["candidates_after_filters"] = 0
        return [], trends, all_signals, state, diagnostics

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
            candidate.category_id,
        ):
            continue

        title_norm = normalize(candidate.title)
        if candidate.category_id in NON_EDITORIAL_CATEGORY_IDS:
            continue
        if any(term in title_norm for term in SPORTS_TERMS):
            continue
        if candidate.made_for_kids or any(
            term in title_norm
            for term in {" kids", "infantil", "para crianças", "para criancas"}
        ):
            continue

        candidates.append(candidate)

    diagnostics["candidates_after_filters"] = len(candidates)
    apply_channel_baselines(candidates)
    apply_momentum(candidates, state, now)
    mark_recent_repeats(candidates, state, now)

    pre_ranked = sorted(
        [
            c
            for c in candidates
            if not c.political_or_electoral
            and not c.recently_seen
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

    if not pre_ranked:
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

    probe_transcripts(pre_ranked)
    diagnostics["transcript_probe_requested"] = min(
        TRANSCRIPT_PROBE_LIMIT,
        len(pre_ranked),
    )
    diagnostics["transcripts_available"] = sum(
        candidate.transcript_status == "available"
        for candidate in pre_ranked
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

    diagnostics["comment_probe_candidates"] = min(24, len(pre_ranked))
    diagnostics["qualified_candidates"] = sum(
        candidate.radar_score is not None
        and candidate.rank_status != "DROP"
        and not candidate.political_or_electoral
        and not candidate.recently_seen
        for candidate in candidates
    )
    return candidates, trends, all_signals, state, diagnostics


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
        "segmento": "segmento com começo-meio-fim e carga emocional",
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
    diagnostics: dict[str, Any] | None = None,
) -> None:
    if top_n != REPORT_TOP_N:
        raise ValueError(f"Top N fixo em {REPORT_TOP_N}; recebido {top_n}.")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    qualified = sorted(
        [
            c
            for c in candidates
            if (
                not c.political_or_electoral
                and not c.made_for_kids
                and not c.recently_seen
                and c.radar_score is not None
                and c.rank_status != "DROP"
            )
        ],
        key=lambda c: c.radar_score or 0,
        reverse=True,
    )
    qualified_ids = {c.video_id for c in qualified}

    # O usuário exige sempre uma entrega Top 5. Os aprovados permanecem
    # primeiro; as vagas restantes são preenchidas com observações transparentes.
    fallback_pool: list[VideoCandidate] = []
    for candidate in candidates:
        if (
            candidate.political_or_electoral
            or candidate.made_for_kids
            or candidate.recently_seen
            or candidate.video_id in qualified_ids
            or candidate.rank_status == "DROP"
        ):
            continue
        if candidate.radar_score is None:
            candidate.radar_score = fallback_score(candidate)
            candidate.confidence_score = round(compute_confidence(candidate), 2)
        candidate.rank_status = "REVIEW"
        fallback_pool.append(candidate)

    fallback_pool.sort(
        key=lambda c: c.radar_score or 0,
        reverse=True,
    )

    repeat_pool = []
    for candidate in candidates:
        if (
            candidate.political_or_electoral
            or candidate.made_for_kids
            or not candidate.recently_seen
            or candidate.video_id in qualified_ids
            or candidate.rank_status == "DROP"
        ):
            continue
        if candidate.radar_score is None:
            candidate.radar_score = fallback_score(candidate)
            candidate.confidence_score = round(compute_confidence(candidate), 2)
        candidate.rank_status = "REVIEW"
        repeat_pool.append(candidate)

    repeat_pool.sort(
        key=lambda c: c.radar_score or 0,
        reverse=True,
    )

    # Se ainda faltarem vagas, entregamos cinco links, mas marcamos claramente
    # os candidatos que falharam no gate semântico como baixa confiança.
    low_signal_pool = []
    for candidate in candidates:
        if (
            candidate.political_or_electoral
            or candidate.made_for_kids
            or candidate.video_id in qualified_ids
            or candidate.rank_status != "DROP"
        ):
            continue
        if candidate.radar_score is None:
            candidate.radar_score = fallback_score(candidate)
            candidate.confidence_score = round(compute_confidence(candidate), 2)
        candidate.rank_status = "REVIEW"
        if "low_signal_backfill" not in candidate.risk_flags:
            candidate.risk_flags.append("low_signal_backfill")
        low_signal_pool.append(candidate)

    low_signal_pool.sort(
        key=lambda c: c.radar_score or 0,
        reverse=True,
    )
    ranked = (
        qualified
        + fallback_pool
        + repeat_pool
        + low_signal_pool
    )[:top_n]
    fallback_ids = {
        c.video_id
        for c in ranked
        if c.video_id in {item.video_id for item in fallback_pool}
    }
    repeat_ids = {
        c.video_id
        for c in ranked
        if c.video_id in {item.video_id for item in repeat_pool}
    }
    low_signal_ids = {
        c.video_id
        for c in ranked
        if c.video_id in {item.video_id for item in low_signal_pool}
    }

    political = sorted(
        [
            c
            for c in candidates
            if c.political_or_electoral
            and not c.made_for_kids
        ],
        key=lambda c: (
            c.review_priority_score
            if c.review_priority_score > 0
            else compute_review_priority(c)
        ),
        reverse=True,
    )[:top_n]
    for candidate in political:
        candidate.rank_status = "POLITICAL_REVIEW"
        if candidate.review_priority_score <= 0:
            candidate.confidence_score = round(compute_confidence(candidate), 2)
            candidate.review_priority_score = compute_review_priority(candidate)

    qualified_queries = {
        query
        for candidate in qualified
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
        "schema_version": STATE_SCHEMA_VERSION,
        "radar_version": RADAR_VERSION,
        "generated_at_utc": generated_at.isoformat(),
        "transcript_probe": {
            "requested": min(
                TRANSCRIPT_PROBE_LIMIT,
                len(candidates),
            ),
            "available": sum(
                c.transcript_status == "available"
                for c in candidates
            ),
            "segments_found": sum(
                c.transcript_segment_score > 0
                for c in candidates
            ),
        },
        "coverage": diagnostics or {},
        "selection": {
            "qualified_count": len(qualified),
            "contractual_links": len(ranked),
            "creator_input_rule": "only QUALIFIED items may proceed to Creator",
        },
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
                "downstream_eligible": c.video_id in qualified_ids,
                "selection_tier": (
                    "QUALIFIED"
                    if c.video_id in qualified_ids
                    else (
                        "REPEAT_BACKFILL"
                        if c.video_id in repeat_ids
                        else (
                            "LOW_SIGNAL_BACKFILL"
                            if c.video_id in low_signal_ids
                            else "REVIEW_FALLBACK"
                        )
                    )
                ),
            }
            for c in ranked
        ],
        "qualified_nonpolitical": [
            asdict(c)
            | {
                "url": c.url,
                "downstream_eligible": True,
                "selection_tier": "QUALIFIED",
                "reasons": explain(c),
            }
            for c in qualified
        ],
        "review_queue_nonpolitical": [
            asdict(c)
            | {
                "url": c.url,
                "downstream_eligible": False,
                "selection_tier": "REVIEW_ONLY",
                "reasons": explain(c),
            }
            for c in ranked
            if c.video_id not in qualified_ids
        ],
        "political_watchlist_raw": [
            asdict(c)
            | {
                "url": c.url,
                "selection_tier": "POLITICAL_REVIEW",
                "reasons": explain(c),
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
            "previous_score",
            "score_delta",
            "rank_status",
            "selection_tier",
            "transcript_status",
            "transcript_segment_score",
            "best_segment_start",
            "best_segment_end",
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
                c.previous_score,
                c.score_delta,
                c.rank_status,
                (
                    "QUALIFIED"
                    if c.video_id in qualified_ids
                    else (
                        "REPEAT_BACKFILL"
                        if c.video_id in repeat_ids
                        else (
                            "LOW_SIGNAL_BACKFILL"
                            if c.video_id in low_signal_ids
                            else "REVIEW_FALLBACK"
                        )
                    )
                ),
                c.transcript_status,
                round(c.transcript_segment_score, 2),
                c.best_segment_start,
                c.best_segment_end,
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

    local_time = generated_at.astimezone(ZoneInfo("America/Sao_Paulo"))
    lines = [
        f"# 🎯 Corte Fino — Radar Viral {RADAR_VERSION}",
        "",
        (
            "Atualizado em "
            f"**{local_time.strftime('%d/%m/%Y %H:%M')} BRT**."
        ),
        "",
        (
            "Ranking técnico/editorial para descoberta de cortes; "
            "pauta política permanece separada como **POLITICAL_REVIEW**."
        ),
        "",
        f"## 🔥 Prioridades ({len(ranked)}/5)",
        "",
        (
            f"Qualificados: **{len(qualified)}/5**. "
            "Apenas itens **QUALIFIED** podem seguir para o Creator."
        ),
        "",
        "Leitura rápida: prioridade, motivo, link.",
        "",
    ]

    if not ranked:
        lines.append(
            "_Nenhuma oportunidade não política nesta rodada._"
        )

    status_icons = {
        "HOT": "🔥",
        "PROMISING": "🟡",
        "WATCH": "🔵",
        "REVIEW": "⚪",
    }

    for index, c in enumerate(ranked, 1):
        is_repeat = c.video_id in repeat_ids
        is_fallback = c.video_id in fallback_ids
        is_low_signal = c.video_id in low_signal_ids
        reasons = explain(c)
        reason = reasons[0] if reasons else "sinais combinados de desempenho"
        if is_repeat:
            reason = f"repetição recente; {reason.lower()}"
        elif is_low_signal:
            reason = "não passou no gate semântico; revisão manual obrigatória"
        elif is_fallback:
            reason = f"alternativa restante; {reason.lower()}"
        delta = ""
        if (
            c.score_delta is not None
            and abs(c.score_delta) >= 0.1
            and c.momentum_state != "STALE"
        ):
            arrow = "↑" if c.score_delta > 0 else "↓"
            delta = f" | {arrow}{abs(c.score_delta):.1f}"
        chapter = f" | {c.best_chapter}" if c.best_chapter else ""
        rights = (
            "CC"
            if c.youtube_license == "creativeCommon"
            else "revisar direitos"
        )
        lines.extend([
            (
                f"{index}. {status_icons.get(c.rank_status, '•')} "
                f"**{c.title}** — {c.channel_title}"
            ),
            (
                f"   {c.rank_status}"
                f"{' / REPEAT BACKFILL' if is_repeat else ''}"
                f"{' / LOW_SIGNAL_BACKFILL' if is_low_signal else ''}"
                f"{' / FALLBACK' if is_fallback else ''} | "
                f"{c.radar_score:.1f}/100{delta} | "
                f"{fmt_int(c.view_count)} views | "
                f"{c.momentum_state} | {rights}"
            ),
            f"   **Status de uso:** "
            f"{'QUALIFIED' if c.video_id in qualified_ids else 'REVIEW_ONLY — não enviar ao Creator'}",
            f"   **Por que agora:** {reason}{chapter}",
            (
                f"   **Janela sugerida:** "
                f"{fmt_duration(c.best_segment_start or 0)}–"
                f"{fmt_duration(c.best_segment_end or 0)}"
                if c.best_segment_start is not None
                and c.best_segment_end is not None
                else "   **Janela sugerida:** investigar no Creator"
            ),
            f"   {c.url}",
            "",
        ])

    if political:
        lines.extend([
            "## 🗳️ Pauta política em revisão",
            "",
            (
                "Itens políticos não entram silenciosamente na fila não política. "
                "Eles ficam separados para checagem de contexto, afirmações e direitos "
                "antes de qualquer corte."
            ),
            "",
        ])
        for index, c in enumerate(political, 1):
            lines.extend([
                (
                    f"{index}. 🗳️ **{c.title}** — {c.channel_title}"
                ),
                (
                    f"   POLITICAL_REVIEW | "
                    f"{c.radar_score:.1f}/100 | "
                    f"{fmt_int(c.view_count)} views"
                ),
                f"   {c.url}",
                "",
            ])

    lines.extend([
        "## Resumo",
        "",
        (
            "A lista contratual mantém cinco links, mas isso não significa cinco aprovações. "
            "Somente itens QUALIFIED podem seguir para o Creator. "
            "Itens REVIEW/FALLBACK, REPEAT BACKFILL e LOW_SIGNAL_BACKFILL são apenas "
            "fila de revisão manual e não devem ser tratados como recomendação automática. "
            "A análise de legenda é enriquecimento: "
            "indisponibilidade não elimina o vídeo, mas reduz a confiança. "
            "Direitos, riscos, política e métricas completas permanecem no JSON/CSV "
            "para auditoria."
        ),
        "",
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
        default=int(os.environ.get("RADAR_TOP_N", str(REPORT_TOP_N))),
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

    if args.top_n != REPORT_TOP_N:
        print(
            f"RADAR_TOP_N é fixo em {REPORT_TOP_N}; ajuste a configuração antes de executar.",
            file=sys.stderr,
        )
        return 2

    generated_at = datetime.now(timezone.utc)

    candidates, trends, signals, state, diagnostics = collect_candidates(
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
        top_n=REPORT_TOP_N,
        generated_at=generated_at,
        diagnostics=diagnostics,
    )

    update_state(Path(args.state_file), state, candidates, generated_at)

    print(
        f"[RADAR] {len(candidates)} candidatos coletados."
    )
    print(
        f"[RADAR] Relatório: {OUTPUT_DIR / 'radar_latest.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
