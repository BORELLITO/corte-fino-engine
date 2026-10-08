from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Regra editorial fixa: toda rodada aprovada precisa terminar com cinco cortes.
# Não permitir override externo evita uma execução “aprovada” com 4 ou 6 arquivos.
MAX_CLIPS = 5
MIN_EDITORIAL_SCORE = float(os.environ.get("MIN_EDITORIAL_SCORE", "78"))
# A nota ordena candidatos; o bloco padrão é um Top 5 fechado.
USE_EDITORIAL_SCORE_GATE = os.environ.get("USE_EDITORIAL_SCORE_GATE", "0").strip().lower() in {"1", "true", "yes", "sim"}
REQUIRE_EXACT_TOP_FIVE = os.environ.get("REQUIRE_EXACT_TOP_FIVE", "1").strip().lower() in {"1", "true", "yes", "sim"}
FORCE_TOP_FIVE = os.environ.get("FORCE_TOP_FIVE", "0").strip().lower() in {"1", "true", "yes", "sim"}
MIN_CLIP_SECONDS = int(os.environ.get("MIN_CLIP_SECONDS", "45"))
MAX_CLIP_SECONDS = int(os.environ.get("MAX_CLIP_SECONDS", "90"))
TARGET_CLIP_SECONDS = int(os.environ.get("TARGET_CLIP_SECONDS", "68"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small").strip() or "small"
MAX_SOURCE_DURATION_SECONDS = int(os.environ.get("MAX_SOURCE_DURATION_SECONDS", "10800"))
TRANSCRIBE_BEAM_SIZE = max(1, int(os.environ.get("TRANSCRIBE_BEAM_SIZE", "3")))
TRANSCRIBE_CPU_THREADS = max(1, int(os.environ.get("TRANSCRIBE_CPU_THREADS", "4")))
TRANSCRIBE_PROGRESS_SECONDS = max(15, int(os.environ.get("TRANSCRIBE_PROGRESS_SECONDS", "45")))
CAPTION_MIN_WORDS = 3
CAPTION_MAX_WORDS = 6
# Pequenas partículas finais (ex.: “né?”, “tá?”) podem durar menos que o mínimo
# quando são unidas ao bloco anterior sem violar largura ou duração.
CAPTION_SHORT_TAIL_WORD_SLACK = 2
CAPTION_FONT_SIZE = int(os.environ.get("CAPTION_FONT_SIZE", "48"))
CAPTION_FONT_NAME = os.environ.get("CAPTION_FONT_NAME", "DejaVu Sans Condensed").strip() or "DejaVu Sans Condensed"
# Mantém as legendas acima da área de interface inferior de Shorts e TikTok.
CAPTION_MARGIN_V = int(os.environ.get("CAPTION_MARGIN_V", "390"))
YOUTUBE_CAPTION_MARGIN_V = int(os.environ.get("YOUTUBE_CAPTION_MARGIN_V", str(CAPTION_MARGIN_V)))
TIKTOK_CAPTION_MARGIN_V = CAPTION_MARGIN_V  # compatibilidade: render único para as duas plataformas
CAPTION_MAX_LINE_CHARS = int(os.environ.get("CAPTION_MAX_LINE_CHARS", "32"))
CAPTION_MIN_DURATION = float(os.environ.get("CAPTION_MIN_DURATION", "0.24"))
CAPTION_MAX_DURATION = float(os.environ.get("CAPTION_MAX_DURATION", "4.0"))
CAPTION_MAX_GAP = float(os.environ.get("CAPTION_MAX_GAP", "1.5"))
CAPTION_SYNC_TOLERANCE = float(os.environ.get("CAPTION_SYNC_TOLERANCE", "0.35"))
THUMB_WIDTH = 1080
THUMB_HEIGHT = 1920
THUMB_FRAME_Y = int(os.environ.get("THUMB_FRAME_Y", "420"))
THUMB_HEADLINE_Y = int(os.environ.get("THUMB_HEADLINE_Y", "1120"))
THUMB_FONT_SIZE = int(os.environ.get("THUMB_FONT_SIZE", "68"))
CAPTION_SUSPECT_TOKENS = {
    # Erros recorrentes de ASR observados em revisões anteriores. Os termos sem
    # correção segura continuam reprovando o candidato; os termos com correção
    # verificada abaixo são normalizados antes do gate e ficam registrados no QA.
    "revindicando", "bradão", "bradio", "idô", "crescentos", "dilhé", "pim",
    "trefa", "vítimo", "lulia", "latrão", "divestindo", "danapolítica", "coneste",
    "médo", "jambos", "violins",
}
# Correções determinísticas de ASR com evidência ortográfica/contextual forte.
# Não altera timestamps nem cria conteúdo: troca somente o token reconhecido.
CAPTION_SAFE_CORRECTIONS = {
    "médo": "medo",
    "violins": "Aviões",
}
CAPTION_MIN_WORD_PROBABILITY = float(os.environ.get("CAPTION_MIN_WORD_PROBABILITY", "0.40"))
CAPTION_SPELLING_MIN_ZIPF = float(os.environ.get("CAPTION_SPELLING_MIN_ZIPF", "2.30"))
CAPTION_ALLOWED_TOKENS = {
    "corte", "fino", "shorts", "tiktok", "youtube", "podcast", "stf", "ia",
    "acre", "lito", "bolsonaro", "lula", "moraes", "brasil", "brasileiro",
    "brasileira", "aviação", "aviao", "avião", "aviao", "helicóptero",
    "helicoptero", "whatsapp", "chatgpt", "openai",
}
ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"
SOURCE_DIR = WORK / "source"
CLIPS_DIR = OUTPUT / "clips"
THUMBS_DIR = OUTPUT / "thumbs"

HOOK_WORDS = {
    "absurdo", "absurda", "surpresa", "surpreendente", "inacreditável", "inacreditavel",
    "ninguém", "ninguem", "nunca", "segredo", "descobri", "descoberta", "revelou",
    "revelação", "revelacao", "verdade", "proibido", "perigoso", "perigo", "ninguém",
}
CONFLICT_WORDS = {
    "mas", "porém", "porem", "só que", "so que", "entretanto", "discordo", "discorda",
    "briga", "treta", "contra", "errado", "errada", "mentira", "problema", "não é bem",
    "nao e bem", "jamais", "nunca", "concorda",
}
PAYOFF_WORDS = {
    "porque", "por isso", "resultado", "aconteceu", "acontece", "descobri", "finalmente",
    "então", "entao", "foi assim", "a verdade", "no fim", "conclusão", "conclusao",
}
QUESTION_WORDS = {"por que", "porque", "como", "quando", "quem", "qual", "será", "sera"}
HUMOR_WORDS = {"risada", "risos", "engraçado", "engracado", "piada", "humor", "rindo"}
EMOTION_WORDS = {
    "medo", "raiva", "vergonha", "emoção", "emocao", "emocionante", "saudade", "família",
    "familia", "chorar", "chorei", "perdi", "ganhei", "trauma", "sonho",
}
GENERIC_STARTS = (
    "e aí", "e ai", "então", "entao", "como eu falei", "como falei", "isso porque",
    "aí eu", "ai eu", "né,", "ne,", "bom, então", "bom entao",
)

NICHE_SIGNAL_MAP = {
    "política e poder": {
        "signals": {"governo", "presidente", "congresso", "stf", "ministro", "eleição", "eleicoes", "voto", "bolsonaro", "lula", "centrão", "corrupção"},
        "lenses": ["confronto", "declaração difícil de ignorar", "consequência pública"],
        "question": "Essa leitura sobre política faz sentido ou exagera? Por quê?",
    },
    "crime e segurança": {
        "signals": {"crime", "polícia", "policia", "prisão", "prisao", "bandido", "segurança", "seguranca", "favela", "impunidade", "tribunal", "investigação"},
        "lenses": ["relato real", "risco", "consequência"],
        "question": "Qual ponto dessa análise mais chamou sua atenção?",
    },
    "tecnologia e inteligência artificial": {
        "signals": {"tecnologia", "tecnológico", "tecnologico", "inteligência artificial", "inteligencia artificial", "ia", "robô", "robo", "algoritmo", "futuro", "chatgpt", "computador"},
        "lenses": ["explicação contraintuitiva", "transformação", "futuro próximo"],
        "question": "Essa mudança parece mais oportunidade ou ameaça?",
    },
    "ciência e conhecimento": {
        "signals": {"ciência", "ciencia", "pesquisa", "experimento", "evidência", "evidencia", "história", "historia", "universo", "avião", "aviao", "helicóptero", "helicoptero", "mistério", "misterio"},
        "lenses": ["explicação", "evidência versus especulação", "descoberta"],
        "question": "Você já conhecia essa explicação?",
    },
    "dinheiro e trabalho": {
        "signals": {"dinheiro", "salário", "salario", "empresa", "negócio", "negocio", "trabalho", "carreira", "investimento", "preço", "preco", "vendas", "mercado"},
        "lenses": ["decisão", "risco", "transformação prática"],
        "question": "Você tomaria essa decisão nas mesmas condições?",
    },
    "comportamento e relações": {
        "signals": {"relacionamento", "casamento", "família", "familia", "amor", "trauma", "ansiedade", "comportamento", "pessoa", "amizade"},
        "lenses": ["identificação", "revelação pessoal", "consequência emocional"],
        "question": "Você já viveu ou presenciou algo parecido?",
    },
    "humor e entretenimento": {
        "signals": {"humor", "risada", "engraçado", "engracado", "piada", "comédia", "comedia", "filme", "série", "serie", "música", "musica", "jogo", "games"},
        "lenses": ["reação", "quebra de expectativa", "punchline"],
        "question": "Qual foi a reação mais inesperada?",
    },
}


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[dict[str, Any]]
    avg_logprob: float | None = None
    no_speech_prob: float | None = None


@dataclass
class Candidate:
    start: float
    end: float
    text: str
    score: float
    components: dict[str, float] = field(default_factory=dict)
    trigger: str = "curiosidade"
    reason: str = ""
    premise: str = ""
    accepted: bool = False
    rejection: str = ""

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 2)

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": self.duration,
            "text": self.text,
            "score": self.score,
            "components": self.components,
            "trigger": self.trigger,
            "reason": self.reason,
            "premise": self.premise,
            "accepted": self.accepted,
            "rejection": self.rejection,
        }


