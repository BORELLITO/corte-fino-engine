from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Sao_Paulo")
# Grade diária oficial: cinco posts por dia. Os dois lotes de uma rodada
# devem usar datas diferentes, preservando uma única fonte/lote por dia.
DAILY_HOURS = (10, 12, 14, 16, 18)
DAILY_SLOT_PRIORITY = (10, 16, 18, 12, 14)
YOUTUBE_HOURS = DAILY_HOURS
TIKTOK_HOURS = DAILY_HOURS

# Aliases mantidos somente para compatibilidade com manifestos/inputs antigos.
DAY_PERIOD_HOURS = DAILY_HOURS
NIGHT_PERIOD_HOURS = DAILY_HOURS
PERIOD_BLOCKS = {
    "daily": DAILY_HOURS,
    "day": DAILY_HOURS,
    "morning": DAILY_HOURS,
    "first": DAILY_HOURS,
    "first_block": DAILY_HOURS,
    "bloco_a": DAILY_HOURS,
    "a": DAILY_HOURS,
    "night": DAILY_HOURS,
    "evening": DAILY_HOURS,
    "second": DAILY_HOURS,
    "second_block": DAILY_HOURS,
    "bloco_b": DAILY_HOURS,
    "b": DAILY_HOURS,
}
MANIFEST_VERSION = 8
BRANDING_VERSION = "hud-corte-fino-v1"
BRANDING_FORMAT = "vertical_9x16_shared"
BRANDING_LOGO_POSITION = "top-right"
BRANDING_CAPTION_MARGIN_V = 430


