from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import re
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
    "Cortes do Flow",
    "Cortes do Inteligência",
    "RedCast",
    "Podpah",
]

PREFERRED_SOURCE_PATTERNS = [
    "flow podcast",
    "cortes do flow",
    "inteligência ltda",
    "inteligencia ltda",
    "cortes do inteligência",
    "cortes do inteligencia",
    "redcast",
    "podpah",
    "pânico",
    "panico",
    "venus podcast",
    "fala ordinário",
    "fala ordinario",
]

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
POLITICAL_TERMS = {
    "eleição", "eleicoes", "eleições", "segundo turno", "presidente", "candidato",
    "candidata", "campanha", "governo", "congresso", "senado", "deputado", "deputada",
    "stf", "tse", "lula", "bolsonaro", "flávio bolsonaro", "flavio bolsonaro",
    "nikolas", "mbl", "pt", "pl", "psol", "missão", "missao", "prefeito", "governador",
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
class VideoCandidate:
    video_id: str
    title: str
    channel_title: str
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
    comment_divergence: bool = False
    views_per_hour: float = 0.0
    comment_rate_per_1k: float = 0.0
    like_rate_per_1k: float = 0.0
    freshness_score: float = 0.0
    velocity_score: float = 0.0
    engagement_score: float = 0.0
    controversy_score: float = 0.0
    emotion_score: float = 0.0
    search_gap_score: float = 0.0
    source_score: float = 0.0
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
    return sum(1 for term in terms if term in norm)


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


def fetch_bytes(url: str, *, timeout: int = 20, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    headers = {
        "User-Agent": "CorteFinoRadar/1.0",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Falha ao acessar {url}: {last_error}")


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
) -> tuple[list[str], int]:
    payload = fetch_json(
        f"{YOUTUBE_API}/search",
        {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "order": "relevance",
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
    max_results: int = 50,
) -> tuple[list[str], int]:
    try:
        payload = fetch_json(
            f"{YOUTUBE_API}/commentThreads",
            {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": max_results,
                "order": "relevance",
                "textFormat": "plainText",
                "key": api_key,
            },
        )
    except Exception as exc:
        print(
            f"[WARN] Comentários indisponíveis para {video_id}: {exc}",
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
    norm = normalize(channel_title)
    return any(pattern in norm for pattern in PREFERRED_SOURCE_PATTERNS)


def is_political(text: str) -> bool:
    norm = normalize(text)
    for term in POLITICAL_TERMS:
        if " " in term or len(term) >= 4:
            if term in norm:
                return True
        elif re.search(rf"(?<!\w){re.escape(term)}(?!\w)", norm):
            return True
    return False


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
        for term in {"criança", "crianca", "menor", "adolescente"}
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
        [signal.gap_score for signal in candidate.query_signals] or [0.0]
    )
    candidate.source_score = 100.0 if candidate.preferred_source else 35.0

    if candidate.youtube_license == "creativeCommon":
        candidate.rights_status = "youtube_creative_commons"
        candidate.rights_note = (
            "O vídeo está marcado pela API do YouTube como Creative Commons; "
            "cumpra os termos e a atribuição aplicáveis."
        )


def finalize_score(candidate: VideoCandidate) -> None:
    if candidate.political_or_electoral:
        candidate.radar_score = None
        return

    score = (
        candidate.velocity_score * 0.24
        + candidate.engagement_score * 0.13
        + candidate.comment_heat_score * 0.18
        + candidate.controversy_score * 0.12
        + candidate.emotion_score * 0.10
        + candidate.search_gap_score * 0.13
        + candidate.freshness_score * 0.05
        + candidate.source_score * 0.05
    )
    if len(candidate.source_queries) >= 2:
        score += min(5.0, 1.5 * (len(candidate.source_queries) - 1))
    candidate.radar_score = round(clamp(score), 2)


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
        political_or_electoral=is_political(combined),
        risk_flags=risk_flags(combined),
    )


def build_queries(
    trends: list[Trend],
    extra_topics: list[str],
    max_queries: int,
) -> list[tuple[str, str, Trend | None]]:
    queries: list[tuple[str, str, Trend | None]] = []
    queries.extend(
        (trend.topic, "google_trends", trend)
        for trend in trends
    )
    queries.extend(
        (topic.strip(), "manual_extra", None)
        for topic in extra_topics
        if topic.strip()
    )
    queries.extend(
        (source, "preferred_source", None)
        for source in SOURCE_QUERIES
    )
    queries.extend(
        (theme, "editorial_theme", None)
        for theme in DEFAULT_THEMES
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
) -> tuple[list[VideoCandidate], list[Trend], list[QuerySignal]]:
    now = datetime.now(timezone.utc)
    published_after = (
        now - timedelta(days=days)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

    trends = fetch_google_trends(trend_limit)
    queries = build_queries(
        trends,
        extra_topics,
        max_queries,
    )

    video_signals: dict[str, list[QuerySignal]] = {}
    all_signals: list[QuerySignal] = []

    for index, (query, source, trend) in enumerate(queries, 1):
        print(f"[RADAR] Busca {index}/{len(queries)}: {query}")
        try:
            ids, total = youtube_search(
                api_key,
                query,
                published_after,
            )
        except Exception as exc:
            print(
                f"[WARN] Busca falhou para '{query}': {exc}",
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
        candidates.append(candidate)

    pre_ranked = sorted(
        [
            c
            for c in candidates
            if not c.political_or_electoral
        ],
        key=lambda c: (
            c.velocity_score * 0.35
            + c.engagement_score * 0.20
            + c.controversy_score * 0.15
            + c.emotion_score * 0.10
            + c.search_gap_score * 0.15
            + c.source_score * 0.05
        ),
        reverse=True,
    )

    for candidate in pre_ranked[:min(20, len(pre_ranked))]:
        comments, replies = youtube_comments(
            api_key,
            candidate.video_id,
            50,
        )
        candidate.sampled_comments = len(comments)
        candidate.sampled_replies = replies
        (
            candidate.comment_heat_score,
            candidate.comment_divergence,
        ) = comment_analysis(comments, replies)

    for candidate in candidates:
        finalize_score(candidate)

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
    reasons = [
        (
            candidate.velocity_score,
            f"velocidade de views {candidate.views_per_hour:,.0f}/h".replace(
                ",",
                ".",
            ),
        ),
        (
            candidate.comment_heat_score,
            "comentários com forte reação/divergência",
        ),
        (
            candidate.controversy_score,
            "vocabulário de conflito/polêmica",
        ),
        (
            candidate.emotion_score,
            "carga emocional",
        ),
        (
            candidate.search_gap_score,
            "demanda/saturação favorável",
        ),
        (
            candidate.source_score,
            "fonte editorial preferida",
        ),
        (
            candidate.engagement_score,
            "densidade de comentários/likes",
        ),
    ]
    return [
        text
        for score, text in sorted(
            reasons,
            reverse=True,
        )[:3]
        if score >= 20
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
            if c.radar_score is not None
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

    gap_signals = sorted(
        [
            signal
            for signal in query_signals
            if signal.source != "preferred_source"
        ],
        key=lambda s: s.gap_score,
        reverse=True,
    )[:top_n]

    payload = {
        "schema_version": 1,
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
            "comments",
            "comment_rate_per_1k",
            "comment_heat",
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
                c.comment_count,
                round(c.comment_rate_per_1k, 3),
                round(c.comment_heat_score, 2),
                round(c.search_gap_score, 2),
                c.preferred_source,
                c.youtube_license,
                c.rights_status,
                ",".join(c.risk_flags),
            ])

    lines = [
        "# 🎯 Corte Fino — Radar Viral",
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
                f"   Score: **{c.radar_score:.1f}/100** | "
                f"{fmt_int(c.view_count)} views | "
                f"{c.views_per_hour:,.0f} views/h médio | "
                f"{fmt_int(c.comment_count)} comentários | "
                f"{fmt_duration(c.duration_seconds)} | "
                f"{license_note}{risk}  "
            ),
            f"   Por quê: {reason}.  ",
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
