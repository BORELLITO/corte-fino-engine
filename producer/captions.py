"""Caption stage: ASS cues timed from measured audio, verified before being called synchronized."""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .common import ProducerError

MAX_LINE_CHARS = 28
MAX_LINES = 2
SCENE_TOLERANCE = 0.25


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    lines: tuple[str, ...]


class Aligner(Protocol):
    def align(self, wav: Path, words: list[str]) -> list[tuple[float, float]]: ...


def _norm(word: str) -> str:
    base = unicodedata.normalize("NFKD", word.casefold())
    return re.sub(r"[^\w]", "", "".join(c for c in base if not unicodedata.combining(c)))


# Function words that must never close a line or a cue (they belong to the NEXT word).
_WEAK_RAW = ("""
a o as os um uma uns umas de do da dos das em no na nos nas num numa ao aos à às pelo pela pelos pelas
por para pra com sem sob sobre entre até e ou mas que se como quando onde nem
meu minha meus minhas teu tua teus tuas seu sua seus suas nosso nossa nossos nossas
me te lhe nos lhes já não mais mesmo
""")
WEAK_WORDS = frozenset(_norm(w) for w in _WEAK_RAW.split())
SOFT_TARGET_CHARS = 42  # reading comfort for a 9:16 short; above this a cue gets a penalty


def _weak(word: str) -> bool:
    return _norm(word) in WEAK_WORDS and not re.search(r"[.!?,;:…]$", word)


def _split_two_lines(words: list[str]) -> tuple[str, str] | None:
    """Best 2-line split: both lines fit, balanced, no line ends on a function word, no 1-word tail."""
    best, best_cost = None, None
    for i in range(1, len(words)):
        l1, l2 = " ".join(words[:i]), " ".join(words[i:])
        if len(l1) > MAX_LINE_CHARS or len(l2) > MAX_LINE_CHARS:
            continue
        cost = abs(len(l1) - len(l2)) + (100 if _weak(words[i - 1]) else 0) + (30 if len(words) - i == 1 else 0)
        if best_cost is None or cost < best_cost:
            best, best_cost = (l1, l2), cost
    return best


def wrap(words: list[str]) -> tuple[str, ...]:
    one = " ".join(words)
    if len(one) <= MAX_LINE_CHARS or len(words) < 2:
        return (one,)
    two = _split_two_lines(words)
    if two:
        return two
    lines, current = [], ""  # overlong content: greedy (the caller sees >MAX_LINES and rejects it)
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= MAX_LINE_CHARS or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return tuple(lines)


def _chunk_cost(words: list[str], last_of_text: bool) -> float:
    text = " ".join(words)
    cost = 10.0
    if not last_of_text and _weak(words[-1]):
        cost += 80
    if len(words) == 1 and not last_of_text:
        cost += 60
    lines = wrap(words)
    cost += 40 * sum(_weak(line.split()[-1]) for line in lines[:-1])  # a line closing on a function word
    if len(lines) == 2 and len(lines[1].split()) == 1 and len(words) > 2:
        cost += 20  # one-word tail line
    if len(text) > SOFT_TARGET_CHARS:
        cost += (len(text) - SOFT_TARGET_CHARS) * 1.5
    if re.search(r"[.!?…]$", words[-1]):
        cost -= 25
    elif re.search(r"[,;:]$", words[-1]):
        cost -= 12
    return cost


def chunk_words(words: list[str]) -> list[list[int]]:
    """Group word indexes into cues (each fits 2 lines) by dynamic programming:
    prefer breaks at punctuation, never end a cue on a function word, avoid 1-word cues."""
    n = len(words)
    if n == 0:
        return []
    INF = float("inf")
    best, prev = [INF] * (n + 1), [0] * (n + 1)
    best[0] = 0.0
    for i in range(1, n + 1):
        for j in range(i - 1, -1, -1):
            chunk = words[j:i]
            if len(wrap(chunk)) > MAX_LINES:
                break  # longer chunks (smaller j) can only be wider
            cost = best[j] + _chunk_cost(chunk, i == n)
            if cost < best[i]:
                best[i], prev[i] = cost, j
    out, i = [], n
    while i > 0:
        out.append(list(range(prev[i], i)))
        i = prev[i]
    return out[::-1]


