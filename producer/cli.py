"""python -m producer.cli episodes/E02.json --out build/E02 [--footage pexels|local:DIR] [--no-asr]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestrator.runflow import run_flow

from .build import build_package
from .captions import FasterWhisperAligner
from .common import ProducerError
from .footage import ChainFootage, LocalCatalogFootage, PexelsFootage, PixabayFootage
from .rejections import load_rejections
from .voice import ElevenLabsVoice, FallbackVoice, OpenAIVoice


def make_voice(cfg: dict):
    """spec["voice"] = {"provider": "elevenlabs"|"openai", "fallback": "openai"|"none", ...ElevenLabs args}.

    Default: ElevenLabs "Mark" with OpenAI-TTS as fallback when Mark itself is unavailable.
    """
    cfg = dict(cfg)
    provider = cfg.pop("provider", "elevenlabs")
    fallback = cfg.pop("fallback", "openai")
    if provider == "openai":
        return OpenAIVoice(**cfg)
    if provider != "elevenlabs":
        raise ProducerError(f"producer:spec:unknown_voice_provider:{provider}")
    primary = ElevenLabsVoice(**cfg)
    if fallback == "none":
        return primary
    if fallback != "openai":
        raise ProducerError(f"producer:spec:unknown_voice_fallback:{fallback}")
    return FallbackVoice(primary, OpenAIVoice())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Produce a Verbo no Chão preview package and validate it")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report-dir", type=Path, default=Path("run-reports"))
    ap.add_argument("--footage", default="pexels", help="comma-separated chain, tried in order: local:<dir> | pixabay | pexels")
    ap.add_argument("--no-asr", action="store_true", help="skip ASR alignment (captions will NOT be marked synchronized)")
    args = ap.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        sources = [x.strip() for x in args.footage.split(",") if x.strip()]
        if spec.get("approved_sources_only") and not all(x.startswith("local:") for x in sources):
            raise ProducerError("producer:spec:approved_sources_only_requires_local_catalog")
        rejected = load_rejections(Path(__file__).resolve().parent.parent / "contracts")
        footage = ChainFootage([LocalCatalogFootage(Path(x[6:])) if x.startswith("local:")
                                else PixabayFootage() if x == "pixabay" else PexelsFootage()
                                for x in sources])
        aligner = None if args.no_asr else FasterWhisperAligner()
        build_package(spec, args.out, make_voice(spec.get("voice", {})), footage, aligner, rejected)
    except (ProducerError, OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED\n- {exc}")
        return 1
    result = run_flow({"episode": spec["episode_id"]}, args.out, args.report_dir, render=True)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
