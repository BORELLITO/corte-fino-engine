"""Producer tests use TEST DOUBLES for voice/footage/ASR (no network, no models).

The doubles are only ever used here; the real providers fail closed (see last tests).
"""
import json
import math
import shutil
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

from orchestrator.runflow import run_flow
from producer import captions
from producer.build import build_package
from producer.common import ProducerError, audio_integrity_ok, duration_sec, run_ffmpeg, sha256_file
from producer.footage import Clip, PexelsFootage
from producer.rejections import load_rejections
from producer.music import write_music

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
needs_ffmpeg = unittest.skipUnless(HAS_FFMPEG, "FFmpeg required for real media execution")

SPEC = {
    "episode_id": "TEST01",
    "scenes": [
        {"id": "S01", "narration": "Senhor, até quando clamarei sem que tu ouças?", "footage_query": "a"},
        {"id": "S02", "narration": "A visão ainda aguarda o seu tempo determinado.", "footage_query": "b"},
        {"id": "S03", "narration": "O justo viverá pela sua fé, mesmo esperando.", "footage_query": "c"},
    ],
}


class FakeVoice:
    engine, language = "Kokoro-82M", "pt-BR"

    def synthesize(self, text, dst):
        n = int(24000 * (0.4 + 0.08 * len(text.split())))
        pcm = array("h", (int(0.3 * 32767 * math.sin(2 * math.pi * 220 * i / 24000)) for i in range(n)))
        with wave.open(str(dst), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(pcm.tobytes())


class WrongEngineVoice(FakeVoice):
    engine = "some-other-tts"


class FakeFootage:
    def __init__(self): self.n = 0

    def fetch(self, query, min_seconds, exclude, dst_dir):
        self.n += 1
        dst = dst_dir / f"fake{self.n}.mp4"
        run_ffmpeg(["-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30", "-t", str(min_seconds + 1),
                    "-vf", f"hue=h={self.n * 50}", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", str(dst)])
        return Clip(f"fake-{self.n}", dst, f"https://example.test/{self.n}", "https://example.test/l", "TEST")


class RepeatingFootage(FakeFootage):
    def fetch(self, *a, **k):  # ignores `exclude` -> always the same clip
        clip = super().fetch(*a, **k) if self.n == 0 else self.first
        self.first = getattr(self, "first", clip)
        return self.first


class FakeAligner:
    def align(self, wav, words):
        total = duration_sec(wav)
        return captions.proportional_times(words, 0.0, total)


@needs_ffmpeg
class ProducerPipelineTest(unittest.TestCase):
    def build(self, voice=None, footage=None, aligner="fake"):
        tmp = Path(tempfile.mkdtemp())
        pkg = tmp / "pkg"
        build_package(SPEC, pkg, voice or FakeVoice(), footage or FakeFootage(),
                      FakeAligner() if aligner == "fake" else None)
        return pkg, run_flow({"t": 1}, pkg, tmp / "reports", render=True)

    def test_end_to_end_reaches_preview_ready_never_publishable(self):
        pkg, result = self.build()
        self.assertEqual(result.errors, ())
        self.assertEqual((result.status, result.state), ("PASS", "PREVIEW_READY"))
        manifest = json.loads(Path(result.manifest_path).read_text())
        self.assertIs(manifest["publication_authorized"], False)
        self.assertEqual(manifest["rights"]["voice_review"], "PENDING")
        self.assertTrue((pkg / "output.mp4").is_file())

    def test_without_asr_alignment_captions_block(self):
        _, result = self.build(aligner=None)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("caption synchronization gate failed", result.errors)

    def test_repeated_clip_is_blocked(self):
        _, result = self.build(footage=RepeatingFootage())
        self.assertEqual(result.status, "BLOCKED")
        self.assertTrue(any("repetition" in e for e in result.errors))

    def test_non_kokoro_voice_is_blocked(self):
        _, result = self.build(voice=WrongEngineVoice())
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("audio engine must remain Kokoro-82M", result.errors)

    def test_refuses_to_overwrite_existing_package(self):
        pkg, _ = self.build()
        with self.assertRaises(ProducerError):
            build_package(SPEC, pkg, FakeVoice(), FakeFootage(), FakeAligner())

    def test_invalid_spec_is_rejected(self):
        bad = {"episode_id": "x", "scenes": [{"id": "S1", "narration": "", "footage_query": "q"}]}
        with self.assertRaises(ProducerError):
            build_package(bad, Path(tempfile.mkdtemp()) / "p", FakeVoice(), FakeFootage())


class ProducerUnitTest(unittest.TestCase):
    def test_real_repo_rejections_are_loaded(self):
        found = load_rejections(Path(__file__).resolve().parent.parent / "contracts")
        self.assertIn("pexels-7977614", found)  # S04 rejection contract
        self.assertIn("f596f2a768d943061f5bc76cd37484840ab0bed72d852f02d5379e601daab6ee", found)  # S10

    @needs_ffmpeg
    def test_rejected_sources_are_preseeded_into_exclusion_set(self):
        seen = []

        class Recorder(FakeFootage):
            def fetch(self, query, min_seconds, exclude, dst_dir):
                seen.append(set(exclude))
                return super().fetch(query, min_seconds, exclude, dst_dir)

        build_package(SPEC, Path(tempfile.mkdtemp()) / "p", FakeVoice(), Recorder(), None,
                      rejected={"pexels-7977614"})
        self.assertTrue(all("pexels-7977614" in e for e in seen) and len(seen) == 3)

    @needs_ffmpeg
    def test_music_is_deterministic_original_and_not_clipped(self):
        d = Path(tempfile.mkdtemp())
        write_music(d / "a.wav", 6.0, seed=3)
        write_music(d / "b.wav", 6.0, seed=3)
        self.assertEqual(sha256_file(d / "a.wav"), sha256_file(d / "b.wav"))
        self.assertTrue(audio_integrity_ok(d / "a.wav"))

    def test_pexels_without_key_fails_closed(self):
        import os
        old = os.environ.pop("PEXELS_API_KEY", None)
        try:
            with self.assertRaises(ProducerError):
                PexelsFootage()
        finally:
            if old: os.environ["PEXELS_API_KEY"] = old

    def test_cue_verification_catches_overlap_and_window_escape(self):
        scenes = [("a b", 0.0, 2.0)]
        bad = [captions.Cue(0.0, 1.5, ("a",)), captions.Cue(1.0, 2.0, ("b",))]
        self.assertIn("cue:1:overlap", captions.verify_cues(bad, scenes))
        late = [captions.Cue(0.0, 5.0, ("a b",))]
        self.assertIn("cue:outside_audio_window", captions.verify_cues(late, scenes))

    def test_wrap_respects_two_lines(self):
        words = ("Senhor até quando clamarei sem que tu ouças e não me salvarás").split()
        for chunk in captions.chunk_words(words):
            self.assertLessEqual(len(captions.wrap([words[i] for i in chunk])), 2)


if __name__ == "__main__":
    unittest.main()