def run(cmd: list[str], capture: bool = False, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(str(item) for item in cmd), flush=True)
    return subprocess.run(
        cmd,
        text=True,
        check=True,
        capture_output=capture,
        timeout=timeout,
    )


def clean() -> None:
    for path in (WORK, OUTPUT):
        if path.exists():
            shutil.rmtree(path)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)


def urls_from_sources() -> list[str]:
    path = ROOT / "sources.txt"
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def source_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_source(url: str) -> tuple[Path, dict[str, Any]]:
    from yt_dlp import YoutubeDL

    opts = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(SOURCE_DIR / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "restrictfilenames": True,
        "retries": 3,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
    }
    cookiefile = os.environ.get("YOUTUBE_COOKIEFILE", "").strip()
    if cookiefile and Path(cookiefile).is_file():
        opts["cookiefile"] = cookiefile
        opts["extractor_args"] = {"youtube": {"player_client": ["web"]}}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        prepared = Path(ydl.prepare_filename(info))
        candidates = (prepared, prepared.with_suffix(".mp4"), *SOURCE_DIR.glob("*.mp4"))
        source = next((item for item in candidates if item.exists()), None)
        if source is None:
            raise FileNotFoundError("O download terminou sem produzir um MP4.")
        return source, info


def obtain_source(source_url: str | None) -> tuple[Path, dict[str, Any]]:
    local_value = os.environ.get("SOURCE_FILE", "").strip() or (source_url or "")
    if local_value.startswith("file://"):
        local_value = local_value[7:]
    local_path = Path(local_value)
    if local_path.is_file():
        return local_path, {
            "title": os.environ.get("SOURCE_TITLE", local_path.stem),
            "channel": os.environ.get("SOURCE_CHANNEL", "Fonte autorizada no Google Drive"),
            "webpage_url": source_url or "",
        }
    if not source_url:
        raise RuntimeError("Nenhuma fonte autorizada encontrada.")
    return download_source(source_url)


def media_duration(path: Path) -> float:
    result = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], capture=True)
    try:
        return float((result.stdout or "").strip())
    except (TypeError, ValueError):
        return 0.0


def transcribe(source: Path) -> list[Segment]:
    from faster_whisper import WhisperModel

    model_kwargs: dict[str, Any] = {
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": TRANSCRIBE_CPU_THREADS,
        "num_workers": 1,
    }
    cache_dir = os.path.expanduser(os.environ.get("WHISPER_MODEL_CACHE", "").strip())
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        model_kwargs["download_root"] = cache_dir

    print(
        f"Transcrição iniciada: modelo={WHISPER_MODEL}, beam={TRANSCRIBE_BEAM_SIZE}, "
        f"threads={TRANSCRIBE_CPU_THREADS}",
        flush=True,
    )
    started_at = time.monotonic()
    model = WhisperModel(WHISPER_MODEL, **model_kwargs)
    segments, _ = model.transcribe(
        str(source),
        language="pt",
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=TRANSCRIBE_BEAM_SIZE,
        condition_on_previous_text=False,
    )
    result: list[Segment] = []
    last_progress = -TRANSCRIBE_PROGRESS_SECONDS
    segment_count = 0
    for segment in segments:
        words = []
        for word in (getattr(segment, "words", None) or []):
            probability = getattr(word, "probability", None)
            words.append({
                "start": float(word.start),
                "end": float(word.end),
                "word": word.word,
                "probability": float(probability) if probability is not None else None,
            })
        text = segment.text.strip()
        if text:
            avg_logprob = getattr(segment, "avg_logprob", None)
            no_speech_prob = getattr(segment, "no_speech_prob", None)
            result.append(Segment(
                float(segment.start),
                float(segment.end),
                text,
                words,
                float(avg_logprob) if avg_logprob is not None else None,
                float(no_speech_prob) if no_speech_prob is not None else None,
            ))
            segment_count += 1
            if float(segment.end) - last_progress >= TRANSCRIBE_PROGRESS_SECONDS:
                elapsed = time.monotonic() - started_at
                print(
                    f"Transcrição: {float(segment.end):.0f}s processados; "
                    f"{segment_count} segmentos; {elapsed / 60:.1f} min decorridos",
                    flush=True,
                )
                last_progress = float(segment.end)
    if not result:
        raise RuntimeError("A transcrição não retornou fala suficiente.")
    print(
        f"Transcrição concluída: {segment_count} segmentos em "
        f"{(time.monotonic() - started_at) / 60:.1f} min",
        flush=True,
    )
    return result


def words_of(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ]+", text.lower())


def contains_signal(text: str, signals: set[str]) -> int:
    normalized = " ".join(words_of(text))
    hits = 0
    for signal in signals:
        phrase = " ".join(words_of(signal))
        if phrase and re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized):
            hits += 1
    return hits


def first_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return re.split(r"(?<=[.!?…])\s+", cleaned, maxsplit=1)[0] if cleaned else ""


def editorial_trigger(text: str) -> str:
    lower = text.lower()
    if contains_signal(lower, {"briga", "treta", "discord", "discordância", "discordancia", "contra", "errado"}):
        return "treta"
    if contains_signal(lower, HUMOR_WORDS):
        return "humor"
    if contains_signal(lower, EMOTION_WORDS):
        return "emoção"
    if "?" in text or contains_signal(lower, QUESTION_WORDS):
        return "curiosidade"
    if contains_signal(lower, HOOK_WORDS):
        return "surpresa"
    return "curiosidade"


def editorial_reason(trigger: str) -> str:
    return {
        "treta": "Há uma posição clara ou contraste que convida a audiência a reagir.",
        "surpresa": "O trecho traz uma afirmação inesperada ou mudança de perspectiva.",
        "humor": "A entrega cômica ou reação funciona sem depender do episódio inteiro.",
        "emoção": "A história pessoal cria identificação e carga emocional.",
        "curiosidade": "A pergunta ou explicação cria uma promessa clara de resposta.",
    }.get(trigger, "O trecho tem premissa clara e contexto suficiente.")


