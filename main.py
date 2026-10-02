from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_CLIPS = int(os.environ.get("MAX_CLIPS", "4"))
MIN_CLIP_SECONDS = 35
MAX_CLIP_SECONDS = 75
CAPTION_MIN_WORDS = 3
CAPTION_MAX_WORDS = 6
ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"
SOURCE_DIR = WORK / "source"
CLIPS_DIR = OUTPUT / "clips"

EMOTION_WORDS = {
    "absurdo", "absurda", "surpresa", "surpreendente", "medo", "raiva",
    "vergonha", "inacreditável", "inacreditavel", "nunca", "sempre",
    "ninguém", "ninguem", "revelou", "revelação", "revelacao", "perdi",
    "ganhei", "treta", "mentira", "verdade", "problema", "polêmica",
    "polemica", "errado", "errada", "cuidado", "segredo", "chocante",
}
CONTRAST_WORDS = {"mas", "porém", "porem", "só que", "so que", "entretanto", "enquanto"}
QUESTION_WORDS = {"por que", "porque", "como", "quando", "quem", "qual", "será", "sera"}


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


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(str(x) for x in cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def clean() -> None:
    if WORK.exists():
        shutil.rmtree(WORK)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def urls_from_sources() -> list[str]:
    path = ROOT / "sources.txt"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]


def discover_url() -> str | None:
    from yt_dlp import YoutubeDL

    queries = ["podcast brasileiro", "entrevista podcast Brasil", "podcast humor Brasil", "Podpah", "Ticaracaticast", "Flow Podcast"]
    found: list[dict[str, Any]] = []
    opts = {"quiet": True, "skip_download": True, "extract_flat": True, "playlistend": 8}
    with YoutubeDL(opts) as ydl:
        for query in queries:
            try:
                data = ydl.extract_info(f"ytsearchdate8:{query}", download=False)
                for item in (data or {}).get("entries", []) or []:
                    if item and (item.get("webpage_url") or item.get("id")):
                        found.append({**dict(item), "query": query})
            except Exception as exc:
                print(f"Busca falhou para {query}: {exc}")

    unique: dict[str, dict[str, Any]] = {}
    for item in found:
        url = item.get("webpage_url") or f"https://www.youtube.com/watch?v={item.get('id')}"
        unique[url] = {**item, "webpage_url": url}

    def score(item: dict[str, Any]) -> float:
        views = float(item.get("view_count") or 0)
        duration = float(item.get("duration") or 0)
        title = (item.get("title") or "").lower()
        topic_bonus = sum(1 for word in ("podcast", "entrevista", "história", "humor", "revelou") if word in title)
        usable_duration = 1 if 900 <= duration <= 14400 else 0
        return (views ** 0.5) + topic_bonus * 10000 + usable_duration * 5000

    ranked = sorted(unique.values(), key=score, reverse=True)
    if not ranked:
        return None
    (OUTPUT / "discovery.json").write_text(json.dumps({"selected": ranked[0], "candidates": ranked[:20]}, ensure_ascii=False, indent=2), encoding="utf-8")
    return ranked[0]["webpage_url"]


def download_source(url: str) -> tuple[Path, dict[str, Any]]:
    from yt_dlp import YoutubeDL

    opts = {
        "format": "bv*[height<=720]+ba/b[height<=720]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(SOURCE_DIR / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "restrictfilenames": True,
    }
    cookiefile = os.environ.get("YOUTUBE_COOKIEFILE", "").strip()
    if cookiefile and Path(cookiefile).is_file():
        opts["cookiefile"] = cookiefile
        opts["extractor_args"] = {"youtube": {"player_client": ["web"]}}

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        prepared = Path(ydl.prepare_filename(info))
        source = next((item for item in (prepared, prepared.with_suffix(".mp4")) if item.exists()), None)
        if source is None:
            source = next(iter(SOURCE_DIR.glob("*.mp4")), None)
        if source is None:
            raise FileNotFoundError("O download terminou sem produzir um MP4.")
        return source, info


def transcribe(source: Path) -> list[Segment]:
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(source), language="pt", word_timestamps=True, vad_filter=True, beam_size=3)
    result: list[Segment] = []
    for segment in segments:
        words = [{"start": float(word.start), "end": float(word.end), "word": word.word} for word in (getattr(segment, "words", None) or [])]
        result.append(Segment(float(segment.start), float(segment.end), segment.text.strip(), words))
    if not result:
        raise RuntimeError("A transcrição não retornou fala suficiente.")
    return result


