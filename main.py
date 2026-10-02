from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_CLIPS = 4
ROOT = Path(__file__).resolve().parents[1]
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
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def discover_url() -> str | None:
    """Best-effort discovery without paid trend credits.

    This is intentionally conservative. The result is marked for manual rights review.
    """
    from yt_dlp import YoutubeDL

    queries = [
        "podcast brasileiro",
        "entrevista podcast Brasil",
        "podcast humor Brasil",
        "Podpah",
        "Ticaracaticast",
        "Flow Podcast",
    ]
    found: list[dict[str, Any]] = []
    opts = {"quiet": True, "skip_download": True, "extract_flat": True, "playlistend": 8}
    with YoutubeDL(opts) as ydl:
        for query in queries:
            try:
                data = ydl.extract_info(f"ytsearchdate8:{query}", download=False)
                for item in (data or {}).get("entries", []) or []:
                    if not item or not item.get("webpage_url") and not item.get("id"):
                        continue
                    item = dict(item)
                    item["query"] = query
                    found.append(item)
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
    chosen = ranked[0]
    Path(OUTPUT / "discovery.json").write_text(json.dumps({"selected": chosen, "candidates": ranked[:20]}, ensure_ascii=False, indent=2), encoding="utf-8")
    return chosen["webpage_url"]


def download_source(url: str) -> tuple[Path, dict[str, Any]]:
    from yt_dlp import YoutubeDL

    outtmpl = str(SOURCE_DIR / "source.%(ext)s")
    opts = {
        "format": "bv*[height<=720]+ba/b[height<=720]/b",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": False,
        "restrictfilenames": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        prepared = Path(ydl.prepare_filename(info))
        candidates = [prepared, prepared.with_suffix(".mp4")]
        source = next((p for p in candidates if p.exists()), None)
        if source is None:
            mp4s = list(SOURCE_DIR.glob("*.mp4"))
            source = mp4s[0] if mp4s else None
        if source is None:
            raise FileNotFoundError("O download terminou sem produzir um MP4.")
        return source, info


def transcribe(source: Path) -> list[Segment]:
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(source), language="pt", word_timestamps=True, vad_filter=True, beam_size=3
    )
    result: list[Segment] = []
    for segment in segments:
        words = []
        for word in (getattr(segment, "words", None) or []):
            words.append({"start": float(word.start), "end": float(word.end), "word": word.word})
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
    for i, start_seg in enumerate(segments):
        start = start_seg.start
        if start >= segments[-1].end:
            break
        end_idx = i
        while end_idx < len(segments) and segments[end_idx].end - start < 68:
            end_idx += 1
        if end_idx <= i:
            continue
        end = segments[end_idx - 1].end
        if end - start < 32 or end - start > 78:
            continue
        text = " ".join(item.text for item in segments[i:end_idx]).strip()
        score = score_text(text)
        if score > 0:
            candidates.append(Candidate(start, end, text, round(score, 2)))

    candidates.sort(key=lambda item: item.score, reverse=True)
    selected: list[Candidate] = []
    for candidate in candidates:
        overlap = False
        for other in selected:
            intersection = max(0.0, min(candidate.end, other.end) - max(candidate.start, other.start))
            shorter = min(candidate.end - candidate.start, other.end - other.start)
            if shorter and intersection / shorter > 0.35:
                overlap = True
                break
        if not overlap:
            selected.append(candidate)
        if len(selected) == MAX_CLIPS:
            break
    return sorted(selected, key=lambda item: item.start)


def srt_time(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, millis = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: list[Segment], candidate: Candidate, path: Path) -> None:
    lines: list[str] = []
    index = 1
    for segment in segments:
        if segment.end <= candidate.start or segment.start >= candidate.end:
            continue
        words = [word for word in segment.words if word["end"] > candidate.start and word["start"] < candidate.end]
        if not words:
            words = [{"start": segment.start, "end": segment.end, "word": segment.text}]
        for offset in range(0, len(words), 8):
            chunk = words[offset : offset + 8]
            start = max(candidate.start, float(chunk[0]["start"])) - candidate.start
            end = min(candidate.end, float(chunk[-1]["end"])) - candidate.start
            text = " ".join(item["word"].strip() for item in chunk).strip()
            if not text or end <= start:
                continue
            lines.extend([str(index), f"{srt_time(start)} --> {srt_time(end)}", text, ""])
            index += 1
    path.write_text("\n".join(lines), encoding="utf-8")


def render_clip(source: Path, srt: Path, candidate: Candidate, output: Path) -> None:
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "text='CORTE FINO':fontcolor=white@0.68:fontsize=28:x=w-tw-48:y=48,"
        f"subtitles={srt}:force_style='FontName=DejaVu Sans,FontSize=18,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
        "Outline=3,Shadow=0,Alignment=2,MarginV=160,MarginL=70,MarginR=70'"
    )
    run([
        "ffmpeg", "-y", "-ss", f"{candidate.start:.3f}", "-i", str(source),
        "-t", f"{candidate.end - candidate.start:.3f}", "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output),
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
    }
    (OUTPUT / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Corte Fino — relatório", "", f"Fonte: {info.get('title') or 'não identificada'}", f"URL: {source_url or 'não informada'}", "", "**Direitos:** REVISÃO DE DIREITOS — confirme autorização antes de publicar.", ""]
    for index, clip in enumerate(clips, 1):
        lines.extend([
            f"## Corte {index}",
            f"- Arquivo: `{clip['file']}`",
            f"- Tempo original: {clip['start']:.2f}s–{clip['end']:.2f}s",
            f"- Nota editorial: {clip['score']}",
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
    try:
        if not source_url:
            source_url = discover_url()
        if not source_url:
            raise RuntimeError("Nenhuma fonte encontrada. Informe um link autorizado no workflow ou em sources.txt.")
        source, info = download_source(source_url)
        segments = transcribe(source)
        candidates = select_candidates(segments)
        if not candidates:
            raise RuntimeError("A transcrição não encontrou quatro momentos com contexto e duração suficientes.")
        for index, candidate in enumerate(candidates, 1):
            srt = WORK / f"corte_{index:02d}.srt"
            output = CLIPS_DIR / f"corte_fino_{index:02d}.mp4"
            write_srt(segments, candidate, srt)
            render_clip(source, srt, candidate, output)
            clips.append({
                "file": str(output.relative_to(OUTPUT)),
                "start": candidate.start,
                "end": candidate.end,
                "score": candidate.score,
                "text": candidate.text,
            })
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
