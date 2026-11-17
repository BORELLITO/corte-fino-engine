"""Offline safety and decoded-WAV tests; live browser is a separate CI job."""
from __future__ import annotations

import copy
import io
import json
import math
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_voice_preview import (
    TARGET_ID, MAX_WAV_BYTES, MAX_TEXT_CHARS, MIN_DURATION, MAX_DURATION,
    VOICE_BIN_BYTES, ONNX_VOICE_SHA,
    approved_source, inspect_pcm_wav, analyze_browser_cache,
)

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "agents/first_batch_seed.json",
    "contracts/autonomous_editorial_policy_v1.json",
    "contracts/e01_ai_editorial_review_v1.json",
    "contracts/kokoro_voice_research_v1.json",
)


def fake_wav(seconds: int = 30, amplitude: int = 1600, *,
             rate: int = 24000, channels: int = 1,
             width: int = 2) -> bytes:
    data = struct.pack("<h", amplitude) * seconds * rate * channels
    out = io.BytesIO()
    with wave.open(out, "wb") as f:
        f.setframerate(rate)
        f.setnchannels(channels)
        f.setsampwidth(width)
        f.writeframes(data)
    return out.getvalue()


def copy_sources(out: Path):
    for rel in FILES:
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)


class E01VoicePreviewTests(unittest.TestCase):
    def test_script_exact_approved_context_source_is_rendered(self):
        text, receipt = approved_source(ROOT)
        self.assertTrue(0 < len(text) <= MAX_TEXT_CHARS)
        self.assertEqual(receipt["episode_id"], TARGET_ID)
        self.assertEqual(receipt["script_sha256"],
                         "67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990")
        self.assertIn("Em Habacuque, capítulo um", text)
        self.assertIn("O diálogo continua ao longo do livro", text)
        self.assertFalse(receipt["voice_audio_generation_authorized"])
        self.assertFalse(receipt["publication_authorized"])

    def test_script_change_revokes_voice_preview_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            copy_sources(root)
            path = root / "agents/first_batch_seed.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            obj["episodes"][0]["blocks"][1]["text"] += " Deus garantiu milagre amanhã."
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
                approved_source(root)

    def test_license_forgery_revokes_preview_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            copy_sources(root)
            path = root / "contracts/kokoro_voice_research_v1.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            obj["model_license"] = "NO_REUSE_ALLOWED"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "license_evidence_wrong"):
                approved_source(root)

    def test_wav_reader_measures_physical_pcm_bytes(self):
        raw = fake_wav(30, 1600)
        metrics = inspect_pcm_wav(raw)
        self.assertEqual(metrics["sample_rate_hz"], 24000)
        self.assertEqual(metrics["duration_seconds"], 30.0)
        self.assertEqual(metrics["channels"], 1)
        self.assertEqual(metrics["frames"], 720000)
        self.assertEqual(metrics["pcm_peak"], 1600)
        self.assertEqual(metrics["bytes"], len(raw))
        self.assertEqual(len(metrics["sha256"]), 64)
        self.assertFalse(metrics["rights_cleared"])
        self.assertFalse(metrics["master_approved"])
        self.assertEqual(metrics["listening_qa"], "NOT_PERFORMED")

    def test_short_wav_cannot_be_mistaken_for_full_preview(self):
        with self.assertRaisesRegex(ProductionError, "wrong_or_oversized_audio|duration_out_of_range"):
            inspect_pcm_wav(fake_wav(5, 1600))

    def test_silent_wav_is_blocked(self):
        with self.assertRaisesRegex(ProductionError, "silent_or_near_silent"):
            inspect_pcm_wav(fake_wav(30, 0))

    def test_near_silent_wav_is_blocked(self):
        with self.assertRaisesRegex(ProductionError, "silent_or_near_silent"):
            inspect_pcm_wav(fake_wav(30, 20))

    def test_non_wav_content_rejected(self):
        with self.assertRaisesRegex(ProductionError, "wrong_or_oversized_audio"):
            inspect_pcm_wav(b"not a wav" * 30000)

    def test_oversized_wav_rejected_early(self):
        with self.assertRaisesRegex(ProductionError, "wrong_or_oversized_audio"):
            inspect_pcm_wav(b"RIFF" + b"\x00" * (MAX_WAV_BYTES + 1))

    def test_unsupported_sample_rate_rejected(self):
        with self.assertRaisesRegex(ProductionError, "unsupported_pcm"):
            inspect_pcm_wav(fake_wav(30, 1700, rate=32000))

    def test_fake_cache_sha_rejected(self):
        class FakePage:
            def evaluate(self, _code):
                return [{"sha256": "0" * 64, "bytes": VOICE_BIN_BYTES}]
        with self.assertRaisesRegex(ProductionError, "known_voice_not_present"):
            analyze_browser_cache(FakePage())

    def test_exact_cache_sha_observed_not_effective_consumption(self):
        class FakePage:
            def evaluate(self, _code):
                return [{"sha256": ONNX_VOICE_SHA, "bytes": VOICE_BIN_BYTES}]
        result = analyze_browser_cache(FakePage())
        self.assertTrue(result["observed_in_same_browser_session"])
        self.assertFalse(result["effective_inference_consumption_proven"])
        self.assertEqual(result["voice_cache_bytes"], VOICE_BIN_BYTES)

    def test_audio_length_policy_is_bounded(self):
        self.assertEqual(MIN_DURATION, 25.0)
        self.assertEqual(MAX_DURATION, 150.0)
        self.assertLess(MAX_WAV_BYTES, 20_000_000)


if __name__ == "__main__":
    unittest.main()
