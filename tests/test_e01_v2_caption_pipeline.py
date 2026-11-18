"""Negative QA, two-line captions and release-boundary regression tests."""
import json
import math
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_v2_caption_pipeline import (
    ASR_SHA, ASR_BYTES, SCRIPT_SHA, WAV_SHA, VOICE_DURATION,
    MAX_LINE, MAX_LINES, norm, canonical_words, asr_words,
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

    def test_short_phrase_is_one_line(self):
        group=[{"text":w} for w in ("Às","vezes,","esperar","machuca.")]
        self.assertEqual(cue_lines(group),["Às vezes, esperar machuca."])

    def test_two_line_balancing_never_exceeds_28_chars(self):
        group=[{"text":w} for w in
               ("Os","primeiros","versos","não","entregam","uma","explicação.")]
        lines=cue_lines(group)
        self.assertLessEqual(len(lines),2)
        self.assertTrue(all(len(l)<=MAX_LINE for l in lines))
        self.assertEqual(" ".join(lines),
                         "Os primeiros versos não entregam uma explicação.")

    def test_unbreakable_single_word_is_fail_closed(self):
        with self.assertRaisesRegex(ProductionError,"more_than_two_lines"):
            cue_lines([{"text":"responsabilizacaointernacionalizada"}])

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
        self.assertTrue(all(all(len(line)<=28 for line in c["lines"]) for c in cues))
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
        self.assertIn(r"{\k",export_ass(c))

    def test_karaoke_breaks_follow_exact_srt_lines(self):
        c=[{"index":1,"start":5.0,"end":6.4,
            "lines":["Nomear o que está errado","e procurar ajuda"],
            "words":[{"text":w,"start":5+.1*i,"end":5+.1*(i+1)}
                     for i,w in enumerate("Nomear o que está errado e procurar ajuda".split())]}]
        art=export_ass(c)
        self.assertEqual(art.count(r"\N"),1)

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
