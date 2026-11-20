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
MAX_LINE_PX = 715            # text width; rendered bbox is ~15 px wider (x ~175..905 centred; >=36 px from HUD rail, derived from the measured >=42 px gap)
MARGIN_SIDE = 180            # keeps x in 180..900 (right HUD rail clear)
MARGIN_BOTTOM = 576          # bottom HUD clearance, measured on 3 screenshots
COLOR_ACTIVE = "&H00F2B0C4"  # light lilac (provisional brand colour): ONLY the word being spoken
COLOR_BASE = "&H00EEF1F2"    # warm white: every other word, before AND after speech
HIGHLIGHT_BRIDGE_MAX_GAP = 0.20  # keep highlight on across tiny gaps (no flicker)
CUE_LEAD_IN = 0.10           # caption appears this long before the first word
CUE_HOLD = 0.35              # caption stays this long after the last word
CUE_GAP_GUARD = 0.04         # never touch the neighbouring caption
MIN_DISPLAY = 1.0            # reading time target for short captions
# Displayed text = canonical words with only NECESSARY punctuation:
# - periods never shown; "?" and "!" kept (they change meaning);
# - the last word of a caption never ends with , : ; (the caption break is the pause);
# - commas/colons INSIDE a caption are kept (they separate list items/clauses,
#   e.g. "violência, injustiça"). No dashes, ellipses or odd spaces, ever.
# Chunking logic still reads the ORIGINAL tokens.
DISPLAY_STRIP = ".,:;"
INNER_STRIP = "."
FORBIDDEN_DISPLAY_CHARS = "—–-‒―…\u00a0\t"
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
    "não","nem","sua","seu","suas","seus","você","é","ele","ela","eles",
    "elas","me","te","lhe","nos","vos","como","quando","porque","pois",
    "pelo","pela","pelos","pelas","num","numa","entre","sobre","sem","até",
}
# words that must stay glued to the NEXT word (never end a line/caption on them)
NO_END_WORDS = FUNCTION_WORDS | {
    "tão","essa","esse","esta","este","isso","mesma","mesmo",
    "mesmas","mesmos","primeiros","primeiras","primeiro","primeira","toda",
    "todo","todas","todos","cada","outra","outro","tantas","tantos","tanta",
    "tanto","algum","alguma","nenhum","nenhuma","diante","favor","longo",
}
# pairs that must never be split across lines or captions
NO_SPLIT_PAIRS = {("capítulo","um"),("capítulo","dois"),("capítulo","três")}


def text_width(text: str) -> float:
    global _FONT
    if _FONT is None:
        check(ImageFont is not None, "caption:pillow_required_for_pixel_layout")
        check(FONT_PATH.is_file() and digest_file(FONT_PATH) == FONT_SHA,
              "caption:caption_font_missing_or_changed")
        _FONT = ImageFont.truetype(str(FONT_PATH), FONT_EM_PX)
    return _FONT.getlength(text)


def display(token: str, last: bool = False) -> str:
    """Token as shown on screen; `last` = final word of its caption."""
    out = token.strip(DISPLAY_STRIP if last else INNER_STRIP)
    check(out and not any(ch in out for ch in FORBIDDEN_DISPLAY_CHARS),
          "caption:invalid_display_token")
    return out


def _dangling(text: str) -> bool:
    """True if the token is a function word WITHOUT closing punctuation
    ('de', 'a', 'que'); 'um,' in 'capítulo um,' ends a clause and is fine."""
    return (text[-1] not in ",.?!:;"
            and text.lower() in NO_END_WORDS)


def _is_no_split(a: str, b: str) -> bool:
    return (a.lower().strip(",.?!:;"), b.lower().strip(",.?!:;")) in NO_SPLIT_PAIRS


def _split(raw: list[str]) -> tuple[float, list[str]] | None:
    """Best 1- or 2-line layout under MAX_LINE_PX, or None. Lower is better.

    Rules (permanent, see docs/REGRAS_LEGENDA_VNC_V1.md): never end a line on
    an article/preposition/conjunction/pronoun, break after punctuation when
    possible, keep lines balanced, prefer the longer line at the bottom
    (pyramid), never leave a one-word orphan line.
    """
    disp = [display(t, last=(k == len(raw) - 1)) for k, t in enumerate(raw)]
    one = " ".join(disp)
    if len(raw) <= ONE_LINE_MAX_WORDS and text_width(one) <= MAX_LINE_PX:
        return 0.0, [one]
    best = None
    for i in range(1, len(raw)):
        if _is_no_split(raw[i-1], raw[i]):
            continue
        left, right = " ".join(disp[:i]), " ".join(disp[i:])   # i>=1: left keeps inner commas
        wl, wr = text_width(left), text_width(right)
        if max(wl, wr) > MAX_LINE_PX:
            continue
        pen = 0.35 * abs(wl - wr)
        if _dangling(raw[i-1]):
            pen += 1500       # (cost/10 => 150): almost never acceptable
        if raw[i-1][-1] in ",:;":
            pen -= 30
        if wl > wr:
            pen += 25
        if min(wl, wr) < 0.30 * max(wl, wr):
            pen += 35
        if best is None or pen < best[0]:
            best = (pen, [left, right])
    return best