def analyze_source_profile(
    segments: list[Segment],
    info: dict[str, Any],
    duration: float,
) -> dict[str, Any]:
    """Cria uma leitura editorial específica antes de procurar os cortes."""
    transcript = " ".join(segment.text for segment in segments)
    corpus = f"{info.get('title', '')} {info.get('channel', '')} {transcript}".lower()
    niche_scores: dict[str, int] = {}
    for niche, data in NICHE_SIGNAL_MAP.items():
        niche_scores[niche] = sum(contains_signal(corpus, {signal}) for signal in data["signals"])
    ranked = sorted(niche_scores.items(), key=lambda item: (-item[1], item[0]))
    dominant_niche, dominant_score = ranked[0] if ranked and ranked[0][1] else ("geral", 0)
    profile_data = NICHE_SIGNAL_MAP.get(dominant_niche, {
        "signals": set(),
        "lenses": ["acontecimento completo", "reação", "consequência"],
        "question": "O que você achou desse ponto?",
    })
    words = words_of(transcript)
    questions = transcript.count("?") + contains_signal(transcript, QUESTION_WORDS)
    conflict = contains_signal(transcript, CONFLICT_WORDS)
    words_per_minute = round(len(words) / max(duration / 60.0, 1.0), 1)
    if words_per_minute >= 155:
        pace = "rápido"
    elif words_per_minute <= 105:
        pace = "pausado"
    else:
        pace = "conversacional"
    return {
        "niche": dominant_niche,
        "niche_confidence": round(min(1.0, dominant_score / 8.0), 2),
        "niche_scores": niche_scores,
        "dominant_signals": [
            signal for signal in profile_data["signals"]
            if contains_signal(corpus, {signal})
        ][:12],
        "lenses": profile_data["lenses"],
        "comment_question": profile_data["question"],
        "duration_seconds": round(duration, 2),
        "word_count": len(words),
        "words_per_minute": words_per_minute,
        "pace": pace,
        "question_density": round(questions / max(len(segments), 1), 3),
        "conflict_density": round(conflict / max(len(words), 1), 3),
        "priority_signals": sorted(profile_data["signals"]),
        "method": "perfil inferido do título, canal e transcrição integral; revisão humana continua recomendada",
    }


def candidate_premise(text: str, trigger: str, profile: dict[str, Any] | None = None) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    opening = short_hook(cleaned, 150)
    niche = (profile or {}).get("niche", "geral")
    return f"Em {niche}, o trecho apresenta: {opening}"


def score_text(
    text: str,
    profile: dict[str, Any] | None = None,
) -> tuple[float, dict[str, float], str, str, str, str]:
    tokens = words_of(text)
    lower = text.lower()
    if not tokens:
        return 0.0, {}, "curiosidade", "Trecho sem fala transcrita.", "", "texto sem fala transcrita"

    opening = " ".join(tokens[:24])
    ending = " ".join(tokens[-35:])
    sentence_count = len(re.findall(r"[.!?…]", text))
    trigger = editorial_trigger(text)

    hook = 4.0
    hook += min(9.0, contains_signal(opening, HOOK_WORDS) * 2.4)
    hook += min(5.0, contains_signal(opening, CONFLICT_WORDS) * 1.8)
    hook += 3.0 if "?" in opening else 0.0
    hook += 2.0 if any(char.isdigit() for char in opening) else 0.0
    hook -= 4.0 if lower.startswith(GENERIC_STARTS) else 0.0
    hook = max(0.0, min(25.0, hook))

    tension = 2.0 + min(12.0, contains_signal(lower, CONFLICT_WORDS) * 2.5)
    tension += min(4.0, lower.count("?") * 2.0)
    tension += 2.0 if any(word in lower for word in ("não", "nao", "nunca", "jamais")) else 0.0
    tension = max(0.0, min(20.0, tension))

    payoff = 2.0 + min(8.0, contains_signal(ending, PAYOFF_WORDS) * 2.0)
    payoff += 4.0 if sentence_count >= 3 else 0.0
    payoff += 4.0 if re.search(r"[.!?…]$", text.strip()) else 0.0
    payoff += 2.0 if len(ending.split()) >= 15 else 0.0
    payoff = max(0.0, min(20.0, payoff))

    autonomy = 8.0
    autonomy += 3.0 if not lower.startswith(GENERIC_STARTS) else 0.0
    autonomy += 2.0 if sentence_count >= 2 else 0.0
    autonomy += 2.0 if len(tokens) >= 90 else 0.0
    autonomy = max(0.0, min(15.0, autonomy))

    novelty = 1.0
    novelty += min(4.0, len(re.findall(r"\b\d+[\wÀ-ÿ]*\b", lower)))
    novelty += min(3.0, contains_signal(lower, {"primeira vez", "ninguém sabe", "segredo", "caso", "história", "historia"}) * 1.5)
    novelty += 2.0 if trigger in {"surpresa", "emoção"} else 0.0
    novelty = max(0.0, min(10.0, novelty))

    comments = 0.0
    comments += 2.0 if "?" in text else 0.0
    comments += 1.5 if any(word in lower for word in ("você", "voce", "concorda", "discorda")) else 0.0
    comments += 1.5 if trigger == "treta" else 0.0
    comments = max(0.0, min(5.0, comments))

    profile = profile or {}
    priority_signals = set(profile.get("priority_signals", []))
    context_hits = contains_signal(lower, priority_signals) if priority_signals else 0
    source_fit = max(0.0, min(5.0, 2.0 + min(3.0, context_hits * 0.75)))

    components = {
        "hook_0_2s": round(hook, 2),
        "tension_or_conflict": round(tension, 2),
        "payoff_or_conclusion": round(payoff, 2),
        "autonomy": round(autonomy, 2),
        "novelty": round(novelty, 2),
        "commentability": round(comments, 2),
        "source_fit": round(source_fit, 2),
    }
    raw_score = round(sum(components.values()), 2)
    score = round(min(100.0, raw_score), 2)
    rejection = ""
    premise = candidate_premise(text, trigger, profile)
    return score, components, trigger, editorial_reason(trigger), premise, rejection


