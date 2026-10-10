from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Sao_Paulo")
YOUTUBE_HOURS = (10, 12, 14, 16, 18)
TIKTOK_HOURS = (10, 12, 16, 18, 20)
YOUTUBE_PRIORITY = (16, 14, 10, 12, 18)
TIKTOK_PRIORITY = (18, 10, 12, 16, 20)

# Limites oficiais usados pelo Publisher para evitar rejeições na API.
TIKTOK_CAPTION_LIMIT = 2200
YOUTUBE_TITLE_LIMIT = 100
YOUTUBE_DESCRIPTION_LIMIT = 5000
YOUTUBE_TAGS_LIMIT = 500


STOPWORDS = set("a o as os um uma uns umas de da do das dos e em no na nos nas para pra por com sem que quem qual quando onde como porque isso isto essa esse essas esses eu voce voces ele ela eles elas me te se meu minha seu sua mais menos muito muita muitos muitas ja nao sim so tambem aqui ali la tem ter vai vou foi ser sao era esta estao ta tao entao ne tipo cara gente acho fica ficar fazer faz fez pode poder todo toda todos todas num numa ate ai bem sobre existe ainda realmente falei falo falou falando dizer disse diz aqui assim entao bom pessoal".split())
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
TOPIC_TAGS = {
    "apostas": "#Apostas",
    "politica": "#Politica",
    "seguranca": "#SegurancaPublica",
    "midia": "#Midia",
    "geral": "#Debate",
}
TOPIC_LABELS = {
    "apostas": "apostas",
    "politica": "política",
    "seguranca": "segurança",
    "midia": "mídia",
    "geral": "essa fala",
}
GENERIC_COPY_PATTERNS = (
    "o trecho transforma",
    "a conversa coloca",
    "uma fala aparentemente simples",
    "recortes que transformam falas em debates",
)
SUSPICIOUS_ORTHOGRAPHY_PATTERNS = (
    (r"\ba cassino\b", "concordância suspeita em 'a cassino'"),
)

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
    "a casino": "o cassino",
    "a cassino": "o cassino",
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
    evidence: list[str] = field(default_factory=list)
    cta: str = ""
    editorial_mode: str = "grounded_context"


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


def _capitalize_sentence_starts(text: str) -> str:
    chars = list(text)
    capitalize_next = True
    for index, char in enumerate(chars):
        if capitalize_next and char.isalpha():
            chars[index] = char.upper()
            capitalize_next = False
        elif char in ".!?":
            capitalize_next = True
    return "".join(chars)


def format_copy_text(text: str, *, final_punctuation: bool = False) -> str:
    """Normalize spacing and punctuation while preserving the source meaning."""
    normalized = re.sub(r"\s+", " ", text or "").strip()
    normalized = re.sub(r"\s+([,.;!?])", r"\1", normalized)
    normalized = re.sub(r"([,;:!?])(?=[A-Za-zÀ-ÿ0-9#])", r"\1 ", normalized)
    normalized = re.sub(r",\s*,+", ", ", normalized)
    normalized = re.sub(r"([.!?])\s*([.!?])+", r"\1", normalized)
    normalized = normalized.strip(" ,;:-")
    normalized = _capitalize_sentence_starts(normalized)
    if final_punctuation and normalized and normalized[-1] not in ".!?…":
        normalized += "."
    return normalized


