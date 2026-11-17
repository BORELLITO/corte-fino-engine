"""Bounded RIFF/WAVE decoder and format normalization for browser TTS.

Accept only mono/stereo PCM16 or IEEE float32, including standard WAVE
FORMAT_EXTENSIBLE wrappers. Never execute embedded data, decompress codecs,
accept malformed offsets, or silently invent waveform samples.
"""
from __future__ import annotations

import hashlib
import io
import math
import struct
import wave
from typing import Any

from agents.content_production import ProductionError, check

PCM_GUID = bytes.fromhex("0100000000001000800000aa00389b71")
FLOAT_GUID = bytes.fromhex("0300000000001000800000aa00389b71")
MAX_INPUT = 18_000_000
ALLOWED_RATES = frozenset((22050, 24000, 44100, 48000))


def normalize_riff_wav(raw: bytes) -> tuple[bytes, dict[str, Any]]:
    check(isinstance(raw, bytes) and 250000 <= len(raw) <= MAX_INPUT
          and raw[:4] == b"RIFF" and raw[8:12] == b"WAVE",
          "wav_normalizer:not_bounded_riff_wave")
    declared_size = struct.unpack_from("<I", raw, 4)[0] + 8
    check(44 <= declared_size <= len(raw), "wav_normalizer:bad_riff_size")
    pos = 12
    fmt: bytes | None = None
    audio: bytes | None = None
    while pos + 8 <= declared_size:
        tag, length = struct.unpack_from("<4sI", raw, pos)
        pos += 8
        end = pos + length
        check(end <= declared_size, "wav_normalizer:chunk_escape")
        if tag == b"fmt ":
            check(fmt is None and 16 <= length <= 128,
                  "wav_normalizer:invalid_or_duplicate_fmt")
            fmt = raw[pos:end]
        elif tag == b"data":
            check(audio is None and 0 < length <= MAX_INPUT,
                  "wav_normalizer:invalid_or_duplicate_data")
            audio = raw[pos:end]
        pos = end + (length % 2)
        check(pos <= declared_size + 1, "wav_normalizer:invalid_padding")
    check(fmt is not None and audio is not None,
          "wav_normalizer:missing_format_or_data")
    check(pos >= declared_size - 1, "wav_normalizer:truncated_riff_chunks")
    encoding, channels, rate, byte_rate, block_align, bits = struct.unpack_from(
        "<HHIIHH", fmt, 0
    )
    original_encoding = encoding
    if encoding == 65534:
        check(len(fmt) >= 40 and struct.unpack_from("<H", fmt, 16)[0] >= 22,
              "wav_normalizer:invalid_extensible_header")
        guid = fmt[24:40]
        check(guid in (PCM_GUID, FLOAT_GUID),
              "wav_normalizer:unsupported_extensible_subtype")
        encoding = 1 if guid == PCM_GUID else 3
        valid_bits = struct.unpack_from("<H", fmt, 18)[0]
        check(valid_bits in (0, bits), "wav_normalizer:misleading_valid_bits")
    check(channels in (1, 2) and rate in ALLOWED_RATES,
          "wav_normalizer:channels_or_rate_unsupported")
    check((encoding == 1 and bits == 16) or
          (encoding == 3 and bits == 32),
          "wav_normalizer:unsupported_encoding_or_depth")
    width = bits // 8
    check(block_align == channels * width
          and byte_rate == rate * block_align
          and len(audio) % block_align == 0,
          "wav_normalizer:bad_sample_alignment")
    frames = len(audio) // block_align
    duration = frames / rate
    check(25.0 <= duration <= 150.0,
          "wav_normalizer:duration_out_of_range")
    if encoding == 1:
        pcm = audio
        name = "PCM16"
    else:
        name = "IEEE_FLOAT32"
        payload = bytearray((len(audio) // 4) * 2)
        for i, (value,) in enumerate(struct.iter_unpack("<f", audio)):
            check(math.isfinite(value) and abs(value) <= 1.2,
                  "wav_normalizer:nan_or_extreme_sample")
            sample = round(max(-1.0, min(1.0, value)) * 32767)
            struct.pack_into("<h", payload, 2 * i, sample)
        pcm = bytes(payload)
    dest = io.BytesIO()
    with wave.open(dest, "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm)
    converted = dest.getvalue()
    return converted, {
        "source_codec": name,
        "source_format_tag": original_encoding,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_bytes": len(raw),
        "normalized_codec": "PCM16",
        "normalized": True,
        "sample_rate_hz": rate,
        "channels": channels,
        "frames": frames,
        "duration_seconds": round(duration, 3),
        "audio_samples_preserved": encoding == 1,
        "voice_license_cleared": False,
        "subjective_listening_qa_completed": False,
    }