def build_candidates(
    segments: list[Segment],
    profile: dict[str, Any] | None = None,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    max_starts = min(len(segments), 1200)
    step = max(1, len(segments) // max_starts)
    for index in range(0, len(segments), step):
        start = segments[index].start
        eligible: list[tuple[int, float]] = []
        for end_index in range(index + 1, min(len(segments), index + 80)):
            duration = segments[end_index].end - start
            if duration > MAX_CLIP_SECONDS:
                break
            if duration >= MIN_CLIP_SECONDS and (re.search(r"[.!?…]$", segments[end_index - 1].text) or duration >= TARGET_CLIP_SECONDS):
                eligible.append((end_index, duration))
        if not eligible:
            continue
        eligible.sort(key=lambda item: abs(item[1] - TARGET_CLIP_SECONDS))
        for end_index, duration in eligible[:2]:
            text = " ".join(item.text for item in segments[index:end_index]).strip()
            score, components, trigger, reason, premise, rejection = score_text(text, profile)
            candidates.append(Candidate(
                start,
                segments[end_index - 1].end,
                text,
                score,
                components,
                trigger,
                reason,
                premise,
                not rejection,
                rejection,
            ))
    unique: dict[tuple[int, int], Candidate] = {}
    for candidate in candidates:
        key = (round(candidate.start), round(candidate.end))
        if key not in unique or candidate.score > unique[key].score:
            unique[key] = candidate
    return sorted(unique.values(), key=lambda item: item.score, reverse=True)


def text_similarity(left: str, right: str) -> float:
    a = set(words_of(left))
    b = set(words_of(right))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def overlaps(left: Candidate, right: Candidate) -> bool:
    intersection = max(0.0, min(left.end, right.end) - max(left.start, right.start))
    return intersection > 0.30 * min(left.duration, right.duration)


def select_candidates(
    segments: list[Segment],
    profile: dict[str, Any] | None = None,
) -> tuple[list[Candidate], list[Candidate]]:
    all_candidates = build_candidates(segments, profile)
    force_top_five = FORCE_TOP_FIVE and MAX_CLIPS >= 5

    if force_top_five or not USE_EDITORIAL_SCORE_GATE:
        # A nota ranqueia; a aprovação depende dos gates objetivos e da revisão final.
        pool = sorted(all_candidates, key=lambda item: (-item.score, item.start))
        for candidate in all_candidates:
            candidate.accepted = False
            candidate.rejection = (
                f"ranqueado abaixo dos selecionados (nota {candidate.score:.2f})"
                if not force_top_five
                else f"não selecionado no Top 5 (nota {candidate.score:.2f})"
            )
    else:
        for candidate in all_candidates:
            if candidate.score < MIN_EDITORIAL_SCORE:
                candidate.accepted = False
                candidate.rejection = f"nota abaixo do mínimo editorial ({candidate.score:.2f} < {MIN_EDITORIAL_SCORE:.2f})"
        pool = [candidate for candidate in all_candidates if candidate.accepted and candidate.score >= MIN_EDITORIAL_SCORE]

    selected: list[Candidate] = []
    deferred: list[Candidate] = []
    trigger_counts: dict[str, int] = {}

    def conflicts(candidate: Candidate) -> bool:
        return any(
            overlaps(candidate, other) or text_similarity(candidate.text, other.text) >= 0.52
            for other in selected
        )

    for candidate in pool:
        if conflicts(candidate):
            candidate.accepted = False
            candidate.rejection = "repetido ou sobreposto a candidato melhor"
            continue
        if trigger_counts.get(candidate.trigger, 0) >= 2:
            deferred.append(candidate)
            continue
        selected.append(candidate)
        candidate.accepted = True
        candidate.rejection = (
            "override Top 5 solicitado"
            if force_top_five and candidate.score < MIN_EDITORIAL_SCORE
            else ""
        )
        trigger_counts[candidate.trigger] = trigger_counts.get(candidate.trigger, 0) + 1
        if len(selected) >= MAX_CLIPS:
            break

    if len(selected) < MAX_CLIPS:
        for candidate in deferred:
            if conflicts(candidate):
                candidate.accepted = False
                candidate.rejection = "repetido ou sobreposto a candidato melhor"
                continue
            selected.append(candidate)
            candidate.accepted = True
            candidate.rejection = (
                "override Top 5 solicitado"
                if force_top_five and candidate.score < MIN_EDITORIAL_SCORE
                else ""
            )
            trigger_counts[candidate.trigger] = trigger_counts.get(candidate.trigger, 0) + 1
            if len(selected) >= MAX_CLIPS:
                break

    for candidate in all_candidates:
        if candidate in selected:
            continue
        if candidate.rejection in {"", "adiado para preservar diversidade editorial"}:
            candidate.accepted = False
            candidate.rejection = "não selecionado após filtro de diversidade"
    selected.sort(key=lambda item: item.start)
    return selected, all_candidates


def ass_time(seconds: float) -> str:
    total_cs = max(0, int(round(seconds * 100)))
    hours, remainder = divmod(total_cs, 360000)
    minutes, remainder = divmod(remainder, 6000)
    whole_seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def ass_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def word_token(value: str) -> str:
    return re.sub(r"[^\wÀ-ÿ]", "", value.lower())


def correct_caption_word(value: str) -> str:
    """Corrige apenas tokens ASR previamente validados, preservando pontuação."""
    match = re.fullmatch(r"([^\wÀ-ÿ]*)([\wÀ-ÿ]+)([^\wÀ-ÿ]*)", value)
    if not match:
        return value
    prefix, token, suffix = match.groups()
    replacement = CAPTION_SAFE_CORRECTIONS.get(word_token(token))
    if not replacement:
        return value
    if replacement == "medo" and token[:1].isupper():
        replacement = replacement.capitalize()
    return f"{prefix}{replacement}{suffix}"


def _caption_context_tokens() -> set[str]:
    """Retorna palavras conhecidas pelo contexto da fonte, sem reescrever a fala."""
    allowed = set(CAPTION_ALLOWED_TOKENS)
    context = " ".join(
        os.environ.get(name, "")
        for name in ("SOURCE_TITLE", "SOURCE_CHANNEL", "SOURCE_NICHE")
    )
    allowed.update(word_token(item) for item in context.split() if word_token(item))
    return allowed


def caption_spelling_issues(labels: list[str]) -> list[str]:
    """Retorna apenas erros explícitos já conhecidos do ASR.

    Palavras raras, nomes, apelidos, marcas, gírias e termos de internet não
    são reprovação automática: sem áudio/contexto humano, tratá-los como erro
    poderia alterar a fala original.
    """
    allowed = _caption_context_tokens()
    return sorted({
        word_token(label)
        for label in labels
        if word_token(label) in CAPTION_SUSPECT_TOKENS
        and word_token(label) not in allowed
    })


def caption_spelling_warnings(labels: list[str]) -> list[str]:
    """Sinaliza palavras raras para revisão humana sem bloquear o corte."""
    allowed = _caption_context_tokens()
    explicit_issues = set(caption_spelling_issues(labels))
    warnings: set[str] = set()
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        zipf_frequency = None

    if not zipf_frequency:
        return []

    for label in labels:
        token = word_token(label)
        if (
            len(token) < 3
            or any(char.isdigit() for char in token)
            or token in allowed
            or token in explicit_issues
        ):
            continue
        if zipf_frequency(token, "pt") < CAPTION_SPELLING_MIN_ZIPF:
            warnings.add(token)
    return sorted(warnings)


def caption_layout(labels: list[str]) -> tuple[int | None, list[int]]:
    """Retorna a quebra usada simultaneamente no QA e no ASS renderizado."""
    text = " ".join(labels).strip()
    if not text:
        return None, []
    if len(text) <= CAPTION_MAX_LINE_CHARS:
        return None, [len(text)]

    options: list[tuple[float, int, list[int]]] = []
    for index in range(1, len(labels)):
        left = " ".join(labels[:index])
        right = " ".join(labels[index:])
        lengths = [len(left), len(right)]
        if max(lengths) <= CAPTION_MAX_LINE_CHARS:
            options.append((abs(lengths[0] - lengths[1]), index, lengths))
    if not options:
        return None, [len(text)]
    _, break_at, lengths = min(options, key=lambda item: item[0])
    return break_at, lengths


def normalize_caption_chunks(
    chunks: list[list[dict[str, Any]]],
) -> list[list[dict[str, Any]]]:
    """Divide blocos longos apenas entre palavras, sem duplicar ou inventar fala."""
    normalized: list[list[dict[str, Any]]] = []
    for original in chunks:
        pending = list(original)
        while pending:
            duration = float(pending[-1]["end"]) - float(pending[0]["start"])
            if duration <= CAPTION_MAX_DURATION or len(pending) <= 1:
                normalized.append(pending)
                break

            options: list[tuple[tuple[float, int, int, int], int, float, float]] = []
            for split_at in range(1, len(pending)):
                left = pending[:split_at]
                right = pending[split_at:]
                left_duration = float(left[-1]["end"]) - float(left[0]["start"])
                right_duration = float(right[-1]["end"]) - float(right[0]["start"])
                if left_duration < CAPTION_MIN_DURATION or right_duration < CAPTION_MIN_DURATION:
                    continue
                left_closes_sentence = bool(re.search(r"[.!?…]$", str(left[-1]["word"])))
                score = (
                    max(left_duration, right_duration),
                    0 if left_closes_sentence else 1,
                    abs(len(left) - len(right)),
                    split_at,
                )
                options.append((score, split_at, left_duration, right_duration))

            if not options:
                # Se o ASR forneceu uma palavra individual com timestamp anômalo,
                # preservamos o bloco para o gate registrar a falha; nunca cortamos
                # uma palavra no meio nem repetimos texto para “passar” no QA.
                normalized.append(pending)
                break

            feasible = [
                option for option in options
                if option[2] <= CAPTION_MAX_DURATION
                and option[3] <= CAPTION_MAX_DURATION
            ]
            _, split_at, _, _ = min(feasible or options, key=lambda item: item[0])
            normalized.append(pending[:split_at])
            pending = pending[split_at:]

    return normalized


def caption_chunks(segments: list[Segment], candidate: Candidate) -> list[list[dict[str, Any]]]:
    words: list[dict[str, Any]] = []
    for segment in segments:
        if segment.end <= candidate.start or segment.start >= candidate.end:
            continue
        source_words = segment.words
        if not source_words:
            tokens = segment.text.split()
            duration = max(segment.end - segment.start, 0.2)
            source_words = [
                {
                    "start": segment.start + duration * index / max(len(tokens), 1),
                    "end": segment.start + duration * (index + 1) / max(len(tokens), 1),
                    "word": token,
                }
                for index, token in enumerate(tokens)
            ]
        for word in source_words:
            text = str(word.get("word", "")).strip()
            if not text:
                continue
            start = max(candidate.start, float(word["start"]))
            end = min(candidate.end, float(word["end"]))
            if end > start:
                corrected_text = correct_caption_word(text)
                words.append({
                    "start": start,
                    "end": end,
                    "word": corrected_text,
                    "source_word": text,
                    "probability": word.get("probability"),
                })

    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        if current:
            projected_duration = float(word["end"]) - float(current[0]["start"])
            current_duration = float(current[-1]["end"]) - float(current[0]["start"])
            projected = [*current, word]
            _, projected_lengths = caption_layout(
                [str(item["word"]).strip() for item in projected]
            )
            word_gap = max(0.0, float(word["start"]) - float(current[-1]["end"]))
            exceeds_duration = (
                projected_duration > CAPTION_MAX_DURATION
                and current_duration >= CAPTION_MIN_DURATION
            )
            exceeds_gap = word_gap > CAPTION_MAX_GAP
            exceeds_words = len(projected) > CAPTION_MAX_WORDS
            exceeds_width = max(projected_lengths, default=0) > CAPTION_MAX_LINE_CHARS
            if exceeds_duration or exceeds_gap or exceeds_words or exceeds_width:
                chunks.append(current)
                current = []
        current.append(word)
        labels = [str(item["word"]).strip() for item in current]
        closes_sentence = bool(re.search(r"[.!?…]$", word["word"]))
        block_duration = float(word["end"]) - float(current[0]["start"])
        ready_sentence = (
            len(current) >= CAPTION_MIN_WORDS
            and closes_sentence
            and block_duration >= CAPTION_MIN_DURATION
        )
        ready_full = len(current) >= CAPTION_MAX_WORDS and block_duration >= CAPTION_MIN_DURATION
        too_long = len(current) >= CAPTION_MIN_WORDS and block_duration >= CAPTION_MAX_DURATION
        _, line_lengths = caption_layout(labels)
        if ready_full or ready_sentence or too_long or max(line_lengths, default=0) > CAPTION_MAX_LINE_CHARS:
            chunks.append(current)
            current = []

    if current:
        current_duration = float(current[-1]["end"]) - float(current[0]["start"])
        if chunks and len(current) < CAPTION_MIN_WORDS and current_duration < CAPTION_MIN_DURATION:
            merged = [*chunks[-1], *current]
            merged_duration = float(merged[-1]["end"]) - float(merged[0]["start"])
            _, merged_lengths = caption_layout([str(item["word"]).strip() for item in merged])
            if (
                len(merged) <= CAPTION_MAX_WORDS + CAPTION_SHORT_TAIL_WORD_SLACK
                and merged_duration <= CAPTION_MAX_DURATION
                and max(merged_lengths, default=0) <= CAPTION_MAX_LINE_CHARS
            ):
                chunks[-1] = merged
            else:
                chunks.append(current)
        else:
            chunks.append(current)
    return normalize_caption_chunks(chunks)

def validate_captions(segments: list[Segment], candidate: Candidate, margin_v: int) -> dict[str, Any]:
    """Audita tempo, continuidade, largura e posição das legendas antes da renderização."""
    chunks = caption_chunks(segments, candidate)
    issues: list[str] = []
    warnings: list[str] = []
    intervals: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    previous_end: float | None = None

    if not chunks:
        issues.append("nenhum bloco de legenda foi gerado")

    for index, chunk in enumerate(chunks, 1):
        for item in chunk:
            original = str(item.get("source_word", item.get("word", ""))).strip()
            corrected = str(item.get("word", "")).strip()
            if original and corrected and original != corrected:
                correction = {"block": index, "from": original, "to": corrected}
                if correction not in corrections:
                    corrections.append(correction)
        labels = [str(item.get("word", "")).strip() for item in chunk if str(item.get("word", "")).strip()]
        text = " ".join(labels)
        suspect_tokens = caption_spelling_issues(labels)
        if suspect_tokens:
            issues.append(
                f"bloco {index} contém erro conhecido de transcrição/ortografia: {', '.join(suspect_tokens)}"
            )
        spelling_warnings = caption_spelling_warnings(labels)
        if spelling_warnings:
            warnings.append(
                f"bloco {index} contém palavra rara/nome/gíria para revisão humana: {', '.join(spelling_warnings)}"
            )
        low_confidence_tokens = sorted({
            word_token(str(item.get("word", "")))
            for item in chunk
            if item.get("probability") is not None
            and float(item.get("probability")) < CAPTION_MIN_WORD_PROBABILITY
            and word_token(str(item.get("word", "")))
        })
        if low_confidence_tokens:
            warnings.append(
                f"bloco {index} contém fala com baixa confiança do ASR para revisão: {', '.join(low_confidence_tokens)}"
            )
        start = max(0.0, float(chunk[0]["start"]) - candidate.start) if chunk else 0.0
        end = max(start, float(chunk[-1]["end"]) - candidate.start) if chunk else start
        duration = end - start

        if not labels:
            issues.append(f"bloco {index} sem texto")
            continue
        if duration < CAPTION_MIN_DURATION:
            issues.append(f"bloco {index} rápido demais ({duration:.2f}s)")
        if duration > CAPTION_MAX_DURATION:
            issues.append(f"bloco {index} longo demais ({duration:.2f}s)")
        if start < -CAPTION_SYNC_TOLERANCE or end > candidate.duration + CAPTION_SYNC_TOLERANCE:
            issues.append(f"bloco {index} fora do intervalo do corte")
        if previous_end is not None:
            gap = start - previous_end
            if gap < -0.03:
                issues.append(f"blocos {index - 1} e {index} sobrepostos ({gap:.2f}s)")
            elif gap > CAPTION_MAX_GAP:
                warnings.append(f"pausa natural entre blocos {index - 1} e {index} ({gap:.2f}s)")

        _, line_lengths = caption_layout(labels)
        if len(line_lengths) > 2 or max(line_lengths, default=0) > CAPTION_MAX_LINE_CHARS:
            issues.append(f"bloco {index} ultrapassa a largura segura ({line_lengths})")

        intervals.append({
            "index": index,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(duration, 3),
            "text": text,
            "line_lengths": line_lengths,
        })
        previous_end = end

    if not 160 <= margin_v <= 420:
        issues.append(f"margem vertical fora da área segura ({margin_v}px)")
    if candidate.duration <= 0:
        issues.append("duração do corte inválida")

    return {
        "passed": not issues,
        "issues": issues,
        "warnings": warnings,
        "corrections": corrections,
        "review_required": bool(warnings or corrections),
        "blocks": len(intervals),
        "max_line_chars": max((max(item["line_lengths"], default=0) for item in intervals), default=0),
        "margin_v": margin_v,
        "alignment": "center-bottom",
        "safe_area": {"margin_left": 70, "margin_right": 70, "margin_bottom": margin_v},
        "sync_tolerance_seconds": CAPTION_SYNC_TOLERANCE,
        "intervals": intervals,
    }


def render_caption(words: list[dict[str, Any]]) -> str:
    labels = [item["word"].strip() for item in words]
    cleaned = [word_token(label) for label in labels]
    priority = HOOK_WORDS | CONFLICT_WORDS | {"porque", "porquê", "por que", "você", "voce"}
    keyword_index = next(
        (index for index, token in enumerate(cleaned) if token in priority),
        max(range(len(labels)), key=lambda index: len(cleaned[index]), default=0),
    )
    break_at, _ = caption_layout(labels)
    rendered: list[str] = []
    for index, label in enumerate(labels):
        if break_at == index:
            rendered.append(r"\N")
        token = ass_escape(label)
        rendered.append(
            # Cobre oficial da identidade: #B85A3C em ordem BGR do ASS.
            f"{{\\c&H003C5AB8&}}{token}{{\\c&H00F4F5F5&}}"
            if index == keyword_index
            else token
        )
        if index < len(labels) - 1 and break_at != index + 1:
            rendered.append(" ")
    return "".join(rendered)


def write_ass(segments: list[Segment], candidate: Candidate, path: Path, margin_v: int) -> None:
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Branco quente #F5F5F4, contorno preto #050505 e caixa semitransparente discreta.
        f"Style: Default,{CAPTION_FONT_NAME},{CAPTION_FONT_SIZE},&H00F4F5F5,&H00F4F5F5,&H00050505,&H99050505,-1,0,0,0,100,100,0,0,1,3,1,2,70,70,{margin_v},1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for chunk in caption_chunks(segments, candidate):
        start = max(0.0, float(chunk[0]["start"]) - candidate.start)
        end = max(start + 0.08, float(chunk[-1]["end"]) - candidate.start)
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{render_caption(chunk)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_filter_complex(caption_path: str) -> str:
    """
    Mantém as cores originais da fonte. O tratamento Corte Fino fica restrito
    à composição vertical, ao fundo desfocado e aos elementos da HUD.
    """
    return (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=22[bg];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{caption_path}':original_size=1080x1920,"
        # Assinatura superior direita: CORTE / FINO, compacta e discreta.
        "drawbox=x=iw-300:y=34:w=268:h=56:color=0x050505@0.72:t=fill,"
        "drawbox=x=iw-300:y=34:w=3:h=56:color=0xB85A3C@0.96:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='CORTE':fontcolor=0xF5F5F4@0.96:fontsize=22:x=w-286:y=49,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='/':fontcolor=0xB85A3C@0.96:fontsize=24:x=w-215:y=47,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='FINO':fontcolor=0xF5F5F4@0.96:fontsize=22:x=w-194:y=49[v]"
    )


def render_clip(source: Path, captions: Path, candidate: Candidate, output: Path) -> None:
    caption_path = str(captions).replace(":", "\\:")
    filter_complex = build_filter_complex(caption_path)
    run([
        "ffmpeg", "-y", "-ss", f"{candidate.start:.3f}", "-i", str(source), "-t", f"{candidate.duration:.3f}",
        "-filter_complex", filter_complex, "-map", "[v]", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", "-avoid_negative_ts", "make_zero", str(output),
    ])


def render_and_validate(
    source: Path,
    captions: Path,
    candidate: Candidate,
    output: Path,
) -> dict[str, Any]:
    """Renderiza em arquivo temporário e só publica o MP4 depois do QA técnico."""
    temporary = output.with_name(f"{output.stem}.part{output.suffix}")
    if temporary.exists():
        temporary.unlink()
    render_clip(source, captions, candidate, temporary)
    qa = validate_video(temporary, candidate.duration)
    if qa["passed"]:
        temporary.replace(output)
        qa["file"] = output.name
    else:
        temporary.unlink(missing_ok=True)
    return qa


def validate_video(path: Path, expected_duration: float) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], capture=True)
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float((data.get("format") or {}).get("duration") or 0)
    decode_ok = True
    try:
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture=True, timeout=180)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        decode_ok = False
    checks = {
        "exists": path.is_file() and path.stat().st_size > 50_000,
        "video_stream": video is not None,
        "audio_stream": audio is not None,
        "resolution_1080x1920": bool(video and video.get("width") == 1080 and video.get("height") == 1920),
        "h264": bool(video and video.get("codec_name") == "h264"),
        "duration_reasonable": abs(duration - expected_duration) <= 3.0 and duration >= MIN_CLIP_SECONDS - 2,
        "decodable": decode_ok,
    }
    return {
        "file": path.name,
        "duration": round(duration, 3),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "checks": checks,
        "passed": all(checks.values()),
    }