def truncate_chars(text: str, limit: int) -> str:
    """Truncate by characters, without exceeding a platform limit."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (cut or text[: limit - 1]).rstrip() + "…"


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
    sentences = [sentence.strip(" -–—") for sentence in parts if 18 <= len(sentence.strip()) <= 220]
    if sentences:
        return sentences
    compact = re.sub(r"\s+", " ", text or "").strip(" -–—")
    return [compact] if 18 <= len(compact) <= 220 else []


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
        return ""
    candidate = max(sentences[:18], key=sentence_score).strip('"“”')
    if len(candidate) <= 92:
        return candidate
    clauses = [part.strip(" ,;:-") for part in re.split(r"[,;:!?]", candidate)]
    valid = [part for part in clauses if 18 <= len(part) <= 92]
    return max(valid, key=len, default="")


def clean_hook(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip('"“” ')
    previous = ""
    while cleaned and cleaned != previous:
        previous = cleaned
        cleaned = LEADING_FILLER_RE.sub("", cleaned).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def build_title(hook: str, topic: str) -> str:
    del topic  # Mantido na assinatura para compatibilidade com o manifesto atual.
    candidate = clean_hook(hook)
    if len(candidate) > YOUTUBE_TITLE_LIMIT or candidate.upper().endswith(BAD_TITLE_ENDINGS) or "…" in candidate:
        clauses = [part.strip(" ,;:-") for part in re.split(r"[,;:!?]", candidate)]
        clauses = [part for part in clauses if len(part) >= 24 and not part.upper().endswith(BAD_TITLE_ENDINGS)]
        candidate = max(clauses, key=len, default="")
    if not candidate or len(candidate) > YOUTUBE_TITLE_LIMIT or candidate.upper().endswith(BAD_TITLE_ENDINGS) or "…" in candidate:
        raise ValueError("Copy reprovada: não foi possível formar um título completo a partir da fala real.")
    return candidate.upper().strip(" .,:;")


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
    if pack.youtube_title and pack.youtube_title != pack.youtube_title.upper():
        issues.append("título do YouTube não está totalmente em maiúsculas")
    if len(pack.youtube_title) > YOUTUBE_TITLE_LIMIT:
        issues.append("título do YouTube excede 100 caracteres")
    if len(pack.tiktok_caption) > TIKTOK_CAPTION_LIMIT:
        issues.append("legenda do TikTok excede 2200 caracteres")
    if len(pack.youtube_description) > YOUTUBE_DESCRIPTION_LIMIT:
        issues.append("descrição do YouTube excede 5000 caracteres")
    for token in UNRESOLVED_ASR_TOKENS:
        if re.search(rf"(?<![a-zà-ÿ]){re.escape(fold(token))}(?![a-zà-ÿ])", combined):
            issues.append(f"token ASR não resolvido: {token}")
    for phrase in GENERIC_COPY_PATTERNS:
        if phrase in combined:
            issues.append(f"frase genérica proibida: {phrase}")
    for pattern, label in SUSPICIOUS_ORTHOGRAPHY_PATTERNS:
        if re.search(pattern, combined):
            issues.append(label)
    if "#shorts" in fold(pack.tiktok_caption):
        issues.append("TikTok não pode conter #Shorts")
    if "#tiktok" in fold(pack.youtube_description):
        issues.append("YouTube não pode conter #TikTok")
    if "…" in pack.youtube_title or pack.youtube_title.upper().endswith(BAD_TITLE_ENDINGS):
        issues.append("título incompleto ou truncado")
    for text in texts:
        if re.search(r"\s{2,}", text) or re.search(r"\s+[,.!?;:]", text):
            issues.append("pontuação ou espaçamento inválido")
            break
    return list(dict.fromkeys(issues))


def _evidence_sentences(transcript: str, hook: str, keywords: list[str]) -> list[str]:
    """Select exact transcript sentences; never synthesize factual context."""
    hook_key = fold(hook)
    candidates = []
    for sentence in split_sentences(transcript):
        if fold(sentence) == hook_key:
            continue
        relevance = sentence_score(sentence)
        relevance += sum(0.75 for keyword in keywords if re.search(
            rf"(?<![\wÀ-ÿ]){re.escape(keyword)}(?![\wÀ-ÿ])", fold(sentence)
        ))
        candidates.append((relevance, sentence))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [sentence for _, sentence in candidates[:1]]


def _question_anchor(topic: str, keywords: list[str], transcript: str) -> str:
    for keyword in keywords:
        if keyword in KEYWORD_ALIASES:
            return KEYWORD_ALIASES[keyword].lower()
    if topic != "geral":
        return TOPIC_LABELS.get(topic, TOPIC_LABELS["geral"])
    for keyword in keywords:
        if keyword not in COPY_NOISE and len(keyword) >= 4:
            original = next(
                (
                    token
                    for token in re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", transcript)
                    if fold(token) == keyword
                ),
                keyword,
            )
            return (original or keyword).lower()
    return TOPIC_LABELS.get(topic, TOPIC_LABELS["geral"])


def build_contextual_cta(transcript: str, topic: str, keywords: list[str], hook: str) -> str:
    """Use curiosity and tension as questions, without asserting new facts."""
    normalized = fold(transcript)
    anchor = _question_anchor(topic, keywords, transcript)
    if "?" in hook or "?" in transcript:
        return f"Essa pergunta sobre {anchor} responde ao problema ou deixa algo importante de fora?"
    if any(marker in normalized for marker in (" mas ", " porem ", " porém ", " so que ", " só que ", " nao ", " não ")):
        return f"Esse contraste sobre {anchor} explica a situação ou simplifica demais a discussão?"
    if any(word in normalized for word in ("raiva", "medo", "vergonha", "sangue", "morte", "perdi", "trauma")):
        return f"Essa fala sobre {anchor} desperta mais identificação, revolta ou dúvida em você?"
    return f"Depois de ouvir essa fala sobre {anchor}, qual ponto mais chamou sua atenção?"


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
    if len(transcript.split()) < 6:
        raise ValueError("Copy reprovada: transcrição insuficiente para uma criação individual.")
    topic = detect_topic(transcript)
    keys = get_keywords(transcript)
    hook = format_copy_text(clean_hook(choose_hook(transcript)))
    if not hook:
        raise ValueError("Copy reprovada: não foi encontrado um gancho completo na fala real.")
    title = build_title(hook, topic)

    raw_evidence = _evidence_sentences(transcript, hook, keys)
    evidence = [format_copy_text(sentence, final_punctuation=True) for sentence in raw_evidence]
    cta = format_copy_text(build_contextual_cta(transcript, topic, keys, hook), final_punctuation=True)
    tiktok_hashtag_text = " ".join(build_hashtags(topic, keys, "tiktok"))
    youtube_hashtag_text = " ".join(build_hashtags(topic, keys, "youtube"))
    evidence_block = f'“{evidence[0]}”\n\n' if evidence else ""
    tiktok = f"{title}\n\n{evidence_block}{cta}\n\n{tiktok_hashtag_text}"
    description_hook = format_copy_text(hook, final_punctuation=True)
    youtube_description = f"{description_hook}\n\n{evidence_block}{cta}\n\n{youtube_hashtag_text}"
    pack = CopyPack(
        topic,
        hook,
        keys,
        viral_score(transcript),
        truncate_chars(tiktok, TIKTOK_CAPTION_LIMIT),
        title,
        truncate_chars(youtube_description, YOUTUBE_DESCRIPTION_LIMIT),
        build_youtube_tags(topic, keys),
        evidence=evidence,
        cta=cta,
    )
    issues = copy_quality_issues(pack)
    normalized_source = fold(transcript)
    for sentence in raw_evidence:
        if fold(sentence) not in normalized_source:
            issues.append("evidência editorial não encontrada na transcrição")
            break
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