def score_text(text: str) -> float:
    lower = text.lower()
    words = re.findall(r"[\wÀ-ÿ]+", lower)
    if len(words) < 35:
        return -50
    score = min(len(words) / 15, 8)
    score += sum(3 for item in EMOTION_WORDS if item in lower)
    score += sum(2 for item in CONTRAST_WORDS if item in lower)
    score += sum(1.5 for item in QUESTION_WORDS if item in lower)
    score += min(sum(1 for word in words if any(char.isdigit() for char in word)), 4)
    if "?" in text:
        score += 2
    if len(words) > 260:
        score -= 3
    return score


def select_candidates(segments: list[Segment]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, start_segment in enumerate(segments):
        start = start_segment.start
        end_index = index
        while end_index < len(segments) and segments[end_index].end - start < 68:
            end_index += 1
        if end_index <= index:
            continue
        end = segments[end_index - 1].end
        if end - start < MIN_CLIP_SECONDS or end - start > MAX_CLIP_SECONDS + 3:
            continue
        text = " ".join(item.text for item in segments[index:end_index]).strip()
        score = score_text(text)
        if score > 0:
            candidates.append(Candidate(start, end, text, round(score, 2)))

    candidates.sort(key=lambda item: item.score, reverse=True)
    selected: list[Candidate] = []
    for candidate in candidates:
        if any(
            min(candidate.end, other.end) - max(candidate.start, other.start)
            > 0.35 * min(candidate.end - candidate.start, other.end - other.start)
            for other in selected
        ):
            continue
        selected.append(candidate)
        if len(selected) == MAX_CLIPS:
            break
    return sorted(selected, key=lambda item: item.start)


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
            source_words = [{"start": segment.start + duration * index / max(len(tokens), 1), "end": segment.start + duration * (index + 1) / max(len(tokens), 1), "word": token} for index, token in enumerate(tokens)]
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
    priority = set(EMOTION_WORDS) | {"mas", "porém", "porem", "entretanto", "nunca", "sempre", "porquê", "porque"}
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


def write_ass(segments: list[Segment], candidate: Candidate, path: Path) -> None:
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,DejaVu Sans,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,4,0,2,70,70,245,1", "",
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
        "ffmpeg", "-y", "-i", str(source), "-ss", f"{candidate.start:.3f}", "-t", f"{candidate.end - candidate.start:.3f}",
        "-filter_complex", filter_complex, "-map", "[v]", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", "-avoid_negative_ts", "make_zero", str(output),
    ])


def write_report(source_url: str | None, info: dict[str, Any], clips: list[dict[str, Any]], error: str | None = None) -> None:
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "source_title": info.get("title"),
        "source_channel": info.get("channel") or info.get("uploader"),
        "rights_status": "REVISÃO DE DIREITOS — confirme autorização antes de publicar",
        "clips": clips,
        "error": error,
        "note": "Nenhuma promessa de viralização. A seleção é editorial e heurística.",
        "editing": {
            "format": "9:16 — 1080x1920",
            "audio": "áudio original preservado em AAC",
            "captions": "ASS dinâmico, 3–6 palavras por bloco, destaque laranja",
            "framing": "quadro completo com fundo desfocado para preservar rostos",
            "branding": "Corte Fino discreto, sem vinheta e sem música adicionada",
        },
    }
    (OUTPUT / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Corte Fino — relatório", "", f"Fonte: {info.get('title') or 'não identificada'}", f"URL: {source_url or 'não informada'}", "", "**Direitos:** REVISÃO DE DIREITOS — confirme autorização antes de publicar.", ""]
    for index, clip in enumerate(clips, 1):
        lines.extend([f"## Corte {index}", f"- Arquivo: {clip['file']}", f"- Tempo original: {clip['start']:.2f}s–{clip['end']:.2f}s", f"- Nota editorial: {clip['score']}", f"- Texto-base: {clip['text']}", ""])
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
    try:
        if not source_url:
            source_url = discover_url()
        if not source_url:
            raise RuntimeError("Nenhuma fonte encontrada. Informe um link autorizado no workflow ou em sources.txt.")
        source, info = download_source(source_url)
        segments = transcribe(source)
        candidates = select_candidates(segments)
        if not candidates:
            raise RuntimeError("A transcrição não encontrou momentos com contexto e duração suficientes.")
        for index, candidate in enumerate(candidates, 1):
            captions = WORK / f"corte_{index:02d}.ass"
            output = CLIPS_DIR / f"corte_fino_{index:02d}.mp4"
            write_ass(segments, candidate, captions)
            render_clip(source, captions, candidate, output)
            clips.append({"file": str(output.relative_to(OUTPUT)), "start": candidate.start, "end": candidate.end, "score": candidate.score, "text": candidate.text})
        write_report(source_url, info, clips)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        write_report(source_url, info, clips, str(exc))
    finally:
        if OUTPUT.exists():
            zip_outputs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
