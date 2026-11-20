import unittest
from agents.e01_v3_voice_audio_probe import parse_duration, parse_silences, parse_loudness


class ProbeParserTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(parse_duration("  Duration: 00:01:16.80, start: 0.0"), 76.8)

    def test_silences(self):
        s = ("[silencedetect @ x] silence_start: 5.8\n"
             "[silencedetect @ x] silence_end: 6.39 | silence_duration: 0.59\n"
             "[silencedetect @ x] silence_start: 8.9\n")
        self.assertEqual(parse_silences(s),
                         [{"start": 5.8, "end": 6.39}, {"start": 8.9, "end": None}])

    def test_loudness(self):
        s = "Summary:\n  Integrated loudness:\n    I:         -19.2 LUFS\n  Loudness range:\n    LRA:         6.1 LU\n  True peak:\n    Peak:       -1.4 dBFS\n"
        r = parse_loudness(s)
        self.assertEqual((r["integrated_lufs"], r["loudness_range_lu"], r["true_peak_dbfs"]),
                         (-19.2, 6.1, -1.4))


if __name__ == "__main__":
    unittest.main()
