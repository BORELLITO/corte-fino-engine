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


STOPWORDS = set("a o as os um uma uns umas de da do das dos e em no na nos nas para pra por com sem que quem qual quando onde como porque isso isto essa esse essas esses eu voce voces ele ela eles elas me te se meu minha seu sua mais menos muito muita muitos muitas ja nao sim so tambem aqui ali la tem ter vai vou foi ser sao era esta estao ta tao entao ne tipo cara gente acho fica ficar fazer faz fez pode poder todo toda todos todas num numa ate ai bem sobre existe ainda realmente falei falou falando dizer disse diz aqui agora assim entao bom pessoal".split())
COPY_NOISE = set("assunto assuntos coisa coisas pessoa pessoas parte jeito forma fala falas trecho trechos video videos canal corte cortes sempre nunca agora hoje casa ganha ganhou divulga divulgar".split())
TOPIC_RULES = {
    "apostas": "aposta apostas bet bets cassino cassinos tigrinho jogo jogos vicio apostar".split(),
    "politica": "lula bolsonaro stf moraes governo presidente congresso senado politica esquerda direita".split(),
    "seguranca": "crime crimes policia bandido bandidos seguranca prisao roubo assalto".split(),
    "midia": "midia noticia jornalista jornalismo tragedia audiencia".split(),
}
TOPIC_TERMS = {
    "apostas": ("apostas", "bet", "cassino", "jogos de aposta"),
    "politica": ("politica", "politica brasileira", "governo", "debate publico"),
    "seguranca": ("seguranca", "seguranca publica", "crime", "policia"),
    "midia": ("midia", "jornalismo", "noticias", "audiencia"),
    "geral": ("debate",),
}
TOPIC_KEYWORDS = {
    "apostas": set("aposta apostas bet bets cassino cassinos tigrinho jogo jogos vicio apostar".split()),
    "politica": set("lula bolsonaro stf moraes governo presidente congresso senado politica esquerda direita".split()),
    "seguranca": set("crime crimes policia bandido bandidos seguranca prisao roubo assalto".split()),
    "midia": set("midia noticia jornalista jornalismo tragedia audiencia".split()),
    "geral": set(),
}
KEYWORD_ALIASES = {
    "stf": "Supremo Tribunal Federal",
    "moraes": "Alexandre de Moraes",
    "tigrinho": "Jogo do Tigrinho",
    "policia": "polícia",
    "seguranca": "segurança",
    "politica": "política",
    "midia": "mídia",
    "tragedia": "tragédia",
    "vicio": "vício",
}
CTA_VARIANTS = {
    "apostas": (
        "Onde termina a escolha individual e começa a responsabilidade de quem influencia?",
        "Você acha que o problema está apenas em apostar ou também em estimular esse comportamento?",
        "Ganhar uma vez muda sua visão sobre o risco?",
    ),
    "politica": (
        "Você concorda com esse argumento ou vê a situação de outra forma?",
        "Esse raciocínio explica o problema ou simplifica demais o debate?",
        "Qual consequência dessa posição costuma ser ignorada?",
    ),
    "seguranca": (
        "Na prática, qual seria a resposta mais justa para esse problema?",
        "Punir, prevenir ou mudar a estrutura: por onde esse debate deveria começar?",
        "Qual parte dessa discussão costuma ficar fora do discurso público?",
    ),
    "midia": (
        "Informar ou explorar o impacto emocional: onde você colocaria o limite?",
        "Quando a informação vira espetáculo, quem assume a responsabilidade?",
        "Você acha que a audiência justifica esse tipo de exposição?",
    ),
    "geral": (
        "Você concorda com esse ponto ou enxerga de outra forma?",
        "Esse argumento convence ou deixa uma contradição importante de fora?",
        "Qual é a sua leitura sobre essa fala?",
    ),
}
EMOTIONAL_BRIDGE_VARIANTS = {
    "apostas": (
        "Quando a recompensa vira vício, a discussão deixa de ser apenas sobre dinheiro.",
        "Por trás da promessa de ganho existe uma discussão sobre comportamento e responsabilidade.",
        "Ganhar uma vez não apaga o risco de perder no longo prazo.",
    ),
    "politica": (
        "A fala toca em uma consequência concreta de um debate que costuma ficar preso aos slogans.",
        "O argumento parece simples, mas muda de peso quando observamos quem será afetado por ele.",
        "Mais do que uma disputa de opiniões, essa fala expõe uma escolha com consequências reais.",
    ),
    "seguranca": (
        "Quando esse assunto entra em pauta, o debate deixa de ser abstrato e encosta na vida real.",
        "A discussão sobre segurança muda quando colocamos as pessoas afetadas no centro da análise.",
        "Entre a reação imediata e a solução duradoura existe um debate que quase sempre é simplificado.",
    ),
    "midia": (
        "A questão não é apenas mostrar o fato, mas decidir como a dor será apresentada ao público.",
        "Informação e audiência podem caminhar juntas, mas nem sempre sem conflito.",
        "O impacto de uma notícia também depende da forma como ela é enquadrada e repetida.",
    ),
    "geral": (
        "Uma fala aparentemente simples pode revelar uma discussão muito maior.",
        "O ponto central não está apenas no que foi dito, mas na consequência desse raciocínio.",
        "É uma opinião curta, mas com espaço suficiente para abrir um debate importante.",
    ),
}
TOPIC_TAGS = {
    "apostas": "#Apostas",
    "politica": "#Politica",
    "seguranca": "#SegurancaPublica",
    "midia": "#Midia",
    "geral": "#Debate",
}
TITLE_TEMPLATES = {
    "apostas": "A VERDADE INCÔMODA SOBRE APOSTAS E RESPONSABILIDADE",
    "politica": "O ARGUMENTO QUE DIVIDIU O DEBATE",
    "seguranca": "A PERGUNTA QUE A SEGURANÇA PÚBLICA EXIGE",
    "midia": "QUANDO A MÍDIA TRANSFORMA DOR EM AUDIÊNCIA",
    "geral": "ESSA FALA ABRIU UM DEBATE INCÔMODO",
}

