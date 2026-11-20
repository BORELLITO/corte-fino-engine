"""Voice stage: one WAV per scene, so scene timing is measured, never guessed."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from .common import ProducerError, normalize_wav


class VoiceProvider(Protocol):
    engine: str  # must equal "Kokoro-82M" to satisfy engine.quality_gates
    language: str

    def synthesize(self, text: str, dst_wav: Path) -> None: ...


class KokoroVoice:
    """Kokoro-82M running locally on the CI runner (CPU). No browser, no hosted site.

    Requires `pip install kokoro soundfile` and the model weights being reachable.
    Any failure raises ProducerError, which keeps the run BLOCKED.
    """

    engine = "Kokoro-82M"
    language = "pt-BR"

    def __init__(self, voice: str = "pf_dora", speed: float = 1.0) -> None:
        self.voice, self.speed = voice, speed
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            try:
                from kokoro import KPipeline  # type: ignore
            except ImportError as exc:
                raise ProducerError("producer:voice:kokoro_not_installed") from exc
            self._pipeline = KPipeline(lang_code="p")
        return self._pipeline

    def synthesize(self, text: str, dst_wav: Path) -> None:
        import numpy as np
        import soundfile as sf  # type: ignore

        try:
            # espeak-based pt-BR G2P truncates long text unless sentences are split by "\n".
            prepared = re.sub(r"(?<=[.!?;:])\s+", "\n", text.strip())
            chunks = [audio for _, _, audio in
                      self._load()(prepared, voice=self.voice, speed=self.speed)]
        except Exception as exc:  # model download / inference failure
            raise ProducerError(f"producer:voice:kokoro_failed:{type(exc).__name__}") from exc
        if not chunks:
            raise ProducerError("producer:voice:empty_output")
        raw = dst_wav.with_suffix(".raw.wav")
        sf.write(str(raw), np.concatenate([np.asarray(c) for c in chunks]), 24000)
        normalize_wav(raw, dst_wav)
        raw.unlink()
