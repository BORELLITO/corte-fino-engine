"""Voice stage: one WAV per scene, so scene timing is measured, never guessed."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Protocol

from .common import ProducerError, normalize_wav


class VoiceProvider(Protocol):
    engine: str  # must be in engine.quality_gates ALLOWED_VOICE_ENGINES
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


TAG_RE = re.compile(r"\[[^\]]{1,40}\]")


def strip_audio_tags(text: str) -> str:
    """Audio-direction tags like [short pause] are performed, never shown in captions."""
    return re.sub(r"\s{2,}", " ", TAG_RE.sub("", text)).strip()


class ElevenLabsVoice:
    """ElevenLabs hosted TTS (REST, stdlib only). Key comes from ELEVENLABS_API_KEY, never logged.

    Commercial use needs a paid plan (Starter+). Default voice: "Mark" (owner-approved by ear).
    """

    engine = "ElevenLabs"
    language = "pt-BR"
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000"

    def __init__(self, voice_id: str = "AER0pA6w0SVtfnFMyfXG", model_id: str = "eleven_v4",
                 api_key_env: str = "ELEVENLABS_API_KEY", timeout: int = 120) -> None:
        self.voice_id, self.model_id, self.timeout = voice_id, model_id, timeout
        self._key_env = api_key_env

    def _request(self, text: str) -> bytes:
        key = os.environ.get(self._key_env, "")
        if not key:
            raise ProducerError("producer:voice:elevenlabs_key_missing")
        body = json.dumps({"text": text, "model_id": self.model_id}).encode("utf-8")
        req = urllib.request.Request(
            self.URL.format(voice_id=self.voice_id), data=body, method="POST",
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/pcm"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (fixed https host)
                return resp.read()
        except urllib.error.HTTPError as exc:
            raise ProducerError(f"producer:voice:elevenlabs_http_{exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProducerError(f"producer:voice:elevenlabs_network:{type(exc).__name__}") from exc

    def synthesize(self, text: str, dst_wav: Path) -> None:
        pcm = self._request(text)
        if len(pcm) < 24000 * 2 * 0.5:  # < 0.5 s of 24 kHz PCM16 is not a narration
            raise ProducerError("producer:voice:empty_output")
        raw = dst_wav.with_suffix(".raw.wav")
        with wave.open(str(raw), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        normalize_wav(raw, dst_wav)
        raw.unlink()