def proportional_times(words: list[str], t0: float, t1: float) -> list[tuple[float, float]]:
    weights = [max(1, len(w)) for w in words]
    total, cursor, out = sum(weights), t0, []
    for w in weights:
        span = (t1 - t0) * w / total
        out.append((cursor, cursor + span))
        cursor += span
    return out


def build_cues(scenes: list[tuple[str, float, float]], aligner_times: list[tuple[float, float]] | None) -> list[Cue]:
    """scenes: (narration, start, end). aligner_times covers every script word in order, if given."""
    cues, offset = [], 0
    for text, t0, t1 in scenes:
        words = text.split()
        times = (aligner_times[offset:offset + len(words)] if aligner_times
                 else proportional_times(words, t0, t1))
        offset += len(words)
        for chunk in chunk_words(words):
            start, end = times[chunk[0]][0], times[chunk[-1]][1]
            cues.append(Cue(start, end, wrap([words[i] for i in chunk])))
    return cues


def verify_cues(cues: list[Cue], scenes: list[tuple[str, float, float]]) -> list[str]:
    errors, prev_end = [], 0.0
    for i, cue in enumerate(cues):
        if cue.end <= cue.start:
            errors.append(f"cue:{i}:interval")
        if cue.start < prev_end - 1e-6:
            errors.append(f"cue:{i}:overlap")
        if len(cue.lines) > MAX_LINES or any(len(x) > MAX_LINE_CHARS and " " in x for x in cue.lines):
            errors.append(f"cue:{i}:safe_area")
        prev_end = max(prev_end, cue.end)
    lo, hi = scenes[0][1] - SCENE_TOLERANCE, scenes[-1][2] + SCENE_TOLERANCE
    if cues and (cues[0].start < lo or cues[-1].end > hi):
        errors.append("cue:outside_audio_window")
    return errors


def _ts(seconds: float) -> str:
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(cues: list[Cue], path: Path) -> None:
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,"
        "Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV\n"
        "Style: Default,DejaVu Sans,42,&H00FFFFFF,&H00000000,&H64000000,1,1,2,1,2,80,80,220\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Text\n"
    )
    newline = "\\N"  # ASS hard line break
    body = "".join(f"Dialogue: 0,{_ts(c.start)},{_ts(c.end)},Default,{newline.join(c.lines)}\n"
                   for c in cues)
    path.write_text(head + body, encoding="utf-8")


class FasterWhisperAligner:
    """Aligns SCRIPT words to the real audio using ASR word timestamps (faster-whisper)."""

    def __init__(self, model: str = "small") -> None:
        self.model_name = model

    def align(self, wav: Path, words: list[str]) -> list[tuple[float, float]]:
        try:
            from faster_whisper import WhisperModel  # type: ignore
            segments, _ = WhisperModel(self.model_name, device="cpu", compute_type="int8").transcribe(
                str(wav), language="pt", word_timestamps=True)
            heard = [(w.word, w.start, w.end) for s in segments for w in (s.words or [])]
        except Exception as exc:
            raise ProducerError(f"producer:captions:asr_failed:{type(exc).__name__}:{str(exc)[:200]}") from exc
        if not heard:
            raise ProducerError("producer:captions:asr_empty")
        a, b = [_norm(w) for w in words], [_norm(h[0]) for h in heard]
        times: list[tuple[float, float] | None] = [None] * len(words)
        for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = (heard[blk.b + k][1], heard[blk.b + k][2])
        if sum(t is not None for t in times) < 0.8 * len(words):
            raise ProducerError("producer:captions:asr_match_below_80pct")
        # interpolate unmatched words between matched neighbours
        last_end = 0.0
        for i, t in enumerate(times):
            if t is None:
                nxt = next((times[j][0] for j in range(i + 1, len(times)) if times[j]), heard[-1][2])
                times[i] = (last_end, max(last_end + 0.05, min(nxt, last_end + 0.4)))
            last_end = times[i][1]
        return times  # type: ignore[return-value]
