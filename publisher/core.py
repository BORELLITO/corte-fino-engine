from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Sao_Paulo")
YOUTUBE_HOURS = (10, 12, 14, 16, 18)
TIKTOK_HOURS = (10, 12, 16, 18, 20)
YOUTUBE_PRIORITY = (16, 14, 10, 12, 18)
TIKTOK_PRIORITY = (18, 10, 12, 16, 20)


STOPWORDS = set("a o as os um uma uns umas de da do das dos e em no na nos nas para pra por com sem que quem qual quando onde como porque isso isto essa esse essas esses eu voce voces ele ela eles elas me te se meu minha seu sua mais menos muito muita muitos muitas ja nao sim so tambem aqui ali la tem ter vai vou foi ser sao era esta estao ta tao entao ne tipo cara gente acho fica ficar fazer faz fez pode poder todo toda todos todas num numa ate ai bem".split())
TOPIC_RULES = {
    "apostas": "aposta apostas bet bets cassino cassinos tigrinho jogo jogos vicio apostar".split(),
    "politica": "lula bolsonaro stf moraes governo presidente congresso senado politica esquerda direita".split(),
    "seguranca": "crime crimes policia bandido bandidos seguranca prisao roubo assalto".split(),
    "midia": "midia noticia jornalista jornalismo tragedia audiencia".split(),
}
CTA = {
    "apostas": "Onde termina a escolha individual e começa a responsabilidade de quem influencia?",
    "politica": "Você concorda com esse argumento ou vê a situação de outra forma?",
    "seguranca": "Na prática, qual seria a resposta mais justa para esse problema?",
    "midia": "Informar ou explorar o impacto emocional: onde você colocaria o limite?",
    "geral": "Você concorda com esse ponto ou enxerga de outra forma?",
}
EMOTIONAL_BRIDGE = {
    "apostas": "Por trás de uma aposta que parece inofensiva, existe uma discussão que pode atingir qualquer família.",
    "politica": "Mais do que uma opinião política, este trecho expõe uma disputa de narrativas que divide o país.",
    "seguranca": "Quando a segurança falha, o problema deixa de ser manchete e passa a fazer parte da vida de alguém.",
    "midia": "Quando uma tragédia vira conteúdo, a pergunta deixa de ser apenas o que aconteceu — e passa a ser quem se beneficia.",
    "geral": "Às vezes, uma frase resume um problema que muita gente sente, mas quase ninguém consegue explicar.",
}
TOPIC_TAGS = {
    "apostas": "#Apostas",
    "politica": "#Politica",
    "seguranca": "#Seguranca",
    "midia": "#Midia",
    "geral": "#Debate",
}