# Correções deliberadamente pequenas e verificadas no motor de legendas. O
# Publisher não tenta "embelezar" nomes, marcas ou gírias desconhecidas.
SAFE_TRANSCRIPT_CORRECTIONS = {
    "médo": "medo",
    "divestindo": "desistindo",
    "violins": "Aviões",
    "revindicando": "reivindicando",
    "bradão": "Brasil",
    "bradio": "Brasil",
    "idô": "segundo",
    "crescentos": "crescendo",
    "dilhé": "devia",
    "latrão": "ladrão",
    "danapolítica": "na política",
    "coneste": "conhece",
    "pim": "PIB",
    "casino": "cassino",
    "crianca": "criança",
    "politica": "política",
    "seguranca": "segurança",
    "policia": "polícia",
    "midia": "mídia",
    "vicio": "vício",
    "publico": "público",
    "audiencia": "audiência",
    "tragedia": "tragédia",
    "milhoes": "milhões",
}
UNRESOLVED_ASR_TOKENS = {
    "revindicando", "bradão", "bradio", "idô", "crescentos", "dilhé", "pim",
    "trefa", "jambos", "lulia", "latrão", "divestindo", "danapolítica", "coneste",
    "vítimo",
}
LEADING_FILLER_RE = re.compile(
    r"^(?:(?:e\s+)?falo\s+mais|bom\s*,?\s*pessoal|pessoal|então|entao|olha|cara|gente)\s*[,;:–—-]?\s*",
    re.IGNORECASE,
)
BAD_TITLE_ENDINGS = (" DE", " DA", " DO", " EM", " PARA", " COM", " E", " OU", " MAS")


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


