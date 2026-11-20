"""Original procedural score: pure synthesis, zero external samples."""
from __future__ import annotations

import math
import random
import wave
from array import array
from pathlib import Path

RATE = 24000
# Slow Am - F - C - G pad (frequencies in Hz); calm, instrumental, no lyrics.
CHORDS = (
    (110.00, 164.81, 220.00, 261.63),
    (87.31, 130.81, 174.61, 220.00),
    (130.81, 196.00, 261.63, 329.63),
    (98.00, 146.83, 196.00, 246.94),
)


def synthesize(duration: float, seed: int = 1) -> list[float]:
    """Pure-stdlib synthesis (the gates job installs no third-party packages)."""
    n = int(duration * RATE)
    rng = random.Random(seed)
    out = [0.0] * n
    chord_len = 8.0
    chord_samples = int(chord_len * RATE)
    for index in range(0, n, chord_samples):
        chord = CHORDS[(index // chord_samples) % len(CHORDS)]
        end = min(n, index + chord_samples)
        freqs = [f * (1 + rng.uniform(-0.002, 0.002)) for f in chord]
        for i in range(index, end):
            local = (i - index) / RATE
            fade = min(1.0, local / 1.5, (chord_len - local) / 1.5)
            if fade <= 0:
                continue
            out[i] = fade * sum(math.sin(2 * math.pi * f * local)
                                + 0.3 * math.sin(4 * math.pi * f * local) for f in freqs)
    edge = min(n, int(2 * RATE))
    peak = max(abs(x) for x in out) or 1.0
    for i in range(n):
        lfo = 0.85 + 0.15 * math.sin(2 * math.pi * 0.1 * i / RATE)
        gain = 0.5 * lfo / peak
        if i < edge:
            gain *= i / edge
        if i >= n - edge:
            gain *= (n - 1 - i) / edge
        out[i] *= gain
    return out


def write_music(path: Path, duration: float, seed: int = 1) -> None:
    pcm = array("h", (int(max(-1.0, min(1.0, x)) * 32767) for x in synthesize(duration, seed)))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(pcm.tobytes())