def ffmpeg_path(path: Path) -> str:
    """Escapa um caminho Linux para uso dentro de um filtro FFmpeg."""
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def thumbnail_headline(text: str, limit: int = 42) -> str:
    """Gera manchete curta a partir da fala real, sem inventar copy editorial."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    sentence = first_sentence(cleaned) or cleaned
    if len(sentence) > limit:
        sentence = sentence[:limit].rsplit(" ", 1)[0].rstrip(" ,;:!?…") + "…"
    words = sentence.upper().split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > 21 and len(lines) < 1:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines[:2]) or "CORTE FINO"


def render_thumbnail(source: Path, candidate: Candidate, output: Path, number: int) -> dict[str, Any]:
    """Cria a thumb com um frame real e um esqueleto determinístico de marca."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.stem}.part{output.suffix}")
    temporary.unlink(missing_ok=True)
    headline = thumbnail_headline(candidate.text)
    headline_path = WORK / f"thumb_{number:02d}.txt"
    headline_path.write_text(headline, encoding="utf-8")
    headline_file = ffmpeg_path(headline_path)
    filter_complex = (
        "[0:v]split=2[bg][fg];"
        f"[bg]scale={THUMB_WIDTH}:{THUMB_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={THUMB_WIDTH}:{THUMB_HEIGHT},gblur=sigma=26,eq=brightness=-0.10[bg];"
        f"[fg]scale=980:1080:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:{THUMB_FRAME_Y},"
        "drawbox=x=42:y=42:w=996:h=1836:color=0xF5F5F4@0.82:t=2,"
        "drawbox=x=58:y=1062:w=964:h=300:color=0x050505@0.82:t=fill,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:"
        f"textfile='{headline_file}':fontcolor=0xF5F5F4@0.98:fontsize={THUMB_FONT_SIZE}:"
        f"line_spacing=8:x=86:y={THUMB_HEADLINE_Y},"
        "drawbox=x=58:y=58:w=4:h=76:color=0xB85A3C@0.98:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='CORTE':fontcolor=0xF5F5F4@0.96:fontsize=24:x=82:y=72,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='/':fontcolor=0xB85A3C@0.96:fontsize=26:x=158:y=70,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='FINO':fontcolor=0xF5F5F4@0.96:fontsize=24:x=180:y=72,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf:text='C/F':fontcolor=0xB85A3C@0.96:fontsize=30:x=82:y=1800"
    )
    frame_time = candidate.start + max(0.25, min(candidate.duration * 0.5, candidate.duration - 0.25))
    run([
        "ffmpeg", "-y", "-ss", f"{frame_time:.3f}", "-i", str(source), "-frames:v", "1",
        "-vf", filter_complex, "-an", "-c:v", "png", str(temporary),
    ])
    qa = validate_thumbnail(temporary, headline)
    if qa["passed"]:
        temporary.replace(output)
        qa["file"] = output.name
    else:
        temporary.unlink(missing_ok=True)
    qa["headline"] = headline
    qa["frame_time"] = round(frame_time, 3)
    return qa


