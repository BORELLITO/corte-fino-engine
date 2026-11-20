"""Produce REAL timecoded E01 v2 caption files from immutable dual ASR bytes.

This does not reinterpret ASR as ground truth: canonical narration always owns
the displayed text. Match timestamps against the two independent Whisper
outputs, report every inferred/uncertain word, enforce two-line mobile-safe
cues, and remain fail-closed for master/release/publishing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

try:
    from PIL import ImageFont
except ImportError:  # Primary engine gates do not install imaging packages.
    ImageFont = None

from agents.content_production import ProductionError, check
from agents.autonomous_editorial_gate import canonical_sha

ASR_SHA = "377063ff846ddef641b9288656ea867ede965a73991abe6b4c203dec3a919a8b"
ASR_BYTES = 72475
SCRIPT_SHA = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
WAV_SHA = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
VOICE_DURATION = 70.425
# v3c layout (PlayRes 1080x1920). Widths are measured in real pixels with the
# exact font that libass renders; character counts are not a valid proxy.
FONT_PATH = Path(__file__).resolve().parents[1] / "assets/fonts/AtkinsonHyperlegibleNext-Bold.ttf"
FONT_SHA = "aa4ee81e4b45aeaf70f5c33f0f1290640b5fe36a34664165f2bae1e35b003546"
FONT_FAMILY = "Atkinson Hyperlegible Next"
FONT_ASS_SIZE = 107          # ASS Fontsize; em = 76 px for this font
FONT_EM_PX = 76
MAX_LINE_PX = 700            # text width; rendered bbox is ~15 px wider
MARGIN_SIDE = 180            # keeps x in 180..900 (right HUD rail clear)
MARGIN_BOTTOM = 576          # bottom HUD clearance, measured on 3 screenshots
COLOR_SUNG = "&H00F2B0C4"    # light lilac (provisional brand colour)
COLOR_UNSUNG = "&H00EEF1F2"  # warm white
MAX_LINES = 2
MAX_CUE_WORDS = 7
ONE_LINE_MAX_WORDS = 3
MAX_CUE_DURATION = 3.4
MIN_CUE_DURATION = 0.28

# The silent H of Habacuque and one numeric spelling variation are explicit
# time-alignment aliases; they do NOT prove that TTS pronounced them correctly.
ALIGNMENT_ALIASES = {
    "habacuque": {"abacuque", "abacook"},
    "um": {"1"},
}


def digest_file(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def norm(raw: str) -> str:
    value = "".join(
        c for c in unicodedata.normalize("NFKD", raw.casefold())
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]", "", value)


def canonical_words(draft: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for block in draft["blocks"]:
        for token in block["text"].split():
            n = norm(token)
            check(bool(n), "caption:empty_word")
            out.append({"text": token, "key": n, "block": block["type"]})
    return out


def asr_words(result: dict[str, Any]) -> list[dict[str, Any]]:
    flat = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            start, end = float(w["start"]), float(w["end"])
            key = norm(w["word"])
            check(key and math.isfinite(start) and math.isfinite(end)
                  and -0.01 <= start <= end <= VOICE_DURATION + 0.5,
                  "caption:invalid_asr_word")
            flat.append({
                "text": w["word"].strip(),
                "key": key, "start": max(0.0, start),
                "end": min(VOICE_DURATION, end),
                "confidence": float(w["probability"]),
            })
    check(130 <= len(flat) <= 240, "caption:asr_words_out_of_bound")
    return flat


def similarity(ref: str, observed: str) -> float:
    if ref == observed:
        return 0.0
    if observed in ALIGNMENT_ALIASES.get(ref, set()):
        return 0.28
    return 1.55


def align_once(canonical: list[dict[str, Any]],
               observed: list[dict[str, Any]]) -> list[dict[str, Any] | None]:
    """Full global edit alignment, not same-index or estimated word speeds."""
    n, m = len(canonical), len(observed)
    check(n <= 300 and m <= 300, "caption:alignment_too_large")
    dp = [[0.0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1): dp[i][0] = i * 1.0
    for j in range(1, m+1): dp[0][j] = j * 1.0
    for i in range(1, n+1):
        for j in range(1, m+1):
            dp[i][j] = min(
                dp[i-1][j-1] + similarity(canonical[i-1]["key"], observed[j-1]["key"]),
                dp[i-1][j] + 1.0,
                dp[i][j-1] + 1.0,
            )
    result: list[dict[str, Any] | None] = [None]*n
    i,j = n,m
    while i or j:
        if i and j and abs(dp[i][j] -
            (dp[i-1][j-1]+similarity(canonical[i-1]["key"],observed[j-1]["key"]))) < 0.001:
            cost = similarity(canonical[i-1]["key"], observed[j-1]["key"])
            if cost < 1.0:
                d = dict(observed[j-1])
                d["alignment"] = "EXACT" if cost == 0 else "PHONETIC_OR_NUMBER_ALIAS"
                result[i-1] = d
            i -= 1; j -= 1
        elif i and abs(dp[i][j] - (dp[i-1][j] + 1.0)) < 0.001:
            i -= 1
        else:
            check(j > 0, "caption:alignment_traceback_failed")
            j -= 1
    return result


def combine_alignments(script: list[dict[str, Any]],
                       small: list[dict[str, Any]],
                       base: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    left = align_once(script, small)
    right = align_once(script, base)
    check(len(left) == len(right) == len(script), "caption:alignment_length")
    words = []
    fallback = 0; interpolated = 0; alias_count = 0
    for i, token in enumerate(script):
        a, b = left[i], right[i]
        if a and a["alignment"] == "EXACT":
            choice, method = a, "SMALL_EXACT"
        elif b and b["alignment"] == "EXACT":
            choice, method = b, "BASE_EXACT_FALLBACK"; fallback += 1
        elif a:
            choice, method = a, "SMALL_PHONETIC_ALIAS"; alias_count += 1
        elif b:
            choice, method = b, "BASE_PHONETIC_ALIAS"; alias_count += 1
        else:
            choice, method = None, "UNVERIFIED_INTERPOLATION"; interpolated += 1
        words.append({
            **token,
            "index": i,
            "start": round(choice["start"], 3) if choice else None,
            "end": round(choice["end"], 3) if choice else None,
            "alignment": method,
            "asr_confidence": choice["confidence"] if choice else None,
        })
    # A sole missing token may be assigned an approximate time, but must always
    # remain explicitly marked, never counted as a verified spoken word.
    for i,w in enumerate(words):
        if w["start"] is not None: continue
        before = next((words[x] for x in range(i-1,-1,-1)
                       if words[x]["end"] is not None),None)
        after = next((words[x] for x in range(i+1,len(words))
                      if words[x]["start"] is not None),None)
        check(before is not None and after is not None,
              "caption:missing_opening_or_closing_word_timestamps")
        start, end = before["end"], after["start"]
        check(end >= start and end - start <= 0.75,
              "caption:missing_word_gap_too_large")
        mid = (start+end)*0.5
        w["start"] = round(mid,3)
        w["end"] = round(mid+0.04,3)
    # Ignore sub-100ms model time jitter, but do not allow a skipped sentence,
    # a 2+ second ASR silence or time reversal to masquerade as sync.
    prev_start = -0.01
    for w in words:
        check(-0.01 <= w["start"] <= w["end"] <= VOICE_DURATION + 0.05,
              "caption:invalid_combined_time")
        check(w["start"]+0.15 >= prev_start, "caption:nonmonotonic_words")
        prev_start = w["start"]
    summary = {
        "total_canonical_words": len(words),
        "timestamp_from_small_exact": sum(w["alignment"] == "SMALL_EXACT" for w in words),
        "timestamp_from_base_fallback": fallback,
        "phonetic_or_numeric_aliases": alias_count,
        "unverified_interpolated_words": interpolated,
        "every_canonical_word_present_in_output": True,
        "confidence_is_asr_estimate_not_acoustic_truth": True,
    }
    check(summary["total_canonical_words"] == 182
          and interpolated <= 3 and alias_count <= 3,
          "caption:too_many_unverified_words")
    return words, summary


_FONT: Any = None
FUNCTION_WORDS = {
    "a","o","as","os","e","de","do","da","dos","das","em","no","na","nos",
    "nas","um","uma","que","com","para","por","ou","mas","se","ao","à",
    "não","nem","sua","seu","suas","seus","você","é",
}


def text_width(text: str) -> float:
    global _FONT
    if _FONT is None:
        check(ImageFont is not None, "caption:pillow_required_for_pixel_layout")
        check(FONT_PATH.is_file() and digest_file(FONT_PATH) == FONT_SHA,
              "caption:caption_font_missing_or_changed")
        _FONT = ImageFont.truetype(str(FONT_PATH), FONT_EM_PX)
    return _FONT.getlength(text)


def _split(raw: list[str]) -> tuple[float, list[str]] | None:
    """Best 1- or 2-line layout under MAX_LINE_PX, or None. Lower is better."""
    one = " ".join(raw)
    if len(raw) <= ONE_LINE_MAX_WORDS and text_width(one) <= MAX_LINE_PX:
        return 0.0, [one]
    best = None
    for i in range(1, len(raw)):
        left, right = " ".join(raw[:i]), " ".join(raw[i:])
        wl, wr = text_width(left), text_width(right)
        if max(wl, wr) > MAX_LINE_PX:
            continue
        pen = (abs(wl - wr)
               + (40 if raw[i-1].lower().strip(",.?!:;") in FUNCTION_WORDS else 0)
               + (0 if wl <= wr else 25))
        if best is None or pen < best[0]:
            best = (pen, [left, right])
    return best


def cue_lines(words: list[dict[str, Any]]) -> list[str]:
    layout = _split([w["text"] for w in words])
    check(layout is not None, "caption:more_than_two_lines")
    return layout[1]


def _segment_cost(group: list[dict[str, Any]]) -> float:
    cost = (len(group) - 5) ** 2 + 3.0
    last = group[-1]["text"]
    if last[-1] in ".?!":
        cost -= 14
    elif last[-1] in ",:;":
        cost -= 9
    elif last.lower().strip(",.") in FUNCTION_WORDS:
        cost += 22
    if any(w["text"][-1] in ".?!" for w in group[:-1]):
        cost += 30
    if any(w["text"][-1] in ",:;" for w in group[:-1]):
        cost += 6
    if len(group) >= 2 and len(cue_lines(group)) == 1:
        cost += 1.5
    return cost


def make_cues(words: list[dict[str, Any]],
              duration: float = VOICE_DURATION) -> list[dict[str, Any]]:
    n = len(words)
    for w in words:
        check(w["start"] is not None and w["end"] is not None,
              "caption:unresolved_time")
    INF = float("inf")
    dp = [INF] * (n + 1); back = [0] * (n + 1); dp[0] = 0.0
    for j in range(1, n + 1):
        for i in range(max(0, j - MAX_CUE_WORDS), j):
            if dp[i] == INF:
                continue
            group = words[i:j]
            if len({w["block"] for w in group}) > 1:
                continue
            if group[-1]["end"] - group[0]["start"] > MAX_CUE_DURATION:
                continue
            if _split([w["text"] for w in group]) is None:
                continue
            c = dp[i] + _segment_cost(group)
            if c < dp[j]:
                dp[j] = c; back[j] = i
    check(dp[n] < INF, "caption:cannot_fit_single_word")
    bounds = []; j = n
    while j > 0:
        bounds.append((back[j], j)); j = back[j]
    cues = []
    for i, j in reversed(bounds):
        group = words[i:j]
        start = max(0.0, group[0]["start"])
        end = min(duration, group[-1]["end"])
        check(end - start >= MIN_CUE_DURATION, "caption:cue_too_short")
        cues.append({
            "index": len(cues) + 1, "start": round(start, 3),
            "end": round(end, 3), "lines": cue_lines(group),
            "words": group, "block": group[0]["block"],
        })
    # SRT track can show a tiny gap between phrases; no early words or overlaps.
    for k, cue in enumerate(cues):
        if k:
            prev = cues[k-1]
            if cue["start"] < prev["end"]:
                overlap = prev["end"] - cue["start"]
                check(overlap <= 0.18,
                      "caption:overlap_not_just_small_asr_jitter")
                prev["end"] = round(cue["start"], 3)
        check(cue["end"] > cue["start"] and len(cue["lines"]) <= MAX_LINES
              and all(text_width(line) <= MAX_LINE_PX for line in cue["lines"]),
              "caption:invalid_bounded_cue")
    check(cues[0]["start"] <= .5
          and cues[-1]["end"] >= duration - 1.3
          and len(cues) >= 20, "caption:coverage_too_short")
    return cues


def clock(seconds: float, sep: str = ",") -> str:
    ms=round(seconds*1000)
    return f"{ms//3600000:02}:{(ms//60000)%60:02}:{(ms//1000)%60:02}{sep}{ms%1000:03}"


def export_srt(cues: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"{c['index']}\n{clock(c['start'])} --> {clock(c['end'])}\n"
        + "\n".join(c["lines"]) for c in cues
    ) + "\n"


def export_vtt(cues: list[dict[str, Any]]) -> str:
    return "WEBVTT\n\n" + "\n\n".join(
        f"{clock(c['start'],'.')} --> {clock(c['end'],'.')}\n"
        + "\n".join(c["lines"]) for c in cues
    ) + "\n"


def ass_time(s: float) -> str:
    cs=round(s*100)
    return f"{cs//360000:01}:{(cs//6000)%60:02}:{(cs//100)%60:02}.{cs%100:02}"


def export_ass(cues: list[dict[str, Any]],
               duration: float = VOICE_DURATION) -> str:
    header = f"""[Script Info]
