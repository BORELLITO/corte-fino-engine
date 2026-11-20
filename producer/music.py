"""Original procedural score: pure synthesis, zero external samples."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

RATE = 24000
# Slow Am - F - C - G pad (frequencies in Hz); calm, instrumental, no lyrics.
CHORDS = (
    (110.00, 164.81, 220.00, 261.63),
    (87.31, 130.81, 174.61, 220.00),
    (130.81, 196.00, 261.63, 329.63),
    (98.00, 146.83, 196.00, 246.94),
)


def synthesize(duration: float, seed: int = 1) -> np.ndarray:
    n = int(duration * RATE)
    t = np.arange(n) / RATE
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    chord_len = 8.0
    for index, start in enumerate(np.arange(0, duration, chord_len)):
        chord = CHORDS[index % len(CHORDS)]
        a, b = int(start * RATE), min(n, int((start + chord_len) * RATE))
        seg_t = t[a:b] - t[a]
        fade = np.minimum(1.0, np.minimum(seg_t / 1.5, (chord_len - seg_t) / 1.5))
        for freq in chord:
            detune = freq * (1 + rng.uniform(-0.002, 0.002))
            out[a:b] += fade * (np.sin(2 * np.pi * detune * seg_t)
                                + 0.3 * np.sin(2 * np.pi * 2 * detune * seg_t))
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.1 * t)
    out *= lfo
    peak = float(np.max(np.abs(out))) or 1.0
    edge = min(n, int(2 * RATE))
    out[:edge] *= np.linspace(0, 1, edge)
    out[-edge:] *= np.linspace(1, 0, edge)
    return 0.5 * out / peak


def write_music(path: Path, duration: float, seed: int = 1) -> None:
    pcm = (synthesize(duration, seed) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(pcm.tobytes())