def cue_lines(words: list[dict[str, Any]]) -> list[str]:
    layout = _split([w["text"] for w in words])
    check(layout is not None, "caption:more_than_two_lines")
    return layout[1]


def _segment_cost(group: list[dict[str, Any]]) -> float:
    """Lower is better. Captions should be whole clauses, never fragments."""
    n = len(group)
    last = group[-1]["text"]
    key = last.lower().strip(",.?!:;")
    cost = 3.0 + (n - 5) ** 2
    if last[-1] in ".?!":
        cost -= 10
    elif last[-1] in ",:;":
        cost -= 6
    else:
        cost += 35           # cut in the middle of a clause
    if _dangling(last):
        cost += 300          # never end a caption on a dangling function word
    if any(w["text"][-1] in ",:;" for w in group[:-1]):
        cost += 4
    if n == 1:
        cost += 30           # orphan word
    elif n == 2:
        cost += 12
    layout = _split([w["text"] for w in group])
    if layout is not None:
        cost += max(0.0, layout[0]) / 10
    return cost


def make_cues(words: list[dict[str, Any]],
              duration: float = VOICE_DURATION) -> list[dict[str, Any]]:
    """Cost-based chunking. Typographic rules are very expensive to break but
    never silently dropped: any cue that still breaks one carries
    cue["rule_violations"] so a human reviews it (see typography_violations)."""
    cues = _make_cues(words, duration)
    for c in cues:
        v = typography_violations(c)
        if v:
            c["rule_violations"] = v
    return cues


def typography_violations(cue: dict[str, Any]) -> list[str]:
    out = []
    if _dangling(cue["words"][-1]["text"]):
        out.append("caption_ends_on_function_word")
    toks = [w["text"] for w in cue["words"]]
    if len(cue["lines"]) == 2:
        k = len(cue["lines"][0].split())
        if _dangling(toks[k-1]):
            out.append("line_ends_on_function_word")
        if _is_no_split(toks[k-1], toks[k]):
            out.append("no_split_pair_broken")
    if len(cue["lines"]) == 2 and (min(text_width(x) for x in cue["lines"])
                                   < 0.30 * max(text_width(x) for x in cue["lines"])):
        out.append("unbalanced_lines")
    return out


def _make_cues(words: list[dict[str, Any]],
               duration: float) -> list[dict[str, Any]]:
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
            if i > 0 and _is_no_split(words[i-1]["text"], words[i]["text"]):
                continue
            if any(w["text"][-1] in ".?!" for w in group[:-1]):
                continue          # a caption never spans two sentences
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
    return _finalize_cues(cues, duration)