Title: VERBO NO CHAO | E01 V2 | QA-ONLY KARAOKE (layout v3c)
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{FONT_FAMILY},{FONT_ASS_SIZE},{COLOR_SUNG},{COLOR_UNSUNG},&H00141210,&H96000000,-1,0,0,0,100,100,0.6,0,1,7,3,2,{MARGIN_SIDE},{MARGIN_SIDE},{MARGIN_BOTTOM},1
Style: QA,DejaVu Sans,34,&H00E6E6E6,&H00E6E6E6,&H0012100E,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,90,90,118,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    out=[
        "Dialogue: 1,0:00:00.00,"+ass_time(duration)
        +",QA,,0,0,0,,PRÉVIA TÉCNICA - NÃO PUBLICAR"
    ]
    for c in cues:
        # Karaoke tags are cumulative; every boundary is derived from the
        # ABSOLUTE rounded word time so centisecond rounding never drifts.
        # \kf fills the word smoothly across exactly its ASR start..end.
        base=round(c["start"]*100)
        parts=[];cursor=0
        line_boundary = len(c["lines"][0].split())
        for idx,w in enumerate(c["words"]):
            if idx:
                parts.append(r"\N" if len(c["lines"]) == 2 and idx == line_boundary else " ")
            ws=max(cursor,round(w["start"]*100)-base)
            we=max(ws+1,round(w["end"]*100)-base)
            if ws>cursor:
                parts.append(r"{\k"+str(ws-cursor)+"}")
            parts.append(r"{\kf"+str(we-ws)+"}"+w["text"].replace("{","").replace("}",""))
            cursor=we
        body="".join(parts)
        out.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Caption,,0,0,0,,{body}")
    return header+"\n".join(out)+"\n"