def validate_thumbnail(path: Path, headline: str) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], capture=True)
    data = json.loads(result.stdout or "{}")
    image = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    checks = {
        "exists": path.is_file() and path.stat().st_size > 20_000,
        "png": bool(image and image.get("codec_name") == "png"),
        "resolution_1080x1920": bool(image and image.get("width") == THUMB_WIDTH and image.get("height") == THUMB_HEIGHT),
        "headline_present": bool(headline.strip()),
    }
    try:
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        checks["decodable"] = False
    else:
        checks["decodable"] = True
    return {
        "stage": "thumbnail",
        "width": image.get("width") if image else None,
        "height": image.get("height") if image else None,
        "checks": checks,
        "passed": all(checks.values()),
    }


def short_hook(text: str, limit: int = 82) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    first = first_sentence(cleaned)
    hook = first if len(first) >= 18 else " ".join(cleaned.split()[:14])
    return hook if len(hook) <= limit else hook[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def rights_info() -> dict[str, Any]:
    status = os.environ.get("SOURCE_RIGHTS_STATUS", "REVISÃO DE DIREITOS — confirme autorização antes de publicar").strip()
    authorized = status.upper().startswith(("AUTHORIZED", "AUTORIZADO", "LICENSED", "LICENCIADO", "CC ", "CREATIVE COMMONS"))
    return {
        "status": status,
        "license": os.environ.get("SOURCE_LICENSE", "").strip(),
        "license_url": os.environ.get("SOURCE_LICENSE_URL", "").strip(),
        "attribution": os.environ.get("SOURCE_ATTRIBUTION", "").strip(),
        "authorized_signal": authorized,
        "publication_gate": "manual_review_required",
        "note": "Autorização e licença devem ser conferidas antes da postagem; crédito sozinho não substitui permissão.",
    }


def enrich_clip(
    clip: dict[str, Any],
    source_url: str | None,
    info: dict[str, Any],
    rights: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = profile or {}
    hook = short_hook(str(clip.get("text", "")))
    title = info.get("title") or "Fonte não identificada"
    channel = info.get("channel") or info.get("uploader") or "Canal não identificado"
    source_link = source_url or info.get("webpage_url") or ""
    hashtags = ["#CorteFino", "#Shorts", "#Cortes"]
    corpus = f"{os.environ.get('SOURCE_NICHE', '')} {title} {channel} {clip.get('text', '')}".lower()
    def has_signal(signal: str) -> bool:
        pattern = rf"(?<![\wÀ-ÿ]){re.escape(signal)}(?![\wÀ-ÿ])"
        return re.search(pattern, corpus) is not None

    for signal, tag in (
        ("futebol", "#Futebol"), ("humor", "#Humor"), ("tecnologia", "#Tecnologia"),
        ("negócios", "#Negocios"), ("negocios", "#Negocios"), ("finanças", "#Financas"),
        ("financas", "#Financas"), ("relacionamento", "#Relacionamento"),
        ("história", "#Historias"), ("historia", "#Historias"), ("true crime", "#TrueCrime"),
        ("inteligência artificial", "#InteligenciaArtificial"), ("ia", "#InteligenciaArtificial"),
        ("podcast", "#Podcast"),
    ):
        if has_signal(signal) and tag not in hashtags:
            hashtags.append(tag)
    hashtags = hashtags[:5]
    attribution = f"Fonte: {title} — {channel}."
    if source_link:
        attribution += f" {source_link}"
    if rights["license"]:
        attribution += f" Licença declarada: {rights['license']}."
    if rights["license_url"]:
        attribution += f" {rights['license_url']}"
    enriched = dict(clip)
    enriched.update({
        "youtube_title": f"{hook} | Corte Fino #Shorts",
        "youtube_description": f"{hook}\n\n{attribution}\nEdição: Corte Fino. Verifique a autorização antes de publicar.",
        "tiktok_caption": f"{hook}\n\n{attribution}\n\n{' '.join(hashtags)}",
        "hashtags": hashtags,
        "comment_question": profile.get("comment_question") or {
            "treta": "Quem está certo nessa discussão? Explique nos comentários.",
            "surpresa": "Você já tinha ouvido essa versão? O que achou?",
            "humor": "Qual foi a parte mais engraçada para você?",
            "emoção": "Essa história te lembrou alguém ou alguma situação?",
            "curiosidade": "Você concorda com essa explicação? Por quê?",
        }.get(clip.get("trigger"), "Você concorda com essa explicação? Por quê?"),
        "niche": profile.get("niche", "geral"),
        "editorial_lenses": profile.get("lenses", []),
        "source": {"title": title, "channel": channel, "url": source_link},
        "rights_status": rights["status"],
    })
    return enriched


def write_reports(
    source_url: str | None,
    source_hash: str | None,
    info: dict[str, Any],
    clips: list[dict[str, Any]],
    candidates: list[Candidate],
    qa: list[dict[str, Any]],
    error: str | None = None,
    profile: dict[str, Any] | None = None,
) -> None:
    rights = rights_info()
    enriched = [enrich_clip(clip, source_url, info, rights, profile) for clip in clips]
    if error and error.startswith("Nenhum momento"):
        status = "EDITORIAL_EMPTY"
    elif error and (
        error.startswith("Nenhum corte passou")
        or error.startswith("Top 5")
        or error.startswith("Não foi possível formar exatamente")
    ):
        status = "TOP_FIVE_INCOMPLETE"
    elif error and error.startswith("DIREITOS_PENDENTES"):
        status = "RIGHTS_PENDING"
    elif error and error.startswith("QA de legenda"):
        status = "CAPTION_REVIEW_REQUIRED"
    elif error:
        status = "TECHNICAL_FAILURE"
    elif enriched:
        status = "READY_FOR_HUMAN_REVIEW"
    else:
        status = "EDITORIAL_EMPTY"
    source_title = info.get("title")
    source_channel = info.get("channel") or info.get("uploader")
    report = {

        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "legacy_status": "READY_FOR_REVIEW" if status == "READY_FOR_HUMAN_REVIEW" else status,
        "execution": {
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_sha": os.environ.get("GITHUB_SHA", ""),
            "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        },
        "source_title": source_title,
        "source_channel": source_channel,
        "rights_status": rights["status"],
        "analysis_profile": profile or {},
        "source": {
            "url": source_url,
            "title": source_title,
            "channel": source_channel,
            "fingerprint_sha256": source_hash,
        },
        "rights": rights,
        "editorial": {
            "minimum_score": MIN_EDITORIAL_SCORE,
            "score_gate_enabled": USE_EDITORIAL_SCORE_GATE,
            "require_exact_top_five": REQUIRE_EXACT_TOP_FIVE,
            "selection_mode": (
                "CLOSED_TOP_FIVE" if REQUIRE_EXACT_TOP_FIVE
                else "FORCE_TOP_FIVE" if FORCE_TOP_FIVE
                else "RANK_ONLY_WITH_OBJECTIVE_GATES" if not USE_EDITORIAL_SCORE_GATE
                else "MIN_SCORE_GATE"
            ),
            "override_minimum_score": FORCE_TOP_FIVE,
            "approved_count": len(enriched),
            "candidate_count": len(candidates),
            "rule": (
                "Top 5 fechado: selecionar exatamente os cinco melhores candidatos disponíveis; sem substituição após a seleção."
                if REQUIRE_EXACT_TOP_FIVE
                else "Só entra o que vale o corte."
            ),
        },
        "clips": enriched,
        "qa": qa,
        "error": error,
        "note": "A seleção usa heurísticas editoriais e não promete viralização. A publicação permanece manual.",
        "editing": {
            "format": "9:16 — 1080x1920",
            "audio": "áudio original preservado em AAC",
            "captions": "ASS dinâmico, no máximo duas linhas de até 32 caracteres, sincronização auditada por palavra, gate ortográfico/confiança do ASR e margem segura",
            "caption_gate": {
                "spelling_checker": "wordfreq pt quando disponível + lista de risco",
                "minimum_word_probability": CAPTION_MIN_WORD_PROBABILITY,
                "manual_correction_policy": "não inventar nem corrigir a fala automaticamente; reprovar para revisão",
            },
            "framing": "quadro completo com fundo desfocado e cores originais preservadas para proteger rostos e cenário",
            "branding": "HUD CORTE / FINO no canto superior direito; cores da fonte preservadas; sem vinheta e sem música adicionada",
            "thumbnails": {
                "count": len(enriched),
                "format": "PNG 1080x1920",
                "source_policy": "frame real do corte; nenhuma face ou identidade gerada/alterada",
                "skeleton": "frame real + fundo desfocado + headline fiel em branco/cobre + moldura fina + marca CORTE / FINO + C/F",
            },
        },
    }
    (OUTPUT / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "candidate_scores.json").write_text(json.dumps([candidate.as_dict() for candidate in candidates], ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Corte Fino — relatório editorial e técnico", "",
        f"Status: {status}",
        f"Fonte: {source_title or 'não identificada'}",
        f"Canal: {source_channel or 'não identificado'}",
        f"URL: {source_url or 'não informada'}",
        f"Fingerprint SHA-256: {source_hash or 'não calculado'}",
        f"**Perfil individual:** {(profile or {}).get('niche', 'geral')}",
        f"**Ritmo da fonte:** {(profile or {}).get('pace', 'não calculado')} | {(profile or {}).get('words_per_minute', 'n/d')} palavras/min",
        f"**Lentes recomendadas:** {', '.join((profile or {}).get('lenses', [])) or 'acontecimento completo'}",
        "",
        (
            "**Critério editorial:** Top 5 fechado; a nota ordena os cinco candidatos e os gates objetivos preservam continuidade, legenda e QA."
            if REQUIRE_EXACT_TOP_FIVE
            else (
                "**Critério editorial:** Top 5 solicitado; a nota ranqueia e os gates objetivos preservam continuidade, legenda e QA."
                if FORCE_TOP_FIVE
                else (
                    "**Critério editorial:** nota usada para ranqueamento; por padrão, não bloqueia nichos ou fontes de menor pontuação. "
                    "Gates objetivos continuam obrigatórios."
                    if not USE_EDITORIAL_SCORE_GATE
                    else "**Critério editorial:** somente candidatos com nota mínima configurada entram na seleção."
                )
            )
        ),
        f"**Cortes aprovados:** {len(enriched)}/{MAX_CLIPS}",
        "**Regra operacional:** Top 5 fechado; nenhuma opção reserva substitui um dos cinco candidatos.",
        "",
        f"**Direitos:** {rights['status']}",
        "**Publicação:** revisão manual obrigatória",
        "",
    ]
    for index, clip in enumerate(enriched, 1):
        lines.extend([
            f"## Corte {index}",
            f"- Vídeo: {clip['file']}",
            f"- Thumbnail pareada: {clip.get('thumbnail_file', 'não gerada')}",
            f"- Tempo original: {clip['start']:.2f}s–{clip['end']:.2f}s",
            f"- Duração: {clip['duration']:.2f}s",
            f"- Nota editorial: {clip['score']}/100",
            f"- Gatilho: {clip['trigger']}",
            f"- Premissa: {clip.get('premise', '')}",
            f"- Motivo: {clip['editorial_reason']}",
            f"- Título YouTube: {clip['youtube_title']}",
            f"- Pergunta: {clip['comment_question']}",
            f"- Texto-base: {clip['text']}",
            "",
        ])
    if error:
        lines.extend(["## Problema", error, ""])
    (OUTPUT / "relatorio.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    clean()
    source_url = os.environ.get("SOURCE_URL", "").strip() or (urls_from_sources() or [None])[0]
    info: dict[str, Any] = {}
    clips: list[dict[str, Any]] = []
    candidates: list[Candidate] = []
    qa: list[dict[str, Any]] = []
    source_hash: str | None = None
    error: str | None = None
    profile: dict[str, Any] = {}
    success = False
    try:
        source, info = obtain_source(source_url)
        source_hash = source_fingerprint(source)
        duration = media_duration(source)
        if duration <= 0:
            raise RuntimeError("Não foi possível determinar a duração da fonte.")
        if duration > MAX_SOURCE_DURATION_SECONDS:
            raise RuntimeError(
                f"Fonte longa demais: {duration / 60:.1f} minutos; "
                f"limite configurado: {MAX_SOURCE_DURATION_SECONDS / 60:.0f} minutos."
            )

        segments = transcribe(source)
        profile = analyze_source_profile(segments, info, duration)
        selected, candidates = select_candidates(segments, profile)
        if not selected:
            raise RuntimeError(
                "Nenhum momento adequado foi encontrado pelas regras editoriais e técnicas."
            )

        # Top 5 fechado: depois da seleção, nenhum candidato reserva pode
        # substituir um dos cinco. Isso preserva a decisão editorial da rodada.
        if REQUIRE_EXACT_TOP_FIVE and len(selected) < MAX_CLIPS:
            raise RuntimeError(
                f"Não foi possível formar exatamente {MAX_CLIPS} candidatos editoriais "
                f"(encontrados: {len(selected)})."
            )
        candidate_pool = selected[:MAX_CLIPS]
        accepted_candidates: list[Candidate] = []

        for candidate in candidate_pool:
            if len(clips) >= MAX_CLIPS:
                break
            if any(
                overlaps(candidate, other)
                or text_similarity(candidate.text, other.text) >= 0.52
                for other in accepted_candidates
            ):
                raise RuntimeError(
                    "O Top 5 fechado contém candidatos repetidos ou sobrepostos; "
                    "nenhuma opção reserva será usada."
                )

            clip_number = len(clips) + 1
            captions = WORK / f"vertical_{clip_number:02d}.ass"
            output = CLIPS_DIR / f"corte_fino_{clip_number:02d}_vertical.mp4"
            write_ass(segments, candidate, captions, CAPTION_MARGIN_V)
            caption_qa = validate_captions(segments, candidate, CAPTION_MARGIN_V)
            if not caption_qa["passed"]:
                candidate.accepted = False
                candidate.rejection = "reprovado no gate automático de legenda"
                qa.append({
                    "platform": "vertical_shared",
                    "clip": clip_number,
                    "stage": "candidate_rejected",
                    "fatal": True,
                    "passed": False,
                    "candidate": candidate.as_dict(),
                    "caption_qa": caption_qa,
                })
                raise RuntimeError(
                    f"Top 5 fechado reprovou no gate de legenda no corte {clip_number}; "
                    "nenhum candidato reserva será usado."
                )

            clip_qa = render_and_validate(source, captions, candidate, output)
            clip_qa["caption_qa"] = caption_qa
            clip_qa["stage"] = "rendered_clip"
            clip_qa["fatal"] = not clip_qa["passed"]
            qa.append({"platform": "vertical_shared", "clip": clip_number, **clip_qa})
            if not clip_qa["passed"]:
                candidate.accepted = False
                candidate.rejection = "reprovado no QA técnico do arquivo final"
                raise RuntimeError(
                    f"Top 5 fechado reprovou no QA técnico no corte {clip_number}; "
                    "nenhum candidato reserva será usado."
                )

            thumbnail_output = THUMBS_DIR / f"corte_fino_{clip_number:02d}_thumb.png"
            thumbnail_qa = render_thumbnail(source, candidate, thumbnail_output, clip_number)
            qa.append({
                "platform": "vertical_shared",
                "clip": clip_number,
                "stage": "thumbnail",
                "fatal": not thumbnail_qa["passed"],
                **thumbnail_qa,
            })
            if not thumbnail_qa["passed"]:
                candidate.accepted = False
                candidate.rejection = "reprovado no QA técnico da thumbnail"
                raise RuntimeError(
                    f"Top 5 fechado reprovou na thumbnail do corte {clip_number}; "
                    "nenhum candidato reserva será usado."
                )

            relative_output = str(output.relative_to(OUTPUT))
            relative_thumbnail = str(thumbnail_output.relative_to(OUTPUT))
            clips.append({
                "file": relative_output,
                "thumbnail_file": relative_thumbnail,
                "render_format": "vertical_9x16_shared",
                "start": candidate.start,
                "end": candidate.end,
                "duration": candidate.duration,
                "score": candidate.score,
                "components": candidate.components,
                "trigger": candidate.trigger,
                "editorial_reason": candidate.reason,
                "text": candidate.text,
            })
            candidate.accepted = True
            candidate.rejection = ""
            accepted_candidates.append(candidate)

        if REQUIRE_EXACT_TOP_FIVE and len(clips) != MAX_CLIPS:
            raise RuntimeError(
                f"Top 5 incompleto: {len(clips)}/{MAX_CLIPS} cortes aprovados; "
                "nenhum candidato reserva será usado."
            )
        if not clips:
            raise RuntimeError(
                "Nenhum corte passou pelo gate automático de legenda, vídeo e thumbnail; "
                "a fonte permanece disponível para nova tentativa."
            )
        success = True
    except Exception as exc:
        error = str(exc)
        print(f"ERRO: {error}", file=sys.stderr)
        # Rodada vazia é um resultado editorial válido e não deve falhar o workflow.
        if error.startswith("Nenhum momento"):
            success = True
    finally:
        if OUTPUT.exists():
            write_reports(source_url, source_hash, info, clips, candidates, qa, error, profile)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