def as_bool(value: object) -> bool:
    """Interpret persisted booleans without treating the string 'false' as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().casefold() in {"1", "true", "yes", "sim", "on"}


def normalize_account_identity(value: object) -> str:
    """Normalize a Studio account identity for fail-closed comparisons."""
    raw = str(value or "").strip().casefold()
    if raw.startswith("@"):
        raw = raw[1:]
    return raw.rstrip("/")

# Limites de metadados mantidos pelo Publisher para compatibilidade com as plataformas.
TIKTOK_CAPTION_LIMIT = 2200
YOUTUBE_TITLE_LIMIT = 100
YOUTUBE_DESCRIPTION_LIMIT = 5000
YOUTUBE_TAGS_LIMIT = 500
YOUTUBE_TAG_COUNT = 20


STOPWORDS = set("a o as os um uma uns umas de da do das dos e em no na nos nas para pra por com sem que quem qual quando onde como porque isso isto essa esse essas esses eu voce voces ele ela eles elas me te se meu minha seu sua mais menos muito muita muitos muitas ja nao sim so tambem aqui ali la tem ter vai vou foi ser sao era esta estao ta tao entao ne tipo cara gente acho fica ficar fazer faz fez pode poder todo toda todos todas num numa ate ai bem sobre existe ainda realmente falei falo falou falando dizer disse diz aqui assim entao bom pessoal".split())
COPY_NOISE = set("assunto assuntos coisa coisas pessoa pessoas parte jeito forma fala falas trecho trechos video videos canal corte cortes sempre nunca agora hoje casa ganha ganhou divulga divulgar".split())
TOPIC_RULES = {
    "apostas": "aposta apostas bet bets cassino cassinos tigrinho jogo jogos vicio apostar".split(),
    "politica": "lula bolsonaro stf moraes governo presidente congresso senado politica esquerda direita".split(),
    "seguranca": "crime crimes policia bandido bandidos seguranca prisao roubo assalto".split(),
    "midia": "midia noticia jornalista jornalismo tragedia audiencia".split(),
    "ia": "ia inteligencia artificial agentes agi algoritmo algoritmos tecnologia automacao".split(),
    "petroleo": "petroleo gasolina energia barril macae plataforma refinaria".split(),
    "espaco": "marte espaco nasa foguete foguetes planeta astronauta astronomia".split(),
}
TOPIC_TERMS = {
    "apostas": ("apostas", "bet", "cassino", "jogos de aposta"),
    "politica": ("politica", "politica brasileira", "governo", "debate publico"),
    "seguranca": ("seguranca", "seguranca publica", "crime", "policia"),
    "midia": ("midia", "jornalismo", "noticias", "audiencia"),
    "ia": ("inteligencia artificial", "tecnologia", "futuro do trabalho"),
    "petroleo": ("petroleo", "energia", "economia", "geopolitica"),
    "espaco": ("Marte", "espaco", "ciencia", "exploracao espacial"),
    "geral": ("debate",),
}
TOPIC_KEYWORDS = {
    "apostas": set("aposta apostas bet bets cassino cassinos tigrinho jogo jogos vicio apostar".split()),
    "politica": set("lula bolsonaro stf moraes governo presidente congresso senado politica esquerda direita".split()),
    "seguranca": set("crime crimes policia bandido bandidos seguranca prisao roubo assalto".split()),
    "midia": set("midia noticia jornalista jornalismo tragedia audiencia".split()),
    "ia": set("ia inteligencia artificial agentes agi algoritmo algoritmos tecnologia automacao".split()),
    "petroleo": set("petroleo gasolina energia barril macae plataforma refinaria".split()),
    "espaco": set("marte espaco nasa foguete foguetes planeta astronauta astronomia".split()),
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
    "ia": "inteligência artificial",
    "agi": "AGI",
    "petroleo": "petróleo",
    "macae": "Macaé",
    "espaco": "espaço",
    "marte": "Marte",
}
TOPIC_LABELS = {
    "apostas": "apostas",
    "politica": "política",
    "seguranca": "segurança",
    "midia": "mídia",
    "ia": "inteligência artificial",
    "petroleo": "petróleo",
    "espaco": "espaço",
    "geral": "essa fala",
}
TOPIC_DISCOVERY_TAGS = {
    "apostas": ("#apostas", "#jogosdeaposta", "#economia"),
    "politica": ("#politicabrasileira", "#governo", "#debatepublico"),
    "seguranca": ("#segurancapublica", "#crime", "#sociedade"),
    "midia": ("#jornalismo", "#noticias", "#comunicacao"),
    "ia": ("#inteligenciaartificial", "#tecnologia", "#futurodotrabalho"),
    "petroleo": ("#petroleo", "#economia", "#geopolitica"),
    "espaco": ("#marte", "#ciencia", "#exploracaoespacial"),
    "geral": ("#podcast", "#debate"),
}
HASH_FRAGMENT_WORDS = {"inteligencia", "artificial", "publica", "brasileira"}
GENERIC_COPY_PATTERNS = (
    "o trecho transforma",
    "a conversa coloca",
    "uma fala aparentemente simples",
    "recortes que transformam falas em debates",
    "uma conversa do",
    "provoca reflexao",
    "provoca reflexão",
    "merece ser ouvida ate o fim",
    "merece ser ouvida até o fim",
    "qual foi a sua leitura",
    "abre espaco para diferentes leituras",
    "abre espaço para diferentes leituras",
    "qual e a sua visao",
    "qual é a sua visão",
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
EMOJIS_BY_TOPIC = {
    "apostas": ("🎰", "⚠️"),
    "politica": ("🏛️", "🗣️"),
    "seguranca": ("🚨", "⚠️"),
    "midia": ("📺", "👀"),
    "ia": ("🧠", "⚖️"),
    "petroleo": ("🛢️", "🌍"),
    "espaco": ("🚀", "🔴"),
    "geral": ("🧠", "💬"),
}
FUNCTIONAL_EMOJIS = frozenset(emoji for pair in EMOJIS_BY_TOPIC.values() for emoji in pair)


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
    credit: str = ""
    evidence: list[str] = field(default_factory=list)
    cta: str = ""
    editorial_mode: str = "grounded_context"


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def compact_paragraphs(text: str) -> str:
    """Normalize horizontal whitespace while preserving paragraph breaks."""
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", text or ""):
        clean = re.sub(r"[ \t\r\f\v]+", " ", paragraph).strip()
        if clean:
            paragraphs.append(clean)
    return "\n\n".join(paragraphs)


def truncate(text: str, limit: int) -> str:
    text = compact_paragraphs(text)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return (cut or text[: limit - 1]).rstrip() + "…"


def truncate_utf8(text: str, limit: int) -> str:
    text = compact_paragraphs(text)
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
        elif char in ".!?…":
            capitalize_next = True
    return "".join(chars)


def format_copy_text(text: str, *, final_punctuation: bool = False) -> str:
    """Normalize spacing and punctuation while preserving the source meaning."""
    normalized = re.sub(r"\s+", " ", text or "").strip()
    normalized = re.sub(r"[–—]", ",", normalized)
    normalized = re.sub(r"\s+([,.;!?…])", r"\1", normalized)
    normalized = re.sub(r"([,;:!?])(?=[A-Za-zÀ-ÿ0-9#])", r"\1 ", normalized)
    normalized = re.sub(r",\s*,+", ", ", normalized)
    normalized = re.sub(r"([.!?…])\s*([.!?…])+", r"\1", normalized)
    normalized = normalized.strip(" ,;:-")
    normalized = _capitalize_sentence_starts(normalized)
    if final_punctuation and normalized and normalized[-1] not in ".!?…":
        normalized += "."
    return normalized


def truncate_chars(text: str, limit: int) -> str:
    """Truncate by characters, without exceeding a platform limit."""
    text = compact_paragraphs(text)
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
    specific = {
        "ia": {"inteligencia", "agentes", "agi", "algoritmo"},
        "petroleo": {"petroleo", "barril", "macae", "refinaria"},
        "espaco": {"marte", "nasa", "foguete", "astronauta", "astronomia"},
    }
    ranked = []
    for order, (topic, rule) in enumerate(TOPIC_RULES.items()):
        overlap = words & set(rule)
        score = len(overlap) + 2 * len(words & specific.get(topic, set()))
        ranked.append((score, -order, topic))
    score, _, topic = max(ranked, default=(0, 0, "geral"))
    return topic if score else "geral"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", re.sub(r"\s+", " ", text).strip())
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


def remove_title_punctuation(text: str) -> str:
    """Remove punctuation while preserving accents, spaces and emojis."""
    chars = []
    for char in text or "":
        chars.append(" " if unicodedata.category(char).startswith("P") else char)
    return re.sub(r"\s+", " ", "".join(chars)).strip()


def build_title(hook: str, topic: str, emoji: str = "") -> str:
    del topic  # Mantido na assinatura para compatibilidade com o manifesto atual.
    candidate = clean_hook(hook)
    if len(candidate) > YOUTUBE_TITLE_LIMIT or candidate.upper().endswith(BAD_TITLE_ENDINGS) or "…" in candidate:
        clauses = [part.strip(" ,;:-") for part in re.split(r"[,;:!?]", candidate)]
        clauses = [part for part in clauses if len(part) >= 24 and not part.upper().endswith(BAD_TITLE_ENDINGS)]
        candidate = max(clauses, key=len, default="")
    if not candidate or len(candidate) > YOUTUBE_TITLE_LIMIT or candidate.upper().endswith(BAD_TITLE_ENDINGS) or "…" in candidate:
        raise ValueError("Copy reprovada: não foi possível formar um título completo a partir da fala real.")
    title = remove_title_punctuation(candidate).upper()
    if emoji:
        title = f"{title} {emoji}".strip()
    if len(title) > YOUTUBE_TITLE_LIMIT:
        words = [word for word in title.split() if word != emoji]
        suffix = f" {emoji}" if emoji else ""
        while words and len((" ".join(words) + suffix)) > YOUTUBE_TITLE_LIMIT:
            words.pop()
        title = (" ".join(words) + suffix).strip()
    return title


def viral_score(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    return round(max(sentence_score(sentence) for sentence in sentences) + text.count("?") * 0.25, 2)


def hashtag(word: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", fold(word))
    return f"#{clean}" if clean else ""


def copy_quality_issues(pack: CopyPack) -> list[str]:
    texts = [pack.youtube_title, pack.tiktok_caption, pack.youtube_description]
    combined = fold(" ".join(texts))
    issues: list[str] = []
    if pack.youtube_title and pack.youtube_title != pack.youtube_title.upper():
        issues.append("título do YouTube não está totalmente em maiúsculas")
    if any(unicodedata.category(char).startswith("P") for char in pack.youtube_title):
        issues.append("título contém pontuação; títulos devem ser sem pontuação")
    if len(pack.youtube_title) > YOUTUBE_TITLE_LIMIT:
        issues.append("título do YouTube excede 100 caracteres")
    if len(pack.tiktok_caption) > TIKTOK_CAPTION_LIMIT:
        issues.append("legenda do TikTok excede 2200 caracteres")
    if len(pack.youtube_description) > YOUTUBE_DESCRIPTION_LIMIT:
        issues.append("descrição do YouTube excede 5000 caracteres")
    if len(pack.youtube_tags) != YOUTUBE_TAG_COUNT:
        issues.append(f"o YouTube precisa de exatamente {YOUTUBE_TAG_COUNT} tags")
    tag_length = sum(len(tag) for tag in pack.youtube_tags) + max(0, 2 * (len(pack.youtube_tags) - 1))
    if tag_length > YOUTUBE_TAGS_LIMIT:
        issues.append("tags do YouTube excedem 500 caracteres")
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
    if "#cortefino" in fold(pack.tiktok_caption) or "#cortefino" in fold(pack.youtube_description):
        issues.append("hashtags não podem usar o branding do Publisher")
    if sum(pack.youtube_title.count(emoji) for emoji in FUNCTIONAL_EMOJIS) != 1:
        issues.append("título precisa conter exatamente um emoji funcional")
    if sum(pack.cta.count(emoji) for emoji in FUNCTIONAL_EMOJIS) != 1:
        issues.append("CTA precisa conter exatamente um emoji funcional")
    if any(dash in text for text in texts for dash in ("–", "—")):
        issues.append("travessão longo não permitido na copy")
    if "…" in pack.youtube_title or pack.youtube_title.upper().endswith(BAD_TITLE_ENDINGS):
        issues.append("título incompleto ou truncado")
    for text in texts:
        if re.search(r"[ \t]{2,}", text) or re.search(r"[ \t]+[,.!?;:]", text):
            issues.append("pontuação ou espaçamento inválido")
            break
        if sentence_case_issues(text):
            issues.append("início de frase não está em maiúscula")
            break
    return list(dict.fromkeys(issues))


def _evidence_sentences(transcript: str, hook: str, keywords: list[str]) -> list[str]:
    """Select exact transcript sentences; never synthesize factual context."""
    hook_key = fold(hook)
    hook_terms = {
        fold(token)
        for token in tokens(hook)
        if fold(token) not in STOPWORDS and fold(token) not in COPY_NOISE
    }
    keyword_terms = {
        fold(keyword)
        for keyword in keywords
        if fold(keyword) not in STOPWORDS and fold(keyword) not in COPY_NOISE
    }
    candidates = []
    for sentence in split_sentences(transcript):
        if fold(sentence) == hook_key:
            continue
        sentence_terms = {fold(token) for token in tokens(sentence)}
        hook_overlap = sentence_terms & hook_terms
        keyword_overlap = sentence_terms & keyword_terms
        # Uma citação precisa sustentar o gancho. Se não houver nenhuma
        # palavra relevante em comum, é melhor omitir a evidência do que
        # preencher a copy com uma frase literal, porém deslocada do assunto.
        if not hook_overlap and not keyword_overlap:
            continue
        relevance = sentence_score(sentence)
        relevance += 2.0 * len(hook_overlap)
        relevance += 0.75 * len(keyword_overlap)
        candidates.append((relevance, sentence))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    if candidates:
        return [sentence for _, sentence in candidates[:1]]
    # Quando o corte tem frases curtas e complementares, a segunda melhor
    # evidência pode não repetir nenhuma palavra do gancho. Ainda assim, ela
    # é segura quando vem imediatamente depois dele e permanece literal.
    sentences = split_sentences(transcript)
    for sentence in sentences:
        if fold(sentence) != hook_key:
            return [sentence]
    return []


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
    """Vary CTAs by theme while remaining grounded in the transcript."""
    normalized = fold(transcript)
    anchor = _question_anchor(topic, keywords, transcript)
    options = {
        "apostas": (
            "Onde termina o entretenimento e começa o prejuízo?",
            "Quem deveria responder por esse problema?",
        ),
        "politica": (
            "Qual é o ponto mais difícil de ignorar nessa discussão?",
            "Essa decisão resolve o problema ou apenas muda o conflito de lugar?",
        ),
        "seguranca": (
            "O que deveria mudar primeiro nessa situação?",
            "Esse problema é tratado na causa ou apenas na consequência?",
        ),
        "midia": (
            "O que ficou de fora dessa narrativa?",
            "A forma de contar muda a maneira como o público entende o fato?",
        ),
        "ia": (
            "A tecnologia está ajudando o ser humano ou substituindo funções demais?",
            "Em que momento a ferramenta passa a tomar o lugar da pessoa?",
        ),
        "petroleo": (
            "Riqueza natural significa desenvolvimento garantido?",
            "Um país consegue prosperar dependendo de uma única riqueza?",
        ),
        "espaco": (
            "Você aceitaria correr esse risco para chegar a outro planeta?",
            "O desejo de explorar justifica um risco desse tamanho?",
        ),
    }
    if topic in options:
        index = sum(ord(char) for char in normalized) % len(options[topic])
        return options[topic][index]
    if "?" in hook or "?" in transcript:
        return f"Essa pergunta sobre {anchor} responde ao problema ou deixa algo importante de fora?"
    if any(marker in normalized for marker in (" mas ", " porem ", " porém ", " so que ", " só que ", " nao ", " não ")):
        return f"Esse contraste sobre {anchor} explica a situação ou simplifica demais a discussão?"
    if any(word in normalized for word in ("raiva", "medo", "vergonha", "sangue", "morte", "perdi", "trauma")):
        return f"Essa fala sobre {anchor} desperta mais identificação, revolta ou dúvida em você?"
    return f"Depois de ouvir essa fala sobre {anchor}, qual ponto mais chamou sua atenção?"


def build_hashtags(topic: str, keywords: list[str], platform: str = "youtube") -> list[str]:
    tags = list(TOPIC_DISCOVERY_TAGS.get(topic, TOPIC_DISCOVERY_TAGS["geral"]))
    allowed = TOPIC_KEYWORDS.get(topic, set())
    for word in keywords[:3]:
        if allowed and word not in allowed:
            continue
        if word not in COPY_NOISE and word not in HASH_FRAGMENT_WORDS:
            candidate = hashtag(KEYWORD_ALIASES.get(word, word))
            if candidate not in tags:
                tags.append(candidate)
    limit = 5 if platform.casefold() == "tiktok" else 6
    return list(dict.fromkeys(tag for tag in tags if tag))[:limit]


_PUBLISHER_CREDIT_PREFIX = "cortefino"

def validate_credit_source(source_name: str = "", *, required: bool = False) -> str:
    """Validate the original channel used in the public credit line.

    Corte Fino is the publishing tool, not the source of a clip. A missing
    source is tolerated only by low-level unit-copy generation; production
    manifest preparation must pass required=True.
    """
    name = format_copy_text(source_name, final_punctuation=False)
    compact = re.sub(r"[^a-z0-9]", "", fold(name))
    if required and not name:
        raise ValueError(
            "Crédito obrigatório: informe o canal ou a fonte original do corte."
        )
    if compact.startswith(_PUBLISHER_CREDIT_PREFIX):
        raise ValueError(
            "Crédito inválido: use o canal ou a fonte original; nunca use Corte Fino."
        )
    return name


def build_credit(source_name: str = "", source_episode: str = "") -> str:
    """Create a transparent, natural credit without inventing a source."""
    name = validate_credit_source(source_name)
    episode = format_copy_text(source_episode, final_punctuation=False)
    if name and episode:
        return f"Créditos: {name}, episódio {episode}."
    if name:
        return f"Créditos: {name}."
    return "Créditos: fonte não identificada."


def build_youtube_tags(
    topic: str,
    keywords: list[str],
    source_name: str = "",
) -> list[str]:
    """Build discovery tags around the actual subject, not the Corte Fino brand."""
    candidates = [*TOPIC_TERMS.get(topic, TOPIC_TERMS["geral"])]
    candidates.extend(KEYWORD_ALIASES.get(word, word) for word in keywords[:8])
    clean_source = format_copy_text(source_name, final_punctuation=False)
    if clean_source:
        candidates.extend((clean_source, f"{clean_source} podcast", f"{clean_source} cortes"))
    candidates.extend((
        "podcast", "podcast brasileiro", "entrevista", "conversa",
        "debate", "trecho de entrevista", "opiniao", "contexto",
        "discussao", "atualidades", "sociedade", "comportamento",
        "analise", "shorts brasil", "youtube shorts brasil",
        "cortes de podcast", "corte de entrevista", "trecho de podcast",
    ))
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
    return tags[:YOUTUBE_TAG_COUNT] or ["corte fino"]


def sentence_case_issues(text: str) -> list[str]:
    """Find sentence starts that are visibly lowercase in platform copy."""
    issues: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text or ""):
        if paragraph.lstrip().startswith("#"):
            continue
        first = re.search(r"[A-Za-zÀ-ÿ]", paragraph)
        if first and first.group(0) != first.group(0).upper():
            issues.append(first.group(0))
        for match in re.finditer(r"[.!?…]\s+[^A-Za-zÀ-ÿ\n]*([A-Za-zÀ-ÿ])", paragraph):
            if match.group(1) != match.group(1).upper():
                issues.append(match.group(1))
    return issues


def make_copy(transcript: str, source_name: str = "", source_episode: str = "") -> CopyPack:
    transcript = normalize_transcript(transcript)
    if len(transcript.split()) < 6:
        raise ValueError("Copy reprovada: transcrição insuficiente para uma criação individual.")
    topic = detect_topic(transcript)
    keys = get_keywords(transcript)
    hook = format_copy_text(clean_hook(choose_hook(transcript)))
    if not hook:
        raise ValueError("Copy reprovada: não foi encontrado um gancho completo na fala real.")
    emoji_title, emoji_cta = EMOJIS_BY_TOPIC.get(topic, EMOJIS_BY_TOPIC["geral"])
    title = build_title(hook, topic, emoji_title)

    raw_evidence = _evidence_sentences(transcript, hook, keys)
    evidence = [format_copy_text(sentence, final_punctuation=True) for sentence in raw_evidence]
    cta = format_copy_text(build_contextual_cta(transcript, topic, keys, hook), final_punctuation=True)
    cta = f"{cta} {emoji_cta}"
    tiktok_hashtag_text = " ".join(build_hashtags(topic, keys, "tiktok"))
    youtube_hashtag_text = " ".join(build_hashtags(topic, keys, "youtube"))
    credit = build_credit(source_name, source_episode)
    evidence_block = f"{evidence[0]}\n\n" if evidence else ""
    tiktok = f"{title}\n\n{evidence_block}{cta}\n\n{credit}\n\n{tiktok_hashtag_text}"
    description_hook = format_copy_text(hook, final_punctuation=True)
    youtube_description = f"{description_hook}\n\n{evidence_block}{cta}\n\n{credit}\n\n{youtube_hashtag_text}"
    pack = CopyPack(
        topic,
        hook,
        keys,
        viral_score(transcript),
        truncate_chars(tiktok, TIKTOK_CAPTION_LIMIT),
        title,
        truncate_chars(youtube_description, YOUTUBE_DESCRIPTION_LIMIT),
        build_youtube_tags(topic, keys, source_name),
        credit=credit,
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


def normalize_period(period: str) -> str:
    key = fold(str(period or "")).replace("-", "_").replace(" ", "_")
    if key not in PERIOD_BLOCKS:
        raise ValueError(f"Período inválido: {period!r}. Use daily.")
    return "daily"


def period_hours(period: str) -> tuple[int, ...]:
    return PERIOD_BLOCKS[normalize_period(period)]


def assign_slots(clips: list[dict], slots: list[int] | tuple[int, ...] | None = None) -> None:
    """Assign one five-slot daily grid to a batch.

    The strongest clip receives the 10h slot, followed by 16h, 18h,
    12h and 14h, based on the current combined YouTube/TikTok audience windows. The priority order is editorial; publication still occurs
    chronologically at the stored timestamps.
    """
    if slots is None:
        if len(clips) != 5:
            raise ValueError("A atribuição de slots exige exatamente 5 cortes por dia.")
        slots = DAILY_HOURS
    slots = tuple(int(hour) for hour in slots)
    if len(clips) != len(slots) or len(set(slots)) != len(slots):
        raise ValueError("A quantidade de cortes precisa coincidir com os 5 slots únicos do dia.")
    ranked = sorted(clips, key=lambda clip: (-float(clip.get("copy", {}).get("viral_score", 0)), int(clip.get("index", 0))))
    priority = [hour for hour in DAILY_SLOT_PRIORITY if hour in slots]
    if len(priority) != len(slots):
        priority = sorted(slots, reverse=True)
    for clip, hour in zip(ranked, priority):
        clip.setdefault("schedule", {})["youtube_hour"] = hour
        clip.setdefault("schedule", {})["tiktok_hour"] = hour


def local_publish_at(day: date, hour: int) -> str:
    local = datetime.combine(day, time(hour=hour), tzinfo=TIMEZONE)
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def copy_dict(pack: CopyPack) -> dict:
    return asdict(pack)


def _copy_pack_from_dict(raw: dict) -> CopyPack:
    """Build a typed copy object for manifest validation."""
    return CopyPack(
        topic=str(raw.get("topic", "")),
        hook=str(raw.get("hook", "")),
        keywords=[str(item) for item in raw.get("keywords", [])],
        viral_score=float(raw.get("viral_score", 0) or 0),
        tiktok_caption=str(raw.get("tiktok_caption", "")),
        youtube_title=str(raw.get("youtube_title", "")),
        youtube_description=str(raw.get("youtube_description", "")),
        youtube_tags=[str(item) for item in raw.get("youtube_tags", [])],
        credit=str(raw.get("credit", "")),
        evidence=[str(item) for item in raw.get("evidence", [])],
        cta=str(raw.get("cta", "")),
        editorial_mode=str(raw.get("editorial_mode", "")),
    )


def validate_manifest(
    manifest: dict,
    *,
    require_rights: bool = False,
    require_transcripts: bool = False,
) -> None:
    """Validate the immutable two-folder/ten-clip, five-per-day contract."""
    if not isinstance(manifest, dict):
        raise RuntimeError("Manifesto inválido: a raiz precisa ser um objeto JSON.")
    issues: list[str] = []
    try:
        version = int(manifest.get("version", 0) or 0)
    except (TypeError, ValueError):
        version = 0
    if version != MANIFEST_VERSION:
        issues.append(f"versão {version} incompatível; esperado exatamente {MANIFEST_VERSION}")
    manifest_day: date | None = None
    try:
        manifest_day = date.fromisoformat(str(manifest.get("date", "")))
    except ValueError:
        issues.append("data ISO inválida")
    if str(manifest.get("timezone", "")).strip() != "America/Sao_Paulo":
        issues.append("fuso horário incompatível; esperado America/Sao_Paulo")
    if manifest.get("youtube_hours") != list(YOUTUBE_HOURS):
        issues.append("grade global do YouTube incompatível")
    if manifest.get("tiktok_hours") != list(TIKTOK_HOURS):
        issues.append("grade global do TikTok incompatível")
    if not str(manifest.get("engine_commit", "")).strip():
        issues.append("versão/commit do motor ausente")

    target_accounts = manifest.get("target_accounts")
    if not isinstance(target_accounts, dict):
        issues.append("contas-alvo ausentes")
        target_accounts = {}
    expected_youtube = normalize_account_identity(target_accounts.get("youtube"))
    expected_tiktok = normalize_account_identity(target_accounts.get("tiktok"))
    if not expected_youtube:
        issues.append("conta-alvo do YouTube ausente")
    if not expected_tiktok:
        issues.append("conta-alvo do TikTok ausente")

    batches = manifest.get("batches")
    if not isinstance(batches, list) or len(batches) != 2:
        issues.append("o manifesto precisa conter exatamente dois lotes de cinco cortes")
        batches = batches if isinstance(batches, list) else []
    batch_by_id: dict[str, dict] = {}
    batch_dates: dict[str, date] = {}
    batch_order: list[str] = []
    batch_sources: dict[str, tuple[str, str]] = {}
    for position, batch in enumerate(batches, 1):
        if not isinstance(batch, dict):
            issues.append(f"lote {position} inválido")
            continue
        batch_id = str(batch.get("batch_id", "")).strip().upper()
        folder = str(batch.get("drive_folder_id", "")).strip()
        if not batch_id or batch_id in batch_by_id:
            issues.append(f"lote {position}: identificador ausente ou duplicado")
        if not folder:
            issues.append(f"lote {position}: pasta do Drive ausente")
        try:
            batch_day = date.fromisoformat(str(batch.get("date", "")))
        except ValueError:
            issues.append(f"lote {batch_id or position}: data ISO inválida")
            batch_day = None
        try:
            expected_hours = list(period_hours(str(batch.get("period", ""))))
        except ValueError as exc:
            issues.append(f"lote {batch_id or position}: {exc}")
            expected_hours = []
        try:
            actual_hours = [int(item) for item in batch.get("hours", [])] if isinstance(batch.get("hours"), list) else []
        except (TypeError, ValueError):
            actual_hours = []
            issues.append(f"lote {batch_id or position}: horários inválidos")
        if expected_hours and actual_hours != expected_hours:
            issues.append(f"lote {batch_id or position}: horários não correspondem ao período informado")
        if batch_id:
            batch_by_id[batch_id] = batch
            batch_order.append(batch_id)
        if batch_id and batch_day:
            batch_dates[batch_id] = batch_day
        batch_source = batch.get("source")
        if not isinstance(batch_source, dict):
            issues.append(f"lote {batch_id or position}: fonte original ausente")
        else:
            try:
                source_name = validate_credit_source(str(batch_source.get("name", "")), required=True)
                source_episode = format_copy_text(str(batch_source.get("episode", "") or ""), final_punctuation=False)
                batch_sources[batch_id] = (source_name, source_episode)
            except ValueError as exc:
                issues.append(f"lote {batch_id or position}: {exc}")

    if len(batch_dates) == 2:
        if len(set(batch_dates.values())) != 2:
            issues.append("modo 5 por dia exige datas diferentes para os lotes A e B")
        elif batch_order[:2] == ["A", "B"] and batch_dates.get("B") <= batch_dates.get("A"):
            issues.append("lote B precisa ser posterior ao lote A")

    folders = [str(batch.get("drive_folder_id", "")).strip() for batch in batches if isinstance(batch, dict)]
    if len(folders) != len(set(folders)):
        issues.append("as duas pastas do Drive precisam ser diferentes")
    if not str(manifest.get("drive_folder_id", "")).strip() and folders:
        issues.append("pasta principal do Drive ausente")
    elif folders and str(manifest.get("drive_folder_id", "")).strip() != folders[0]:
        issues.append("pasta principal do manifesto não corresponde ao lote A")
    declared_folders = manifest.get("drive_folder_ids")
    if not isinstance(declared_folders, list) or [str(item) for item in declared_folders] != folders:
        issues.append("lista de pastas do manifesto não coincide com os dois lotes")
    if manifest_day and batches and isinstance(batches[0], dict):
        first_batch_date = str(batches[0].get("date", ""))
        if first_batch_date != manifest_day.isoformat():
            issues.append("data principal do manifesto não corresponde ao lote A")

    source = manifest.get("source")
    source_signature: tuple[str, str] | None = None
    if isinstance(source, dict):
        try:
            source_signature = (
                validate_credit_source(str(source.get("name", "")), required=True),
                format_copy_text(str(source.get("episode", "") or ""), final_punctuation=False),
            )
        except ValueError as exc:
            issues.append(str(exc))
    else:
        issues.append("fonte principal do manifesto ausente")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        issues.append("o manifesto precisa conter as duas fontes originais")
    else:
        source_signatures: list[tuple[str, str]] = []
        for source_position, source_item in enumerate(sources, 1):
            try:
                if not isinstance(source_item, dict):
                    raise ValueError("objeto de fonte ausente")
                source_signatures.append(
                    (
                        validate_credit_source(str(source_item.get("name", "")), required=True),
                        format_copy_text(str(source_item.get("episode", "") or ""), final_punctuation=False),
                    )
                )
            except (AttributeError, ValueError) as exc:
                issues.append(f"fonte {source_position}: {exc}")
        if len(source_signatures) == 2:
            if source_signature and source_signature != source_signatures[0]:
                issues.append("fonte principal não corresponde à fonte do lote A")
            expected_batch_sources = [batch_sources.get(batch_id) for batch_id in batch_order]
            if expected_batch_sources != source_signatures:
                issues.append("fontes declaradas não correspondem às fontes dos lotes")

    clips = manifest.get("clips")
    if not isinstance(clips, list) or len(clips) != 10:
        issues.append("o manifesto precisa conter exatamente 10 cortes")
        clips = clips if isinstance(clips, list) else []
    indexes = [clip.get("index") for clip in clips if isinstance(clip, dict)]
    if indexes != list(range(1, 11)):
        issues.append("os cortes precisam estar numerados globalmente de 1 a 10")

    seen_drive_ids: set[str] = set()
    seen_checksums: set[str] = set()
    seen_slots: set[tuple[str, int]] = set()
    by_batch: dict[str, list[dict]] = {batch_id: [] for batch_id in batch_by_id}
    for position, clip in enumerate(clips, 1):
        if not isinstance(clip, dict):
            issues.append(f"corte {position:02d} não é um objeto válido")
            continue
        raw_index = clip.get("index", position)
        try:
            display_index = int(raw_index)
        except (TypeError, ValueError):
            display_index = position
        label = f"corte {display_index:02d}"
        required_keys = ("drive_id", "drive_folder_id", "batch_id", "batch_index", "name", "md5_checksum")
        if require_transcripts:
            required_keys += ("transcript",)
        for key in required_keys:
            if not str(clip.get(key, "")).strip():
                issues.append(f"{label}: campo {key} ausente")
        drive_id = str(clip.get("drive_id", "")).strip()
        checksum = str(clip.get("md5_checksum", "")).strip()
        if drive_id and drive_id in seen_drive_ids:
            issues.append(f"{label}: arquivo Drive duplicado")
        if checksum and checksum in seen_checksums:
            issues.append(f"{label}: checksum duplicado")
        if drive_id:
            seen_drive_ids.add(drive_id)
        if checksum:
            seen_checksums.add(checksum)
        batch_id = str(clip.get("batch_id", "")).strip().upper()
        try:
            batch_index = int(clip.get("batch_index"))
        except (TypeError, ValueError):
            batch_index = 0
        if batch_id not in batch_by_id:
            issues.append(f"{label}: lote inexistente")
        elif str(clip.get("drive_folder_id", "")).strip() != str(batch_by_id[batch_id].get("drive_folder_id", "")).strip():
            issues.append(f"{label}: pasta não corresponde ao lote")
        else:
            by_batch.setdefault(batch_id, []).append(clip)
        schedule = clip.get("schedule")
        if not isinstance(schedule, dict):
            issues.append(f"{label}: bloco de agendamento inválido")
            schedule = {}
        try:
            youtube_hour = int(schedule.get("youtube_hour"))
            tiktok_hour = int(schedule.get("tiktok_hour"))
        except (TypeError, ValueError):
            issues.append(f"{label}: horários inválidos")
            youtube_hour = tiktok_hour = -1
        if youtube_hour != tiktok_hour:
            issues.append(f"{label}: YouTube e TikTok precisam compartilhar o mesmo horário")
        expected_batch_hours: list[int] = []
        if batch_id in batch_by_id:
            try:
                expected_batch_hours = list(period_hours(str(batch_by_id.get(batch_id, {}).get("period", ""))))
            except ValueError:
                expected_batch_hours = []
        if expected_batch_hours and youtube_hour not in expected_batch_hours:
            issues.append(f"{label}: horário fora do período do lote")
        publish_at = str(schedule.get("youtube_publish_at", "")).strip()
        tiktok_at = str(schedule.get("tiktok_publish_at", "")).strip()
        if not publish_at or not tiktok_at or publish_at != tiktok_at:
            issues.append(f"{label}: timestamps de publicação ausentes ou divergentes")
        parsed_at = None
        try:
            raw_parsed_at = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
            if raw_parsed_at.tzinfo is None:
                raise ValueError("timestamp sem fuso horário")
            parsed_at = raw_parsed_at.astimezone(TIMEZONE)
        except (TypeError, ValueError):
            if publish_at:
                issues.append(f"{label}: timestamp de publicação inválido")
        if parsed_at and parsed_at.hour != youtube_hour:
            issues.append(f"{label}: hora do timestamp não corresponde ao slot")
        if parsed_at and batch_id in batch_dates and parsed_at.date() != batch_dates[batch_id]:
            issues.append(f"{label}: data do timestamp não corresponde ao lote")
        if parsed_at:
            slot_key = (parsed_at.date().isoformat(), parsed_at.hour)
            if slot_key in seen_slots:
                issues.append(f"{label}: conflito de horário com outro corte")
            seen_slots.add(slot_key)
        raw_copy = clip.get("copy")
        if not isinstance(raw_copy, dict):
            issues.append(f"{label}: copy ausente")
            continue
        try:
            pack = _copy_pack_from_dict(raw_copy)
        except (TypeError, ValueError):
            issues.append(f"{label}: copy inválida")
            continue
        for copy_issue in copy_quality_issues(pack):
            issues.append(f"{label}: {copy_issue}")
        expected_source = batch_sources.get(batch_id)
        if expected_source:
            expected_credit = build_credit(*expected_source)
            if fold(pack.credit) != fold(expected_credit):
                issues.append(f"{label}: crédito não corresponde à fonte do lote")
        if not pack.credit or fold(pack.credit).startswith("creditos: fonte nao identificada"):
            issues.append(f"{label}: crédito da fonte original ausente")
        if "corte fino" in fold(pack.credit):
            issues.append(f"{label}: crédito não pode ser o Publisher")
        if "\n\n" not in pack.tiktok_caption:
            issues.append(f"{label}: legenda TikTok sem separação de parágrafos")
        if "\n\n" not in pack.youtube_description:
            issues.append(f"{label}: descrição YouTube sem separação de parágrafos")
        if not pack.youtube_title or pack.youtube_title != pack.youtube_title.upper():
            issues.append(f"{label}: título YouTube não está totalmente em maiúsculas")
        if not pack.tiktok_caption.split("\n\n")[-1].startswith("#"):
            issues.append(f"{label}: hashtags TikTok ausentes ou fora do final")
        if not pack.youtube_description.split("\n\n")[-1].startswith("#"):
            issues.append(f"{label}: hashtags YouTube ausentes ou fora do final")

    for batch_id, batch in batch_by_id.items():
        batch_clips = by_batch.get(batch_id, [])
        if len(batch_clips) != 5:
            issues.append(f"lote {batch_id}: esperado 5 cortes, encontrados {len(batch_clips)}")
        normalized_batch_indexes: list[int] = []
        for item in batch_clips:
            try:
                normalized_batch_indexes.append(int(item.get("batch_index", 0)))
            except (TypeError, ValueError):
                normalized_batch_indexes.append(0)
        if sorted(normalized_batch_indexes) != [1, 2, 3, 4, 5]:
            issues.append(f"lote {batch_id}: índices precisam ser exatamente 1 a 5")

    if len(seen_slots) != len([clip for clip in clips if isinstance(clip, dict)]):
        issues.append("existem timestamps de publicação duplicados")

    rights = manifest.get("rights")
    authorized = as_bool(rights.get("authorized")) if isinstance(rights, dict) else False
    if require_rights and not authorized:
        issues.append("direitos não confirmados para publicação")
    if not isinstance(rights, dict) or "authorized" not in rights:
        issues.append("bloco de direitos ausente")
    branding = manifest.get("branding")
    if not isinstance(branding, dict) or branding.get("version") != BRANDING_VERSION:
        issues.append("versão da identidade visual ausente ou incompatível")
    else:
        try:
            caption_margin = int(branding.get("caption_margin_v", -1) or -1)
        except (TypeError, ValueError):
            caption_margin = -1
        if (
            branding.get("format") != BRANDING_FORMAT
            or branding.get("logo_position") != BRANDING_LOGO_POSITION
            or caption_margin != BRANDING_CAPTION_MARGIN_V
        ):
            issues.append("contrato de HUD/legenda incompatível com o motor de renderização")
    if issues:
        raise RuntimeError("Manifesto inválido: " + "; ".join(dict.fromkeys(issues)))

