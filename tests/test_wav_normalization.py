import io
import math
import struct
import unittest
import wave

from agents.content_production import ProductionError
from agents.wav_normalization import normalize_riff_wav, FLOAT_GUID


def chunk(kind: bytes, payload: bytes):
    return kind + struct.pack("<I", len(payload)) + payload + (b"\x00" if len(payload) % 2 else b"")


def test_riff(fmt_code: int = 3, seconds: int = 30,
              sample: float = 0.15, extensible: bool = False):
    sr = 24000
    bits = 32 if fmt_code == 3 else 16
    width = bits // 8
    encoding = 65534 if extensible else fmt_code
    fmt = struct.pack("<HHIIHH", encoding, 1, sr, sr * width, width, bits)
    if extensible:
        subtype = FLOAT_GUID if fmt_code == 3 else bytes.fromhex(
            "0100000000001000800000aa00389b71"
        )
        fmt += struct.pack("<HHI", 22, bits, 0) + subtype
    samples = (struct.pack("<f", sample) if fmt_code == 3 else
               struct.pack("<h", 1400)) * (sr * seconds)
    payload = b"WAVE" + chunk(b"fmt ", fmt) + chunk(b"data", samples)
    return b"RIFF" + struct.pack("<I", len(payload)) + payload


class WAVNormalizationTests(unittest.TestCase):
    def test_ieee_float_32_is_normalized_to_pcm16(self):
        original = test_riff(3, sample=0.17)
        normalized, report = normalize_riff_wav(original)
        self.assertEqual(report["source_codec"], "IEEE_FLOAT32")
        self.assertEqual(report["source_format_tag"], 3)
        self.assertFalse(report["audio_samples_preserved"])
        self.assertFalse(report["voice_license_cleared"])
        self.assertEqual(report["duration_seconds"], 30.0)
        with wave.open(io.BytesIO(normalized), "rb") as f:
            self.assertEqual(f.getsampwidth(), 2)
            self.assertEqual(f.getframerate(), 24000)
            self.assertEqual(f.getnchannels(), 1)
            first = struct.unpack("<h", f.readframes(1))[0]
            self.assertAlmostEqual(first, 5570, delta=2)

    def test_pcm16_source_decodes_and_preserves_frames(self):
        original = test_riff(1)
        normalized, report = normalize_riff_wav(original)
        self.assertTrue(report["audio_samples_preserved"])
        with wave.open(io.BytesIO(normalized), "rb") as f:
            self.assertEqual(struct.unpack("<h", f.readframes(1))[0], 1400)

    def test_wave_format_extensible_float_supported(self):
        original = test_riff(3, sample=0.14, extensible=True)
        normalized, report = normalize_riff_wav(original)
        self.assertEqual(report["source_format_tag"], 65534)
        self.assertEqual(report["source_codec"], "IEEE_FLOAT32")
        with wave.open(io.BytesIO(normalized), "rb") as f:
            self.assertEqual(f.getnframes(), 720000)

    def test_wave_format_extensible_pcm_supported(self):
        original = test_riff(1, extensible=True)
        normalized, report = normalize_riff_wav(original)
        self.assertEqual(report["source_format_tag"], 65534)
        with wave.open(io.BytesIO(normalized), "rb") as f:
            self.assertEqual(f.getnframes(), 720000)

    def test_nonfinite_float_never_passes(self):
        with self.assertRaisesRegex(ProductionError, "nan_or_extreme_sample"):
            normalize_riff_wav(test_riff(3, sample=math.nan))

    def test_extreme_float_never_passes(self):
        with self.assertRaisesRegex(ProductionError, "nan_or_extreme_sample"):
            normalize_riff_wav(test_riff(3, sample=9.0))

    def test_short_audio_is_rejected(self):
        with self.assertRaisesRegex(ProductionError, "duration_out_of_range"):
            normalize_riff_wav(test_riff(3, seconds=4))

    def test_riff_size_beyond_blob_rejected(self):
        original = test_riff(3)
        tampered = original[:4] + struct.pack("<I", len(original) + 100) + original[8:]
        with self.assertRaisesRegex(ProductionError, "bad_riff_size"):
            normalize_riff_wav(tampered)

    def test_unsupported_wave_tag_rejected(self):
        original = test_riff(3)
        tampered = bytearray(original)
        struct.pack_into("<H", tampered, 20, 6)
        with self.assertRaisesRegex(ProductionError, "unsupported_encoding_or_depth"):
            normalize_riff_wav(bytes(tampered))

    def test_data_chunk_truncation_rejected(self):
        original = test_riff(3)
        with self.assertRaisesRegex(ProductionError, "bad_riff_size"):
            normalize_riff_wav(original[:-8])

    def test_source_data_cannot_automatically_clear_publication(self):
        _, proof = normalize_riff_wav(test_riff(1))
        self.assertNotIn("publication_authorized", proof)
        self.assertFalse(proof["subjective_listening_qa_completed"])


if __name__ == "__main__":
    unittest.main()
