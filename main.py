from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_CLIPS = int(os.environ.get("MAX_CLIPS", "5"))
MIN_EDITORIAL_SCORE = 0.0  # compatibilidade: a nota apenas ordena candidatos; nunca bloqueia a geração
MIN_CLIP_SECONDS = int(os.environ.get("MIN_CLIP_SECONDS", "45"))
MAX_CLIP_SECONDS = int(os.environ.get("MAX_CLIP_SECONDS", "90"))
TARGET_CLIP_SECONDS = int(os.environ.get("TARGET_CLIP_SECONDS", "68"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base").strip() or "base"
MAX_SOURCE_DURATION_SECONDS = int(os.environ.get("MAX_SOURCE_DURATION_SECONDS", "10800"))
CAPTION_MIN_WORDS = 3
CAPTION_MAX_WORDS = 6
CAPTION_FONT_SIZE = int(os.environ.get("CAPTION_FONT_SIZE", "48"))
CAPTION_MARGIN_V = int(os.environ.get("CAPTION_MARGIN_V", "220"))
YOUTUBE_CAPTION_MARGIN_V = int(os.environ.get("YOUTUBE_CAPTION_MARGIN_V", str(CAPTION_MARGIN_V)))
TIKTOK_CAPTION_MARGIN_V = int(os.environ.get("TIKTOK_CAPTION_MARGIN_V", str(CAPTION_MARGIN_V + 80)))
ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"
SOURCE_DIR = WORK / "source"
CLIPS_DIR = OUTPUT / "clips"
YOUTUBE_DIR = CLIPS_DIR
TIKTOK_DIR = CLIPS_DIR

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


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[dict[str, Any]]


@dataclass
class Candidate:
    start: float
    end: float
    text: str
    score: float
    components: dict[str, float] = field(default_factory=dict)
    trigger: str = "curiosidade"
    reason: str = ""
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
    YOUTUBE_DIR.mkdir(parents=True, exist_ok=True)
    TIKTOK_DIR.mkdir(parents=True, exist_ok=True)


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

    model_kwargs: dict[str, Any] = {"device": "cpu", "compute_type": "int8"}
    cache_dir = os.environ.get("WHISPER_MODEL_CACHE", "").strip()
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        model_kwargs["download_root"] = cache_dir
    model = WhisperModel(WHISPER_MODEL, **model_kwargs)
    segments, _ = model.transcribe(
        str(source),
        language="pt",
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )
    result: list[Segment] = []
    for segment in segments:
        words = [
            {"start": float(word.start), "end": float(word.end), "word": word.word}
            for word in (getattr(segment, "words", None) or [])
        ]
        text = segment.text.strip()
        if text:
            result.append(Segment(float(segment.start), float(segment.end), text, words))
    if not result:
        raise RuntimeError("A transcrição não retornou fala suficiente.")
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


def score_text(text: str) -> tuple[float, dict[str, float], str, str, str]:
    tokens = words_of(text)
    lower = text.lower()
    if not tokens:
        return 0.0, {}, "curiosidade", "Trecho sem fala transcrita.", "texto sem fala transcrita"

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

    components = {
        "hook_0_2s": round(hook, 2),
        "tension_or_conflict": round(tension, 2),
        "payoff_or_conclusion": round(payoff, 2),
        "autonomy": round(autonomy, 2),
        "novelty": round(novelty, 2),
        "commentability": round(comments, 2),
    }
    raw_score = round(sum(components.values()), 2)
    score = round((raw_score / 95.0) * 100.0, 2)
    if False:
        rejection = f"nota {score:.2f} abaixo do mínimo {MIN_EDITORIAL_SCORE:.2f}"
    elif False:
        rejection = "conclusão ou payoff insuficiente"
    elif False:
        rejection = "gancho inicial insuficiente"
    elif False:
        rejection = "depende de contexto externo"
    else:
        rejection = ""
    return score, components, trigger, editorial_reason(trigger), rejection


def build_candidates(segments: list[Segment]) -> list[Candidate]:
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
            score, components, trigger, reason, rejection = score_text(text)
            candidates.append(Candidate(start, segments[end_index - 1].end, text, score, components, trigger, reason, not rejection, rejection))
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


def select_candidates(segments: list[Segment]) -> tuple[list[Candidate], list[Candidate]]:
    all_candidates = build_candidates(segments)
    approved = [candidate for candidate in all_candidates if candidate.accepted]
    selected: list[Candidate] = []
    deferred: list[Candidate] = []
    trigger_counts: dict[str, int] = {}

    def conflicts(candidate: Candidate) -> bool:
        return any(
            overlaps(candidate, other) or text_similarity(candidate.text, other.text) >= 0.52
            for other in selected
        )

    for candidate in approved:
        if conflicts(candidate):
            candidate.accepted = False
            candidate.rejection = "repetido ou sobreposto a candidato melhor"
            continue
        if trigger_counts.get(candidate.trigger, 0) >= 2:
            deferred.append(candidate)
            continue
        selected.append(candidate)
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
            trigger_counts[candidate.trigger] = trigger_counts.get(candidate.trigger, 0) + 1
            if len(selected) >= MAX_CLIPS:
                break

    for candidate in deferred:
        if candidate not in selected and candidate.accepted:
            candidate.accepted = False
            candidate.rejection = "adiado para preservar diversidade editorial"
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
                {"start": segment.start + duration * index / max(len(tokens), 1), "end": segment.start + duration * (index + 1) / max(len(tokens), 1), "word": token}
                for index, token in enumerate(tokens)
            ]
        for word in source_words:
            text = str(word.get("word", "")).strip()
            if not text:
                continue
            start = max(candidate.start, float(word["start"]))
            end = min(candidate.end, float(word["end"]))
            if end > start:
                words.append({"start": start, "end": end, "word": text})
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        current.append(word)
        plain = " ".join(item["word"] for item in current)
        closes_sentence = bool(re.search(r"[.!?…]$", word["word"]))
        if len(current) >= CAPTION_MAX_WORDS or (len(current) >= CAPTION_MIN_WORDS and closes_sentence) or len(plain) >= 38:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def render_caption(words: list[dict[str, Any]]) -> str:
    labels = [item["word"].strip() for item in words]
    cleaned = [word_token(label) for label in labels]
    priority = HOOK_WORDS | CONFLICT_WORDS | {"porque", "porquê", "por que", "você", "voce"}
    keyword_index = next((index for index, token in enumerate(cleaned) if token in priority), max(range(len(labels)), key=lambda index: len(cleaned[index]), default=0))
    break_at: int | None = None
    if len(" ".join(labels)) > 32 and len(labels) > 1:
        target = len(" ".join(labels)) / 2
        running = 0
        for index, label in enumerate(labels[:-1]):
            running += len(label) + (1 if index else 0)
            if running >= target:
                break_at = index + 1
                break
    rendered: list[str] = []
    for index, label in enumerate(labels):
        if break_at == index:
            rendered.append(r"\N")
        token = ass_escape(label)
        rendered.append(f"{{\\c&H0000A5FF&}}{token}{{\\c&H00FFFFFF&}}" if index == keyword_index else token)
        if index < len(labels) - 1 and break_at != index + 1:
            rendered.append(" ")
    return "".join(rendered)


def write_ass(segments: list[Segment], candidate: Candidate, path: Path, margin_v: int) -> None:
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,DejaVu Sans,{CAPTION_FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,4,0,2,70,70,{margin_v},1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for chunk in caption_chunks(segments, candidate):
        start = max(0.0, float(chunk[0]["start"]) - candidate.start)
        end = max(start + 0.08, float(chunk[-1]["end"]) - candidate.start)
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{render_caption(chunk)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_clip(source: Path, captions: Path, candidate: Candidate, output: Path) -> None:
    caption_path = str(captions).replace(":", "\\:")
    filter_complex = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=22,eq=brightness=-0.18:saturation=0.80[bg];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{caption_path}':original_size=1080x1920,"
        "drawbox=x=iw-240:y=34:w=210:h=40:color=black@0.30:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='CORTE FINO':fontcolor=white@0.76:fontsize=22:x=w-tw-48:y=43[v]"
    )
    run([
        "ffmpeg", "-y", "-i", str(source), "-ss", f"{candidate.start:.3f}", "-t", f"{candidate.duration:.3f}",
        "-filter_complex", filter_complex, "-map", "[v]", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", "-avoid_negative_ts", "make_zero", str(output),
    ])


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


def enrich_clip(clip: dict[str, Any], source_url: str | None, info: dict[str, Any], rights: dict[str, Any]) -> dict[str, Any]:
    hook = short_hook(str(clip.get("text", "")))
    title = info.get("title") or "Fonte não identificada"
    channel = info.get("channel") or info.get("uploader") or "Canal não identificado"
    source_link = source_url or info.get("webpage_url") or ""
    hashtags = ["#CorteFino", "#Shorts", "#Cortes"]
    corpus = f"{os.environ.get('SOURCE_NICHE', '')} {title} {channel} {clip.get('text', '')}".lower()
    for signal, tag in (
        ("futebol", "#Futebol"), ("humor", "#Humor"), ("tecnologia", "#Tecnologia"),
        ("negócios", "#Negocios"), ("negocios", "#Negocios"), ("finanças", "#Financas"),
        ("financas", "#Financas"), ("relacionamento", "#Relacionamento"),
        ("história", "#Historias"), ("historia", "#Historias"), ("true crime", "#TrueCrime"),
        ("ia", "#InteligenciaArtificial"), ("podcast", "#Podcast"),
    ):
        if signal in corpus and tag not in hashtags:
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
        "comment_question": {
            "treta": "Quem está certo nessa discussão? Explique nos comentários.",
            "surpresa": "Você já tinha ouvido essa versão? O que achou?",
            "humor": "Qual foi a parte mais engraçada para você?",
            "emoção": "Essa história te lembrou alguém ou alguma situação?",
            "curiosidade": "Você concorda com essa explicação? Por quê?",
        }.get(clip.get("trigger"), "Você concorda com essa explicação? Por quê?"),
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
) -> None:
    rights = rights_info()
    enriched = [enrich_clip(clip, source_url, info, rights) for clip in clips]
    if error and error.startswith("Nenhum momento passou no filtro editorial"):
        status = "EDITORIAL_EMPTY"
    elif error and error.startswith("DIREITOS_PENDENTES"):
        status = "RIGHTS_PENDING"
    elif error:
        status = "TECHNICAL_FAILURE"
    elif enriched:
        status = "READY_FOR_REVIEW"
    else:
        status = "EDITORIAL_EMPTY"
    source_title = info.get("title")
    source_channel = info.get("channel") or info.get("uploader")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_title": source_title,
        "source_channel": source_channel,
        "rights_status": rights["status"],
        "source": {
            "url": source_url,
            "title": source_title,
            "channel": source_channel,
            "fingerprint_sha256": source_hash,
        },
        "rights": rights,
        "editorial": {
            "minimum_score": MIN_EDITORIAL_SCORE,
            "approved_count": len(enriched),
            "candidate_count": len(candidates),
            "rule": "Só entra o que vale o corte.",
        },
        "clips": enriched,
        "qa": qa,
        "error": error,
        "note": "A seleção usa heurísticas editoriais e não promete viralização. A publicação permanece manual.",
        "editing": {
            "format": "9:16 — 1080x1920",
            "audio": "áudio original preservado em AAC",
            "captions": "ASS dinâmico, 3–6 palavras por bloco, destaque discreto e terço inferior",
            "framing": "quadro completo com fundo desfocado para preservar rostos",
            "branding": "Corte Fino discreto, sem vinheta e sem música adicionada",
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
        "",
        f"**Nota mínima:** {MIN_EDITORIAL_SCORE:.0f}/100",
        f"**Cortes aprovados:** {len(enriched)}",
        f"**Direitos:** {rights['status']}",
        "**Publicação:** revisão manual obrigatória",
        "",
    ]
    for index, clip in enumerate(enriched, 1):
        lines.extend([
            f"## Corte {index}",
            f"- YouTube Shorts: {clip['youtube_file']}",
            f"- TikTok: {clip['tiktok_file']}",
            f"- Tempo original: {clip['start']:.2f}s–{clip['end']:.2f}s",
            f"- Duração: {clip['duration']:.2f}s",
            f"- Nota editorial: {clip['score']}/100",
            f"- Gatilho: {clip['trigger']}",
            f"- Motivo: {clip['editorial_reason']}",
            f"- Título YouTube: {clip['youtube_title']}",
            f"- Pergunta: {clip['comment_question']}",
            f"- Texto-base: {clip['text']}",
            "",
        ])
    if error:
        lines.extend(["## Problema", error, ""])
    (OUTPUT / "relatorio.md").write_text("\n".join(lines), encoding="utf-8")


def zip_outputs() -> None:
    zip_path = OUTPUT / "corte-fino-resultados.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in OUTPUT.rglob("*"):
            if path.is_file() and path != zip_path:
                archive.write(path, path.relative_to(OUTPUT))


def main() -> int:
    clean()
    source_url = os.environ.get("SOURCE_URL", "").strip() or (urls_from_sources() or [None])[0]
    info: dict[str, Any] = {}
    clips: list[dict[str, Any]] = []
    candidates: list[Candidate] = []
    qa: list[dict[str, Any]] = []
    source_hash: str | None = None
    error: str | None = None
    success = False
    try:
        source, info = obtain_source(source_url)
        source_hash = source_fingerprint(source)
        duration = media_duration(source)
        if duration <= 0:
            raise RuntimeError("Não foi possível determinar a duração da fonte.")
        if duration > MAX_SOURCE_DURATION_SECONDS:
            raise RuntimeError(f"Fonte longa demais: {duration / 60:.1f} minutos; limite configurado: {MAX_SOURCE_DURATION_SECONDS / 60:.0f} minutos.")
        rights = rights_info()
        if not rights["authorized_signal"] and os.environ.get("ALLOW_UNVERIFIED_SOURCE", "0") != "1":
            raise RuntimeError("DIREITOS_PENDENTES: a fonte precisa ter autorização/licença confirmada antes da geração automática.")
        segments = transcribe(source)
        selected, candidates = select_candidates(segments)
        if not selected:
            raise RuntimeError(f"Nenhum momento passou no filtro editorial mínimo de {MIN_EDITORIAL_SCORE:.0f}/100.")

        for index, candidate in enumerate(selected, 1):
            yt_captions = WORK / f"shorts_{index:02d}.ass"
            tt_captions = WORK / f"tiktok_{index:02d}.ass"
            yt_output = YOUTUBE_DIR / f"corte_fino_{index:02d}_youtube_shorts.mp4"
            tt_output = TIKTOK_DIR / f"corte_fino_{index:02d}_tiktok.mp4"
            write_ass(segments, candidate, yt_captions, YOUTUBE_CAPTION_MARGIN_V)
            render_clip(source, yt_captions, candidate, yt_output)
            write_ass(segments, candidate, tt_captions, TIKTOK_CAPTION_MARGIN_V)
            render_clip(source, tt_captions, candidate, tt_output)
            yt_qa = validate_video(yt_output, candidate.duration)
            tt_qa = validate_video(tt_output, candidate.duration)
            qa.extend([
                {"platform": "youtube_shorts", "clip": index, **yt_qa},
                {"platform": "tiktok", "clip": index, **tt_qa},
            ])
            if not yt_qa["passed"] or not tt_qa["passed"]:
                raise RuntimeError(f"QA reprovou o corte {index}: confira qa.json e relatorio.json.")
            clips.append({
                "file": str(yt_output.relative_to(OUTPUT)),
                "youtube_file": str(yt_output.relative_to(OUTPUT)),
                "tiktok_file": str(tt_output.relative_to(OUTPUT)),
                "start": candidate.start,
                "end": candidate.end,
                "duration": candidate.duration,
                "score": candidate.score,
                "components": candidate.components,
                "trigger": candidate.trigger,
                "editorial_reason": candidate.reason,
                "text": candidate.text,
            })
        success = True
    except Exception as exc:
        error = str(exc)
        print(f"ERRO: {error}", file=sys.stderr)
        if error.startswith("Nenhum momento passou no filtro editorial"):
            success = True
    finally:
        if OUTPUT.exists():
            write_reports(source_url, source_hash, info, clips, candidates, qa, error)
            zip_outputs()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