def _finalize_cues(cues: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
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
    apply_display_times(cues, duration)
    check(cues[0]["start"] <= .5
          and cues[-1]["end"] >= duration - 1.3
          and len(cues) >= 20, "caption:coverage_too_short")
    return cues


def make_cues_from_plan(words: list[dict[str, Any]], plan: list[list[str]],
                        duration: float = VOICE_DURATION) -> list[dict[str, Any]]:
    """Build captions from an editor-reviewed plan (lines of ORIGINAL tokens).

    The plan only decides line breaks and caption boundaries; text and word
    timing always come from `words`. Every cue is still checked against the
    permanent typography rules and carries rule_violations if it breaks one.
    """
    flat = [t for cue in plan for line in cue for t in line.split()]
    check(flat == [w["text"] for w in words], "caption:plan_text_differs_from_script")
    cues, i = [], 0
    for lines in plan:
        check(1 <= len(lines) <= MAX_LINES, "caption:plan_more_than_two_lines")
        n = sum(len(l.split()) for l in lines)
        group = words[i:i+n]
        i += n
        check(len({w["block"] for w in group}) == 1, "caption:plan_cue_spans_blocks")
        check(not any(w["text"][-1] in ".?!" for w in group[:-1]),
              "caption:plan_cue_spans_two_sentences")
        check(group[-1]["end"] - group[0]["start"] <= MAX_CUE_DURATION,
              "caption:plan_cue_too_long")
        shown, k = [], 0
        for li, line in enumerate(lines):
            toks = line.split()
            last_line = li == len(lines) - 1
            shown.append(" ".join(display(t, last=(last_line and j == len(toks) - 1))
                                  for j, t in enumerate(toks)))
            k += len(toks)
        check(all(text_width(x) <= MAX_LINE_PX for x in shown),
              "caption:plan_line_too_wide")
        start = max(0.0, group[0]["start"])
        end = min(duration, group[-1]["end"])
        check(end - start >= MIN_CUE_DURATION, "caption:cue_too_short")
        cues.append({"index": len(cues) + 1, "start": round(start, 3),
                     "end": round(end, 3), "lines": shown, "words": group,
                     "block": group[0]["block"]})
    cues = _finalize_cues(cues, duration)
    for c in cues:
        v = typography_violations(c)
        if v:
            c["rule_violations"] = v
    return cues


def apply_display_times(cues: list[dict[str, Any]], duration: float) -> None:
    """Give captions reading time without touching word timing.

    Appear CUE_LEAD_IN before the first word and linger up to CUE_HOLD after
    the last, always keeping CUE_GAP_GUARD from the neighbouring caption, and
    try to reach MIN_DISPLAY. Word highlight times are unaffected.
    """
    n = len(cues)
    for k, c in enumerate(cues):
        first, last = c["words"][0]["start"], c["words"][-1]["end"]
        prev_end = cues[k-1]["end"] if k else 0.0
        c["start"] = round(max(prev_end + CUE_GAP_GUARD if k else 0.0,
                               min(c["start"], first - CUE_LEAD_IN)), 3)
        limit = (cues[k+1]["words"][0]["start"] - CUE_LEAD_IN - CUE_GAP_GUARD
                 if k + 1 < n else duration)
        want = max(last + CUE_HOLD, c["start"] + MIN_DISPLAY)
        c["end"] = round(max(c["end"], min(want, limit)), 3)
        check(c["end"] > c["start"], "caption:display_time_collapsed")


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


def highlight_spans(words: list[dict[str, Any]]) -> list[tuple[int, float, float]]:
    """(word index, start, end): when each word is highlighted.

    A word is highlighted from its start to its end; across a gap of at most
    HIGHLIGHT_BRIDGE_MAX_GAP to the next word the highlight is held until the
    next word starts, so the colour never flickers off between words.
    """
    spans = []
    for i, w in enumerate(words):
        end = w["end"]
        if i + 1 < len(words):
            nxt = words[i+1]["start"]
            if 0 < nxt - end <= HIGHLIGHT_BRIDGE_MAX_GAP:
                end = nxt
        spans.append((i, w["start"], max(end, w["start"] + 0.04)))
    return spans


def _cue_text(cue: dict[str, Any], active: int | None) -> str:
    out = []
    line_boundary = len(cue["lines"][0].split())
    for idx, w in enumerate(cue["words"]):
        if idx:
            out.append(r"\N" if len(cue["lines"]) == 2 and idx == line_boundary else " ")
        t = display(w["text"], last=(idx == len(cue["words"]) - 1))
        out.append(r"{\1c" + COLOR_ACTIVE + r"&}" + t + r"{\1c" + COLOR_BASE + r"&}"
                   if idx == active else t)
    return "".join(out)


def export_ass(cues: list[dict[str, Any]],
               duration: float = VOICE_DURATION) -> str:
    header = f"""[Script Info]
Title: VERBO NO CHAO | E01 | QA-ONLY KARAOKE (layout v3c, word-by-word highlight)
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{FONT_FAMILY},{FONT_ASS_SIZE},{COLOR_BASE},{COLOR_BASE},&H00141210,&H96000000,-1,0,0,0,100,100,0.6,0,1,7,3,2,{MARGIN_SIDE},{MARGIN_SIDE},{MARGIN_BOTTOM},1
Style: QA,DejaVu Sans,34,&H00E6E6E6,&H00E6E6E6,&H0012100E,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,90,90,118,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    out = [
        "Dialogue: 1,0:00:00.00,"+ass_time(duration)
        +",QA,,0,0,0,,PRÉVIA TÉCNICA - NÃO PUBLICAR"
    ]

    def event(t0: float, t1: float, text: str) -> None:
        if round(t1*100) > round(t0*100):
            out.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Caption,,0,0,0,,{text}")

    for c in cues:
        # One event per state, same style/position/text in every state, so
        # nothing moves. Only the word being spoken is lilac; every other word
        # is the base white before AND after its turn (no accumulated fill).
        spans = highlight_spans(c["words"])
        t = c["start"]
        for i, hs, he in spans:
            hs, he = max(hs, t), min(he, c["end"])
            if hs > t:
                event(t, hs, _cue_text(c, None))
            if he > hs:
                event(hs, he, _cue_text(c, i))
            t = max(t, he)
        if c["end"] > t:
            event(t, c["end"], _cue_text(c, None))
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
