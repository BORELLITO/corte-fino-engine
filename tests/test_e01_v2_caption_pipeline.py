"""Negative QA, two-line captions and release-boundary regression tests."""
import json
import math
import re
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
try:
    from PIL import ImageFont as _PIL
except ImportError:
    _PIL = None
needs_pillow = unittest.skipUnless(
    _PIL is not None, "Pillow is installed in the dedicated caption workflow")
from agents.e01_v2_caption_pipeline import (
    ASR_SHA, ASR_BYTES, SCRIPT_SHA, WAV_SHA, VOICE_DURATION,
    MAX_LINE_PX, MAX_LINES, MARGIN_SIDE, MARGIN_BOTTOM, FONT_PATH, FONT_SHA,
    FONT_ASS_SIZE, COLOR_ACTIVE, COLOR_BASE, typography_violations, text_width, digest_file, norm, canonical_words, asr_words,
    align_once, combine_alignments, cue_lines, make_cues,
    clock, export_srt, export_vtt, export_ass, evaluate,
)

ROOT = Path(__file__).resolve().parents[1]


class E01CaptionQATests(unittest.TestCase):
    def test_pinned_reproducible_source_digests_and_time(self):
        self.assertEqual(len(ASR_SHA), 64)
        self.assertEqual(ASR_BYTES, 72475)
        self.assertEqual(SCRIPT_SHA, "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6")
        self.assertEqual(WAV_SHA, "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e")
        self.assertEqual(VOICE_DURATION, 70.425)

    def test_script_is_exactly_182_canonical_words(self):
        draft = json.loads((ROOT / "contracts/e01_script_v2_candidate.json")
                           .read_text(encoding="utf-8"))["episode"]
        words=canonical_words(draft)
        self.assertEqual(len(words),182)
        self.assertEqual([w["text"] for w in words[:4]],
                         ["Você","já","repetiu","a"])
        self.assertIn("machuca.", [w["text"] for w in words])
        self.assertEqual(words[-1]["text"], "esperança.")

    def test_normalization_respects_accents_and_negation(self):
        self.assertEqual(norm("Às"),"as")
        self.assertEqual(norm("dói."),"doi")
        self.assertEqual(norm("Habacuque,"),"habacuque")
        self.assertNotEqual(norm("não"),norm("sim"))

    def test_nonsemantic_word_aliases_cannot_claim_exact_acoustic_match(self):
        ref=[{"key":"habacuque"},{"key":"um"}]
        asr=[{"key":"abacuque","text":"Abacuque","start":1,"end":2,"confidence":.8},
             {"key":"1","text":"1","start":2,"end":3,"confidence":.9}]
        aligned=align_once(ref,asr)
        self.assertEqual([w["alignment"] for w in aligned],
                         ["PHONETIC_OR_NUMBER_ALIAS","PHONETIC_OR_NUMBER_ALIAS"])

    def test_exact_word_timecodes_are_preferred(self):
        ref=[{"key":"esperar"},{"key":"machuca"}]
        asr=[{"key":"esperar","start":1,"end":1.3,"confidence":.98},
             {"key":"machuca","start":1.3,"end":2.0,"confidence":.99}]
        out=align_once(ref,asr)
        self.assertTrue(all(w["alignment"]=="EXACT" for w in out))

    @needs_pillow
    def test_short_phrase_is_one_line(self):
        group=[{"text":w} for w in ("Às","vezes,","esperar")]
        self.assertEqual(cue_lines(group),["Às vezes, esperar"])

    @needs_pillow
    def test_two_line_balancing_never_exceeds_pixel_limit(self):
        group=[{"text":w} for w in
               ("Os","primeiros","versos","não")]
        lines=cue_lines(group)
        self.assertLessEqual(len(lines),2)
        self.assertTrue(all(text_width(l)<=MAX_LINE_PX for l in lines))
        self.assertEqual(" ".join(lines),
                         "Os primeiros versos não")

    @needs_pillow
    def test_too_many_words_for_two_pixel_lines_is_fail_closed(self):
        group=[{"text":w} for w in
               ("Os","primeiros","versos","não","entregam","uma","explicação.")]
        with self.assertRaisesRegex(ProductionError,"more_than_two_lines"):
            cue_lines(group)

    @needs_pillow
    def test_unbreakable_single_word_is_fail_closed(self):
        with self.assertRaisesRegex(ProductionError,"more_than_two_lines"):
            cue_lines([{"text":"responsabilizacaointernacionalizada"}])

    @needs_pillow
    def test_real_canonical_words_are_split_before_unbreakable_two_line_crossings(self):
        draft=json.loads((ROOT / "contracts/e01_script_v2_candidate.json")
                         .read_text(encoding="utf-8"))["episode"]
        tokens=canonical_words(draft)
        for i,w in enumerate(tokens):
            w["index"]=i
            w["start"]=round(i*0.385,3)
            w["end"]=round(i*0.385+0.30,3)
            w["alignment"]="SIMULATED_TEST_ONLY"
            w["asr_confidence"]=0.9
        cues=make_cues(tokens)
        self.assertGreater(len(cues),20)
        self.assertTrue(all(len(c["lines"])<=2 for c in cues))
        self.assertTrue(all(all(text_width(line)<=MAX_LINE_PX for line in c["lines"])
                            for c in cues))
        self.assertTrue(all(len(c["words"])<=7 for c in cues))
        self.assertEqual(
            " ".join(w["text"] for c in cues for w in c["words"]),
            " ".join(w["text"] for w in tokens))
        self.assertFalse(any(cues[i]["start"] < cues[i-1]["end"]
                             for i in range(1,len(cues))))

    def test_srt_vtt_time_format_is_stable(self):
        self.assertEqual(clock(70.425),"00:01:10,425")
        self.assertEqual(clock(70.425,"."),"00:01:10.425")
        c=[{"index":1,"start":6.06,"end":7.76,
            "lines":["Às vezes, esperar machuca."],
            "words":[{"text":"Às","start":6.06,"end":6.3},
                     {"text":"vezes,","start":6.3,"end":6.62},
                     {"text":"esperar","start":6.74,"end":7.1},
                     {"text":"machuca.","start":7.1,"end":7.76}]}]
        self.assertIn("00:00:06,060 --> 00:00:07,760",export_srt(c))
        self.assertIn("WEBVTT",export_vtt(c))
        self.assertIn(r"{\1c&H00F2B0C4&}",export_ass(c))

    def test_karaoke_breaks_follow_exact_srt_lines(self):
        c=[{"index":1,"start":5.0,"end":6.4,
            "lines":["Nomear o que está errado","e procurar ajuda"],
            "words":[{"text":w,"start":5+.1*i,"end":5+.1*(i+1)}
                     for i,w in enumerate("Nomear o que está errado e procurar ajuda".split())]}]
        art=export_ass(c)
        events=[l for l in art.splitlines() if l.startswith("Dialogue: 0")]
        self.assertTrue(events and all(l.count(r"\N")==1 for l in events))

    @needs_pillow
    def test_font_asset_is_pinned_and_has_license(self):
        self.assertEqual(digest_file(FONT_PATH),FONT_SHA)
        lic=(ROOT/"assets/fonts/OFL-AtkinsonHyperlegibleNext.txt").read_text(encoding="utf-8")
        self.assertIn("SIL Open Font License",lic)

    @needs_pillow
    def test_layout_keeps_text_inside_hud_safe_columns(self):
        # rendered bbox ~= text width + 15 px (outline/spacing, measured)
        # centred bbox = text width + 15; right edge must stay <= 906 (>=36 px HUD gap,
        # derived from the measured >=42 px gap, NOT re-measured on a device)
        self.assertLessEqual(540+(MAX_LINE_PX+15)/2,906)
        self.assertGreaterEqual(MARGIN_SIDE,180)
        self.assertGreaterEqual(MARGIN_BOTTOM,576)
        art=export_ass([{"index":1,"start":1,"end":2,"lines":["a"],
                         "words":[{"text":"a","start":1,"end":2}]}])
        self.assertIn(f"Atkinson Hyperlegible Next,{FONT_ASS_SIZE},{COLOR_BASE},{COLOR_BASE}",art)
        self.assertIn(f",{MARGIN_SIDE},{MARGIN_SIDE},{MARGIN_BOTTOM},1",art)

    def test_only_the_spoken_word_is_highlighted_and_resets_after(self):
        words=[{"text":"Eu","start":10.0,"end":10.2},
               {"text":"clamo,","start":10.3,"end":10.8},
               {"text":"e","start":11.6,"end":11.7},
               {"text":"não","start":11.75,"end":12.0}]
        cue={"index":1,"start":9.9,"end":12.3,"lines":["Eu clamo, e não"],"words":words}
        ev=[]
        for l in export_ass([cue]).splitlines():
            if l.startswith("Dialogue: 0"):
                f=l.split(",",9);ev.append((f[1],f[2],f[9]))
        def active(text):
            return re.findall(r"\{\\1c"+re.escape(COLOR_ACTIVE)+r"&\}([^{]*)",text)
        # every event shows the whole caption; at most ONE word is lilac
        for _,_,t in ev:
            self.assertLessEqual(len(active(t)),1)
            self.assertEqual(re.sub(r"\{[^}]*\}","",t).replace("\\N"," "),"Eu clamo, e não")
        seq=[active(t)[0] if active(t) else None for _,_,t in ev]
        # Eu -> clamo, (bridged gap 0.1) -> nothing (long gap) -> e -> não -> nothing
        self.assertEqual(seq,[None,"Eu","clamo,",None,"e","não",None])
        # a spoken word never stays lilac after its turn
        self.assertEqual(seq.count("Eu"),1)

    def test_events_are_contiguous_without_overlap(self):
        words=[{"text":"a","start":1.0,"end":1.2},{"text":"b","start":1.25,"end":1.5}]
        cue={"index":1,"start":0.9,"end":1.9,"lines":["a b"],"words":words}
        ev=[l.split(",",9) for l in export_ass([cue]).splitlines() if l.startswith("Dialogue: 0")]
        for x,y in zip(ev,ev[1:]):
            self.assertLessEqual(x[2],y[1])

    def test_absent_real_asr_json_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ProductionError,"untrusted_asr_report"):
                evaluate(ROOT,Path(d)/"not-found.json")

    def test_forged_real_report_size_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"report.json";p.write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ProductionError,"untrusted_asr_report"):
                evaluate(ROOT,p)

    def test_forged_real_report_hash_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"report.json";p.write_bytes(b"x"*ASR_BYTES)
            with self.assertRaisesRegex(ProductionError,"untrusted_asr_report"):
                evaluate(ROOT,p)

    def test_caption_schema_locks_two_lines(self):
        schema=json.loads((ROOT/"contracts/caption_contract.schema.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["max_lines"]["enum"],[2])
        self.assertEqual(MAX_LINES,2)


if __name__=="__main__":
    unittest.main()