@dataclass
class CopyPack:
    topic: str
    hook: str
    keywords: list[str]
    viral_score: float
    tiktok_caption: str
    youtube_title: str
    youtube_description: str
    youtube_tags: list[str]


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def truncate(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (cut or text[: limit - 1]).rstrip() + "…"


def truncate_utf8(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text.encode("utf-8")) <= limit:
        return text
    candidate = text
    while candidate and len((candidate + "…").encode("utf-8")) > limit:
        candidate = candidate[:-1].rstrip()
    return candidate.rstrip(" ,.;:-") + "…"


def natural_index(name: str) -> int:
    m = re.search(r"(?:^|[_\-\s])(0?[1-5])(?:[_\-\s.]|$)", name)
    return int(m.group(1)) if m else 999


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", text.lower())


def get_keywords(text: str, limit: int = 4) -> list[str]:
    counts = Counter()
    for word in tokens(text):
        base = fold(word)
        if base in STOPWORDS or base.isdigit() or len(base) < 4:
            continue
        counts[base] += 1
    return [w for w, _ in counts.most_common(limit)]


def detect_topic(text: str) -> str:
    words = set(tokens(fold(text)))
    ranked = [(len(words & set(rule)), topic) for topic, rule in TOPIC_RULES.items()]
    score, topic = max(ranked, default=(0, "geral"))
    return topic if score else "geral"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", re.sub(r"\s+", " ", text).strip())
    return [s.strip(" -–—") for s in parts if 18 <= len(s.strip()) <= 220]


def sentence_score(sentence: str) -> float:
    s = fold(sentence)
    hot = ("absurdo", "problema", "responsabilidade", "verdade", "mentira", "sangue", "vicio", "crime", "morte", "dinheiro", "milhoes", "jovem", "perde", "ganha", "sempre", "nunca", "pior", "grave", "risco", "erro", "escandalo", "polemica")
    score = sum(1.5 for word in hot if word in s)
    score += 1.2 if "?" in sentence else 0
    score += min(len(sentence.split()), 18) / 20
    if 5 <= len(sentence.split()) <= 16:
        score += 1
    return score


def choose_hook(text: str) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return truncate(text or "Esse trecho levanta uma discussão importante", 92)
    return truncate(max(sentences[:18], key=sentence_score), 92).strip('"“”')


def viral_score(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    return round(max(sentence_score(s) for s in sentences) + text.count("?") * 0.25, 2)


def hashtag(word: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", fold(word))
    return f"#{clean.title()}" if clean else ""


def build_hashtags(topic: str, keywords: list[str]) -> list[str]:
    tags = [TOPIC_TAGS.get(topic, TOPIC_TAGS["geral"])]
    tags.extend(hashtag(word) for word in keywords[:4])
    tags.append("#CorteFino")
    tags.append("#Shorts")
    return list(dict.fromkeys(tag for tag in tags if tag))


def build_youtube_tags(topic: str, keywords: list[str]) -> list[str]:
    candidates = [topic.replace("_", " "), *keywords[:5], "corte fino", "cortes de podcast", "shorts"]
    tags: list[str] = []
    seen: set[str] = set()
    total = 0
    for raw in candidates:
        tag = re.sub(r"\s+", " ", raw).strip()
        key = fold(tag)
        if not tag or key in seen:
            continue
        addition = len(tag) + (2 if tags else 0)
        if total + addition > 490:
            break
        tags.append(tag)
        seen.add(key)
        total += addition
    return tags or ["corte fino"]


def make_copy(transcript: str) -> CopyPack:
    topic = detect_topic(transcript)
    keys = get_keywords(transcript)
    hook = choose_hook(transcript)
    title = truncate(hook.upper(), 96)
    subject = ", ".join(keys[:3]) if keys else "esse assunto"
    hashtags = build_hashtags(topic, keys)
    hashtag_text = " ".join(hashtags)
    bridge = EMOTIONAL_BRIDGE.get(topic, EMOTIONAL_BRIDGE["geral"])
    cta = CTA[topic]
    tiktok = f"{title}\n\n{bridge} O trecho coloca {subject} no centro da conversa.\n\n{cta}\n\n{hashtag_text}"
    yt_desc = f"{hook}\n\n{bridge} O trecho coloca {subject} no centro da conversa.\n\n{cta}\n\nCorte Fino — recortes que transformam falas em debates.\n\n{hashtag_text}"
    return CopyPack(
        topic,
        hook,
        keys,
        viral_score(transcript),
        truncate(tiktok, 3500),
        title,
        truncate_utf8(yt_desc, 5000),
        build_youtube_tags(topic, keys),
    )


def assign_slots(clips: list[dict]) -> None:
    ranked = sorted(clips, key=lambda c: (-c["copy"]["viral_score"], c["index"]))
    for clip, hour in zip(ranked, YOUTUBE_PRIORITY):
        clip.setdefault("schedule", {})["youtube_hour"] = hour
    for clip, hour in zip(ranked, TIKTOK_PRIORITY):
        clip.setdefault("schedule", {})["tiktok_hour"] = hour


def local_publish_at(day: date, hour: int) -> str:
    local = datetime.combine(day, time(hour=hour), tzinfo=TIMEZONE)
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def copy_dict(pack: CopyPack) -> dict:
    return asdict(pack)