def evaluate(root: Path, report_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    check(report_path.is_file() and report_path.stat().st_size == ASR_BYTES
          and digest_file(report_path) == ASR_SHA,
          "caption:untrusted_asr_report_sha_or_size")
    script_path=root/"contracts/e01_script_v2_candidate.json"
    check(script_path.is_file(),"caption:script_missing")
    draft=json.loads(script_path.read_text(encoding="utf-8"))["episode"]
    check(canonical_sha(draft)==SCRIPT_SHA
          and draft["episode_id"]=="VNC-W01-E1"
          and draft["script_id"]=="vnc-vnc-w01-e1-script-v2",
          "caption:unreviewed_script_content")
    report=json.loads(report_path.read_text(encoding="utf-8"))
    check(report.get("status")=="BLOCKED_V2_TEXT_OR_CRITICAL_WORD_DISCREPANCY"
          and report.get("source_script_sha256")==SCRIPT_SHA
          and report.get("source_wav_sha256")==WAV_SHA
          and report.get("duration_seconds")==VOICE_DURATION
          and report.get("final_audio_master_approved") is False
          and report.get("publication_authorized") is False,
          "caption:asr_receipt_does_not_match_original")
    model_results=report.get("model_results")
    check(isinstance(model_results,list) and len(model_results)==2
          and model_results[0]["model"]["repository"]=="Systran/faster-whisper-small"
          and model_results[1]["model"]["repository"]=="Systran/faster-whisper-base"
          and model_results[0]["fidelity_estimates"]["thresholds_passed"]
          and model_results[1]["fidelity_estimates"]["thresholds_passed"],
          "caption:asr_inference_invalid")
    canonical=canonical_words(draft)
    words, alignment=combine_alignments(
        canonical,asr_words(model_results[0]),asr_words(model_results[1]))
    cues=make_cues(words)
    stats={
        "project":"verbo-no-chao","episode_id":"VNC-W01-E1",
        "candidate_version":2,"status":"TIMED_CAPTIONS_PROVISIONAL_NOT_MASTER",
        "source_script_sha256":SCRIPT_SHA,
        "source_wav_sha256":WAV_SHA,"source_asr_report_sha256":ASR_SHA,
        "duration_seconds":VOICE_DURATION,"language":"pt-BR",
        "cue_count":len(cues),"max_lines":MAX_LINES,
        "max_line_width_px":MAX_LINE_PX,
        "caption_layout":"v3c_atkinson_lilac_margins180_bottom576",
        "min_caption_start":cues[0]["start"],
        "last_caption_end":cues[-1]["end"],
        "alignment":alignment,
        "rendered_video_master_exists":False,
        "karaoke_timestamps_verified_frame_by_frame":False,
        "caption_text_is_canonical_script":True,
        "speech_intelligibility_guaranteed":False,
        "voice_rights_cleared":False,
        "final_video_caption_sync_approved":False,
        "publication_authorized":False,
        "warnings":[
            "Whisper-base split 'machuca' into 'uma chuca'; primary small model recognized correct script, still requires physical playback QC.",
            "ASR pauses and timing are estimates; visual layout, line overflow and narration synchronization require actual rendered preview inspection.",
            "Outputs contain no third-party media or release rights; final visual/voice/music rights and publisher permission are pending.",
        ],
    }
    return cues,stats


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--asr-report",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    try:
        cues,report=evaluate(args.root.resolve(),args.asr_report.resolve())
        (out/"e01-v2-captions.srt").write_text(export_srt(cues),encoding="utf-8")
        (out/"e01-v2-captions.vtt").write_text(export_vtt(cues),encoding="utf-8")
        (out/"e01-v2-karaoke-qa.ass").write_text(export_ass(cues),encoding="utf-8")
        (out/"e01-v2-caption-timeline.json").write_text(
            json.dumps(cues,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except Exception as e:
        report={
            "status":"BLOCKED_TIMED_CAPTION_GENERATION",
            "error_code":str(e) if isinstance(e,ProductionError) else type(e).__name__,
            "caption_text_is_canonical_script":False,
            "voice_rights_cleared":False,
            "publication_authorized":False,
        }
        for name in ("e01-v2-captions.srt","e01-v2-captions.vtt",
                     "e01-v2-karaoke-qa.ass","e01-v2-caption-timeline.json"):
            (out/name).unlink(missing_ok=True)
    (out/"qa-report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],"cue_count":report.get("cue_count"),
        "alignment":report.get("alignment"),
        "publication_authorized":False,
        "error_code":report.get("error_code"),
    },ensure_ascii=False))
    return 0 if report["status"]=="TIMED_CAPTIONS_PROVISIONAL_NOT_MASTER" else 2


if __name__=="__main__":
    raise SystemExit(main())
