"""Voice stage: one WAV per scene, so scene timing is measured, never guessed.

Providers: ElevenLabs (primary, owner-approved voice "Mark") and OpenAI-TTS (fallback only).
Kokoro was removed on 2026-11-20 (owner: too robotic).
"""
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
        _write_pcm_as_wav(self._request(text), dst_wav)


class OpenAIVoice:
    """Fallback narrator (gpt-4o-mini-tts, REST, stdlib). Key from OPENAI_API_KEY, never logged.

    Chosen to approximate "Mark": calm, warm, steady Brazilian male narrator. NOT yet approved by ear:
    the owner must listen before the first publication that relies on it.
    """

    engine = "OpenAI-TTS"
    language = "pt-BR"
    URL = "https://api.openai.com/v1/audio/speech"
    INSTRUCTIONS = ("Narre em português do Brasil, com voz masculina grave, calma, firme e acolhedora, "
                    "ritmo lento e natural, com pausas e respiração entre as frases. "
                    "Tom de paz e confiança, sem sensualidade, sem dramatização exagerada.")

    def __init__(self, voice: str = "ash", model: str = "gpt-4o-mini-tts",
                 api_key_env: str = "OPENAI_API_KEY", timeout: int = 120) -> None:
        self.voice, self.model, self.timeout, self._key_env = voice, model, timeout, api_key_env

    def synthesize(self, text: str, dst_wav: Path) -> None:
        key = os.environ.get(self._key_env, "")
        if not key:
            raise ProducerError("producer:voice:openai_key_missing")
        body = json.dumps({"model": self.model, "voice": self.voice, "input": strip_audio_tags(text),
                           "instructions": self.INSTRUCTIONS, "response_format": "pcm"}).encode("utf-8")
        req = urllib.request.Request(self.URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (fixed https host)
                pcm = resp.read()
        except urllib.error.HTTPError as exc:
            raise ProducerError(f"producer:voice:openai_http_{exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProducerError(f"producer:voice:openai_network:{type(exc).__name__}") from exc
        _write_pcm_as_wav(pcm, dst_wav)


class FallbackVoice:
    """Primary voice; falls back ONLY when the voice/service itself is unavailable (404, 5xx, network).

    Auth, billing and quota errors (401/402/403/429) never fall back: they block for the owner.
    `engine` always reports the provider that actually produced the audio, and mixing providers inside
    one episode is refused, so a single video never changes narrator halfway.
    """

    language = "pt-BR"
    UNAVAILABLE = ("_http_404", "_http_5", "_network:")

    def __init__(self, primary, fallback) -> None:
        self.primary, self.fallback = primary, fallback
        self.engine = primary.engine
        self._active = None

    def synthesize(self, text: str, dst_wav: Path) -> None:
        if self._active is None:
            try:
                self.primary.synthesize(text, dst_wav)
                self._active = self.primary
            except ProducerError as exc:
                if not any(tag in str(exc) for tag in self.UNAVAILABLE):
                    raise
                self.fallback.synthesize(text, dst_wav)
                self._active = self.fallback
            self.engine = self._active.engine
            return
        self._active.synthesize(text, dst_wav)


def _write_pcm_as_wav(pcm: bytes, dst_wav: Path) -> None:
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