def _preserve_case(replacement: str, original: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def normalize_transcript(text: str) -> str:
    """Apply only explicit ASR corrections already validated by the engine."""
    normalized = re.sub(r"\s+", " ", text or "").strip()
    for source, replacement in SAFE_TRANSCRIPT_CORRECTIONS.items():
        pattern = rf"(?<![\wÀ-ÿ]){re.escape(source)}(?![\wÀ-ÿ])"
        normalized = re.sub(
            pattern,
            lambda match: _preserve_case(replacement, match.group(0)),
            normalized,
            flags=re.IGNORECASE,
        )
    return normalized


def natural_index(name: str) -> int:
    match = re.search(r"(?:^|[_\-\s])(0?[1-5])(?:[_\-\s.]|$)", name)
    return int(match.group(1)) if match else 999


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", text.lower())


def get_keywords(text: str, limit: int = 4) -> list[str]:
    counts = Counter()
    for word in tokens(text):
        base = fold(word)
        if base in STOPWORDS or base in COPY_NOISE or base.isdigit() or len(base) < 4:
            continue
        counts[base] += 1
    return [word for word, _ in counts.most_common(limit)]


def detect_topic(text: str) -> str:
    words = set(tokens(fold(text)))
    ranked = [(len(words & set(rule)), topic) for topic, rule in TOPIC_RULES.items()]
    score, topic = max(ranked, default=(0, "geral"))
    return topic if score else "geral"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", re.sub(r"\s+", " ", text).strip())
    return [sentence.strip(" -–—") for sentence in parts if 18 <= len(sentence.strip()) <= 220]


def sentence_score(sentence: str) -> float:
    normalized = fold(sentence)
    hot = ("absurdo", "problema", "responsabilidade", "verdade", "mentira", "sangue", "vicio", "crime", "morte", "dinheiro", "milhoes", "jovem", "perde", "ganha", "sempre", "nunca", "pior", "grave", "risco", "erro", "escandalo", "polemica")
    score = sum(1.5 for word in hot if word in normalized)
    score += 1.2 if "?" in sentence else 0
    score += min(len(sentence.split()), 18) / 20
    if 5 <= len(sentence.split()) <= 16:
        score += 1
    if LEADING_FILLER_RE.match(sentence):
        score -= 1.5
    return score


def choose_hook(text: str) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return truncate(text or "Esse trecho levanta uma discussão importante", 92)
    return truncate(max(sentences[:18], key=sentence_score), 92).strip('"“”')


def clean_hook(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip('"“” ')
    previous = ""
    while cleaned and cleaned != previous:
        previous = cleaned
        cleaned = LEADING_FILLER_RE.sub("", cleaned).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Esse trecho levanta uma discussão importante"


def build_title(hook: str, topic: str) -> str:
    candidate = clean_hook(hook)
    if len(candidate) > 100 or candidate.upper().endswith(BAD_TITLE_ENDINGS) or "…" in candidate:
        clauses = [part.strip(" ,;:-") for part in re.split(r"[,;:!?]", candidate)]
        clauses = [part for part in clauses if len(part) >= 24 and not part.upper().endswith(BAD_TITLE_ENDINGS)]
        candidate = max(clauses, key=len, default="")
    if len(candidate) < 24 or len(candidate) > 100 or candidate.upper().endswith(BAD_TITLE_ENDINGS):
        candidate = TITLE_TEMPLATES.get(topic, TITLE_TEMPLATES["geral"])
    return candidate.upper().strip(" .,!?:;")


def viral_score(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    return round(max(sentence_score(sentence) for sentence in sentences) + text.count("?") * 0.25, 2)


def hashtag(word: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", fold(word))
    return f"#{clean.title()}" if clean else ""


def copy_quality_issues(pack: CopyPack) -> list[str]:
    texts = [pack.youtube_title, pack.tiktok_caption, pack.youtube_description]
    combined = fold(" ".join(texts))
    issues: list[str] = []
    for token in UNRESOLVED_ASR_TOKENS:
        if re.search(rf"(?<![a-zà-ÿ]){re.escape(fold(token))}(?![a-zà-ÿ])", combined):
            issues.append(f"token ASR não resolvido: {token}")
    if "#shorts" in fold(pack.tiktok_caption):
        issues.append("TikTok não pode conter #Shorts")
    if "…" in pack.youtube_title or pack.youtube_title.upper().endswith(BAD_TITLE_ENDINGS):
        issues.append("título incompleto ou truncado")
    for text in texts:
        if re.search(r"\s{2,}", text) or re.search(r"\s+[,.!?;:]", text):
            issues.append("pontuação ou espaçamento inválido")
            break
    return list(dict.fromkeys(issues))


def build_hashtags(topic: str, keywords: list[str], platform: str = "youtube") -> list[str]:
    tags = [TOPIC_TAGS.get(topic, TOPIC_TAGS["geral"])]
    allowed = TOPIC_KEYWORDS.get(topic, set())
    for word in keywords[:3]:
        if not allowed or word not in allowed:
            continue
        if word not in COPY_NOISE:
            tags.append(hashtag(KEYWORD_ALIASES.get(word, word)))
    platform_tag = "#TikTok" if platform.casefold() == "tiktok" else "#Shorts"
    tags.extend(("#CorteFino", platform_tag))
    limit = 5 if platform.casefold() == "tiktok" else 6
    return list(dict.fromkeys(tag for tag in tags if tag))[:limit]


def build_youtube_tags(topic: str, keywords: list[str]) -> list[str]:
    allowed = TOPIC_KEYWORDS.get(topic, set())
    relevant = [word for word in keywords if allowed and word in allowed]
    candidates = [*TOPIC_TERMS.get(topic, TOPIC_TERMS["geral"])]
    candidates.extend(KEYWORD_ALIASES.get(word, word) for word in relevant[:5])
    candidates.extend(("corte fino", "cortes de podcast", "shorts"))
    tags: list[str] = []
    seen: set[str] = set()
    total = 0
    for raw in candidates:
        tag = re.sub(r"\s+", " ", raw).strip()
        key = fold(tag)
        addition = len(tag) + (2 if tags else 0)
        if not tag or key in seen or total + addition > 490:
            continue
        tags.append(tag)
        seen.add(key)
        total += addition
    return tags or ["corte fino"]


def make_copy(transcript: str) -> CopyPack:
    transcript = normalize_transcript(transcript)
    topic = detect_topic(transcript)
    keys = get_keywords(transcript)
    hook = clean_hook(choose_hook(transcript))
    title = build_title(hook, topic)
    tiktok_hashtag_text = " ".join(build_hashtags(topic, keys, "tiktok"))
    youtube_hashtag_text = " ".join(build_hashtags(topic, keys, "youtube"))
    variants_index = int(viral_score(transcript) * 100) % len(EMOTIONAL_BRIDGE_VARIANTS[topic])
    bridge = EMOTIONAL_BRIDGE_VARIANTS[topic][variants_index]
    cta = CTA_VARIANTS[topic][variants_index]
    tiktok = f"{title}\n\n{bridge}\n\n{cta}\n\n{tiktok_hashtag_text}"
    youtube_description = f"{hook}\n\n{bridge}\n\n{cta}\n\nCorte Fino — recortes que transformam falas em debates.\n\n{youtube_hashtag_text}"
    pack = CopyPack(
        topic,
        hook,
        keys,
        viral_score(transcript),
        truncate(tiktok, 3500),
        title,
        truncate_utf8(youtube_description, 5000),
        build_youtube_tags(topic, keys),
    )
    issues = copy_quality_issues(pack)
    if issues:
        raise ValueError("Copy reprovada no QA: " + "; ".join(issues))
    return pack


def assign_slots(clips: list[dict]) -> None:
    ranked = sorted(clips, key=lambda clip: (-clip["copy"]["viral_score"], clip["index"]))
    for clip, hour in zip(ranked, YOUTUBE_PRIORITY):
        clip.setdefault("schedule", {})["youtube_hour"] = hour
    for clip, hour in zip(ranked, TIKTOK_PRIORITY):
        clip.setdefault("schedule", {})["tiktok_hour"] = hour


def local_publish_at(day: date, hour: int) -> str:
    local = datetime.combine(day, time(hour=hour), tzinfo=TIMEZONE)
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def copy_dict(pack: CopyPack) -> dict:
    return asdict(pack)
